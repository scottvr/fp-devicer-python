# Commit: eer was not EER; it was abs(far, frr), so I've renamed it and added an actual eer calculation in its place.
**Hash:** `15c8f64e23e87d644d276354fbd9846a248b8f4e`  
**Date:** 2026-03-19  

## Editorial Rationale

>  I gave you an actual EER function, and renamed what you had been calling EER to far_ffr_gap or somesuch. search for `true_eer` in the diff below to see.

---

## Technical Diffs
```diff
commit 15c8f64e23e87d644d276354fbd9846a248b8f4e
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 10:06:03 2026 -0500

    eer was not EER; it was abs(far, frr), so I've renamed it and added an actual eer calculation in its place.

diff --git a/src/devicer/benchmarks/__init__.py b/src/devicer/benchmarks/__init__.py
index 62f6472..c501bb1 100644
--- a/src/devicer/benchmarks/__init__.py
+++ b/src/devicer/benchmarks/__init__.py
@@ -11,7 +11,7 @@ from .data_generator import (
 	generate_webgl_blob,
 	mutate,
 )
-from .metrics import BenchmarkResult, calculate_metrics
+from .metrics import BenchmarkResult, EqualErrorRateResult, calculate_metrics, calculate_true_eer
 
 if TYPE_CHECKING:
 	from .accuracy_bench import run_accuracy_benchmark
@@ -19,9 +19,11 @@ if TYPE_CHECKING:
 
 __all__ = [
 	"BenchmarkResult",
+	"EqualErrorRateResult",
 	"create_attractor_fingerprint",
 	"create_base_fingerprint",
 	"calculate_metrics",
+	"calculate_true_eer",
 	"generate_audio_blob",
 	"generate_canvas_blob",
 	"generate_dataset",
diff --git a/src/devicer/benchmarks/accuracy_bench.py b/src/devicer/benchmarks/accuracy_bench.py
index 1b2f5f8..9dc46e0 100644
--- a/src/devicer/benchmarks/accuracy_bench.py
+++ b/src/devicer/benchmarks/accuracy_bench.py
@@ -7,7 +7,7 @@ from typing import Any, Dict, List
 
 from ..libs.confidence import calculate_confidence
 from .data_generator import LabeledFingerprint, generate_dataset
-from .metrics import BenchmarkResult, ScoredPair, calculate_metrics
+from .metrics import BenchmarkResult, ScoredPair, calculate_metrics, calculate_true_eer
 
 
 def _format_table(data: List[Dict[str, Any]]) -> str:
@@ -102,12 +102,20 @@ def run_accuracy_benchmark(
 
     results = calculate_metrics(scored_pairs)
     best = max(results, key=lambda item: item.f1)
+    true_eer = calculate_true_eer(results)
 
     output = "\n".join(
         [
             f"--- Accuracy Metrics ({datetime.now(UTC).isoformat()}) ---",
             _format_table([asdict(item) for item in results]),
-            f"Best threshold: {best.threshold} | F1: {best.f1:.3f} | EER: {best.eer:.3f}"
+            (
+                f"Best threshold (F1): {best.threshold} | "
+                f"F1: {best.f1:.3f} | FAR/FRR gap: {best.far_frr_gap:.3f}"
+            ),
+            (
+                f"True EER: {true_eer.eer:.3f} at threshold≈{true_eer.threshold:.2f} "
+                f"(FAR={true_eer.far:.3f}, FRR={true_eer.frr:.3f}, method={true_eer.method})"
+            ),
         ]
     )
 
diff --git a/src/devicer/benchmarks/demo_scenario_generator.py b/src/devicer/benchmarks/demo_scenario_generator.py
index 2649b7d..ab105a6 100644
--- a/src/devicer/benchmarks/demo_scenario_generator.py
+++ b/src/devicer/benchmarks/demo_scenario_generator.py
@@ -14,7 +14,7 @@ from scenario_generator import (
     get_scenario_types,
     get_scenario_categories,
 )
-from metrics import ScoredPair, calculate_metrics
+from metrics import ScoredPair, calculate_metrics, calculate_true_eer
 from scoring_breakdown import decompose_confidence, format_breakdown
 
 
@@ -296,7 +296,7 @@ def demo_profiled_scenario_benchmark():
     }
 
     threshold_f1_rows: List[Dict[str, Any]] = []
-    threshold_eer_rows: List[Dict[str, Any]] = []
+    threshold_gap_rows: List[Dict[str, Any]] = []
     for index in range(len(metrics_by_score["overall"])):
         overall_row = metrics_by_score["overall"][index]
         instance_row = metrics_by_score["same_instance"][index]
@@ -314,14 +314,14 @@ def demo_profiled_scenario_benchmark():
                 "entity_f1": entity_row.f1,
             }
         )
-        threshold_eer_rows.append(
+        threshold_gap_rows.append(
             {
                 "threshold": overall_row.threshold,
-                "overall_eer": overall_row.eer,
-                "instance_eer": instance_row.eer,
-                "environment_eer": environment_row.eer,
-                "device_eer": device_row.eer,
-                "entity_eer": entity_row.eer,
+                "overall_gap": overall_row.far_frr_gap,
+                "instance_gap": instance_row.far_frr_gap,
+                "environment_gap": environment_row.far_frr_gap,
+                "device_gap": device_row.far_frr_gap,
+                "entity_gap": entity_row.far_frr_gap,
             }
         )
 
@@ -351,6 +351,10 @@ def demo_profiled_scenario_benchmark():
         name: max(rows, key=lambda item: item.f1)
         for name, rows in metrics_by_score.items()
     }
+    true_eer_by_score = {
+        name: calculate_true_eer(rows)
+        for name, rows in metrics_by_score.items()
+    }
 
     print(f"Generated scenario pairs: {len(scored_pairs)}")
     print()
@@ -358,13 +362,21 @@ def demo_profiled_scenario_benchmark():
     print(_format_table(scenario_rows))
     print("Threshold Comparison (F1):")
     print(_format_table(threshold_f1_rows))
-    print("Threshold Comparison (EER):")
-    print(_format_table(threshold_eer_rows))
+    print("Threshold Comparison (FAR/FRR Gap):")
+    print(_format_table(threshold_gap_rows))
     for name in ["overall", "same_instance", "same_environment", "same_device", "same_entity"]:
         best = best_by_score[name]
         print(
-            f"Best {name}: threshold={best.threshold}, "
-            f"f1={best.f1:.3f}, eer={best.eer:.3f}"
+            f"Best {name} (F1): threshold={best.threshold}, "
+            f"f1={best.f1:.3f}, far_frr_gap={best.far_frr_gap:.3f}"
+        )
+    print()
+    for name in ["overall", "same_instance", "same_environment", "same_device", "same_entity"]:
+        eer = true_eer_by_score[name]
+        print(
+            f"True EER {name}: eer={eer.eer:.3f}, "
+            f"threshold≈{eer.threshold:.2f}, "
+            f"far={eer.far:.3f}, frr={eer.frr:.3f}, method={eer.method}"
         )
 
 
diff --git a/src/devicer/benchmarks/metrics.py b/src/devicer/benchmarks/metrics.py
index fc3aae9..230d238 100644
--- a/src/devicer/benchmarks/metrics.py
+++ b/src/devicer/benchmarks/metrics.py
@@ -18,7 +18,7 @@ class BenchmarkResult:
     f1: float
     far: float
     frr: float
-    eer: float
+    far_frr_gap: float
     attr: float
 
 
@@ -49,7 +49,7 @@ def calculate_metrics(
         recall = (tp / (tp + fn)) if (tp + fn) else 0.0
         far = (fp / (fp + tn)) if (fp + tn) else 0.0
         frr = (fn / (tp + fn)) if (tp + fn) else 0.0
-        eer = abs(far - frr)
+        far_frr_gap = abs(far - frr)
 
         attractor_impostors = [p for p in scored_pairs if (not p["sameDevice"]) and p["isAttractor"] is True]
         if attractor_impostors:
@@ -69,9 +69,88 @@ def calculate_metrics(
                 f1=f1,
                 far=far,
                 frr=frr,
-                eer=eer,
+                far_frr_gap=far_frr_gap,
                 attr=attr,
             )
         )
 
     return results
+
+
+@dataclass(frozen=True)
+class EqualErrorRateResult:
+    threshold: float
+    eer: float
+    far: float
+    frr: float
+    method: str
+
+
+def calculate_true_eer(results: Sequence[BenchmarkResult]) -> EqualErrorRateResult:
+    """
+    Compute true Equal Error Rate (EER) from FAR/FRR threshold sweep results.
+
+    If FAR and FRR cross between sampled thresholds, linearly interpolate the
+    crossing point. If no crossing exists in sampled points, use the nearest
+    threshold by |FAR - FRR| and report average(FAR, FRR) there.
+    """
+    if not results:
+        return EqualErrorRateResult(
+            threshold=0.0,
+            eer=0.0,
+            far=0.0,
+            frr=0.0,
+            method="empty",
+        )
+
+    ordered = sorted(results, key=lambda item: item.threshold)
+    previous = ordered[0]
+    previous_delta = previous.far - previous.frr
+
+    if previous_delta == 0:
+        return EqualErrorRateResult(
+            threshold=float(previous.threshold),
+            eer=previous.far,
+            far=previous.far,
+            frr=previous.frr,
+            method="exact_threshold",
+        )
+
+    for current in ordered[1:]:
+        current_delta = current.far - current.frr
+
+        if current_delta == 0:
+            return EqualErrorRateResult(
+                threshold=float(current.threshold),
+                eer=current.far,
+                far=current.far,
+                frr=current.frr,
+                method="exact_threshold",
+            )
+
+        if previous_delta * current_delta < 0:
+            interpolation = previous_delta / (previous_delta - current_delta)
+            threshold = previous.threshold + interpolation * (current.threshold - previous.threshold)
+            far = previous.far + interpolation * (current.far - previous.far)
+            frr = previous.frr + interpolation * (current.frr - previous.frr)
+            eer = (far + frr) / 2.0
+            return EqualErrorRateResult(
+                threshold=float(threshold),
+                eer=eer,
+                far=far,
+                frr=frr,
+                method="interpolated_crossing",
+            )
+
+        previous = current
+        previous_delta = current_delta
+
+    nearest = min(ordered, key=lambda item: abs(item.far - item.frr))
+    eer = (nearest.far + nearest.frr) / 2.0
+    return EqualErrorRateResult(
+        threshold=float(nearest.threshold),
+        eer=eer,
+        far=nearest.far,
+        frr=nearest.frr,
+        method="nearest_threshold",
+    )
diff --git a/src/devicer/benchmarks/scoring_breakdown.py b/src/devicer/benchmarks/scoring_breakdown.py
index c01701d..ef77341 100644
--- a/src/devicer/benchmarks/scoring_breakdown.py
+++ b/src/devicer/benchmarks/scoring_breakdown.py
@@ -693,7 +693,7 @@ def format_breakdown(breakdown: ScoreBreakdown) -> str:
 from typing import Any, Dict, List
 
 from data_generator import LabeledFingerprint, generate_dataset, mutate, create_base_fingerprint
-from metrics import ScoredPair, calculate_metrics
+from metrics import ScoredPair, calculate_metrics, calculate_true_eer
 
 try:
     from devicer.libs.confidence import calculate_confidence
@@ -838,7 +838,7 @@ def demo_large_dataset_comparison():
     }
 
     threshold_f1_rows: List[Dict[str, Any]] = []
-    threshold_eer_rows: List[Dict[str, Any]] = []
+    threshold_gap_rows: List[Dict[str, Any]] = []
     for index in range(len(metrics_by_score["legacy"])):
         legacy_row = metrics_by_score["legacy"][index]
         instance_row = metrics_by_score["same_instance"][index]
@@ -856,14 +856,14 @@ def demo_large_dataset_comparison():
                 "entity_f1": entity_row.f1,
             }
         )
-        threshold_eer_rows.append(
+        threshold_gap_rows.append(
             {
                 "threshold": legacy_row.threshold,
-                "legacy_eer": legacy_row.eer,
-                "instance_eer": instance_row.eer,
-                "environment_eer": env_row.eer,
-                "device_eer": device_row.eer,
-                "entity_eer": entity_row.eer,
+                "legacy_gap": legacy_row.far_frr_gap,
+                "instance_gap": instance_row.far_frr_gap,
+                "environment_gap": env_row.far_frr_gap,
+                "device_gap": device_row.far_frr_gap,
+                "entity_gap": entity_row.far_frr_gap,
             }
         )
 
@@ -911,6 +911,10 @@ def demo_large_dataset_comparison():
         name: max(rows, key=lambda item: item.f1)
         for name, rows in metrics_by_score.items()
     }
+    true_eer_by_profile = {
+        name: calculate_true_eer(rows)
+        for name, rows in metrics_by_score.items()
+    }
 
     print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
     print(f"Compared pairs: {len(pairs)}")
@@ -919,13 +923,21 @@ def demo_large_dataset_comparison():
     print(_format_table(cohort_rows))
     print("Threshold Comparison (F1):")
     print(_format_table(threshold_f1_rows))
-    print("Threshold Comparison (EER):")
-    print(_format_table(threshold_eer_rows))
+    print("Threshold Comparison (FAR/FRR Gap):")
+    print(_format_table(threshold_gap_rows))
     for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
         best = best_by_profile[name]
         print(
             f"Best {name}: "
-            f"threshold={best.threshold}, f1={best.f1:.3f}, eer={best.eer:.3f}"
+            f"threshold={best.threshold}, f1={best.f1:.3f}, far_frr_gap={best.far_frr_gap:.3f}"
+        )
+    print()
+    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
+        eer = true_eer_by_profile[name]
+        print(
+            f"True EER {name}: eer={eer.eer:.3f}, "
+            f"threshold≈{eer.threshold:.2f}, far={eer.far:.3f}, "
+            f"frr={eer.frr:.3f}, method={eer.method}"
         )
 
 
diff --git a/tests/benchmarks/test_metrics.py b/tests/benchmarks/test_metrics.py
index 011e685..75f1a75 100644
--- a/tests/benchmarks/test_metrics.py
+++ b/tests/benchmarks/test_metrics.py
@@ -1,4 +1,6 @@
-from devicer.benchmarks.metrics import calculate_metrics
+import pytest
+
+from devicer.benchmarks.metrics import BenchmarkResult, calculate_metrics, calculate_true_eer
 
 
 def test_calculate_metrics_basic_parity_math():
@@ -17,7 +19,7 @@ def test_calculate_metrics_basic_parity_math():
     assert result.recall == 1.0
     assert result.far == 0.5
     assert result.frr == 0.0
-    assert result.eer == 0.5
+    assert result.far_frr_gap == 0.5
     assert result.attr == 1.0
 
 
@@ -27,3 +29,33 @@ def test_calculate_metrics_default_threshold_count():
     assert len(results) == 21
     assert results[0].threshold == 0
     assert results[-1].threshold == 100
+
+
+def test_calculate_true_eer_interpolates_crossing():
+    rows = [
+        BenchmarkResult(80, 0.0, 0.0, 0.0, far=0.4, frr=0.2, far_frr_gap=0.2, attr=0.0),
+        BenchmarkResult(90, 0.0, 0.0, 0.0, far=0.2, frr=0.4, far_frr_gap=0.2, attr=0.0),
+    ]
+
+    eer = calculate_true_eer(rows)
+
+    assert eer.method == "interpolated_crossing"
+    assert eer.threshold == pytest.approx(85.0)
+    assert eer.eer == pytest.approx(0.3)
+    assert eer.far == pytest.approx(0.3)
+    assert eer.frr == pytest.approx(0.3)
+
+
+def test_calculate_true_eer_falls_back_to_nearest_threshold():
+    rows = [
+        BenchmarkResult(80, 0.0, 0.0, 0.0, far=0.5, frr=0.1, far_frr_gap=0.4, attr=0.0),
+        BenchmarkResult(90, 0.0, 0.0, 0.0, far=0.2, frr=0.05, far_frr_gap=0.15, attr=0.0),
+    ]
+
+    eer = calculate_true_eer(rows)
+
+    assert eer.method == "nearest_threshold"
+    assert eer.threshold == 90.0
+    assert eer.eer == 0.125
+    assert eer.far == 0.2
+    assert eer.frr == 0.05
```


---

### Navigation
[← Previous (Commit 22)](7855254_some_realist.md) | [Back to Index](./index.md) | [Next (Commit 24) →](12b11d3_use_small_ep.md)
