# Commit: also fixed eer in last commit, now adding the new eer and old far/frr columns
**Hash:** `857215157d2347f9a214ec469e46198a3de64d0f`  
**Date:** 2026-03-19  

## Editorial Rationale

>  this is just some changes to the still-forming metrics output for the repots.

---

## Technical Diffs
```diff
commit 857215157d2347f9a214ec469e46198a3de64d0f
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 10:18:13 2026 -0500

    also fixed eer in last commit, now adding the new eer and old far/frr columns

diff --git a/src/devicer/benchmarks/accuracy_bench.py b/src/devicer/benchmarks/accuracy_bench.py
index 9dc46e0..322207c 100644
--- a/src/devicer/benchmarks/accuracy_bench.py
+++ b/src/devicer/benchmarks/accuracy_bench.py
@@ -1,6 +1,5 @@
 from __future__ import annotations
 
-from dataclasses import asdict
 from datetime import UTC, datetime
 from pathlib import Path
 from typing import Any, Dict, List
@@ -103,19 +102,34 @@ def run_accuracy_benchmark(
     results = calculate_metrics(scored_pairs)
     best = max(results, key=lambda item: item.f1)
     true_eer = calculate_true_eer(results)
+    per_threshold_rows = [
+        {
+            "threshold": row.threshold,
+            "precision": row.precision,
+            "recall": row.recall,
+            "f1": row.f1,
+            "far": row.far,
+            "frr": row.frr,
+            "gap_far_frr": row.far_frr_gap,
+        }
+        for row in results
+    ]
+    summary_rows = [
+        {
+            "best_f1_threshold": best.threshold,
+            "best_f1": best.f1,
+            "eer_threshold": true_eer.threshold,
+            "eer": true_eer.eer,
+        }
+    ]
 
     output = "\n".join(
         [
             f"--- Accuracy Metrics ({datetime.now(UTC).isoformat()}) ---",
-            _format_table([asdict(item) for item in results]),
-            (
-                f"Best threshold (F1): {best.threshold} | "
-                f"F1: {best.f1:.3f} | FAR/FRR gap: {best.far_frr_gap:.3f}"
-            ),
-            (
-                f"True EER: {true_eer.eer:.3f} at threshold≈{true_eer.threshold:.2f} "
-                f"(FAR={true_eer.far:.3f}, FRR={true_eer.frr:.3f}, method={true_eer.method})"
-            ),
+            "Per-threshold table:",
+            _format_table(per_threshold_rows),
+            "Benchmark summary:",
+            _format_table(summary_rows),
         ]
     )
 
diff --git a/src/devicer/benchmarks/demo_scenario_generator.py b/src/devicer/benchmarks/demo_scenario_generator.py
index ab105a6..b15f89f 100644
--- a/src/devicer/benchmarks/demo_scenario_generator.py
+++ b/src/devicer/benchmarks/demo_scenario_generator.py
@@ -355,29 +355,44 @@ def demo_profiled_scenario_benchmark():
         name: calculate_true_eer(rows)
         for name, rows in metrics_by_score.items()
     }
+    per_threshold_rows = [
+        {
+            "threshold": row.threshold,
+            "precision": row.precision,
+            "recall": row.recall,
+            "f1": row.f1,
+            "far": row.far,
+            "frr": row.frr,
+            "gap_far_frr": row.far_frr_gap,
+        }
+        for row in metrics_by_score["overall"]
+    ]
+    summary_rows = []
+    for name in ["overall", "same_instance", "same_environment", "same_device", "same_entity"]:
+        best = best_by_score[name]
+        eer = true_eer_by_score[name]
+        summary_rows.append(
+            {
+                "profile": name,
+                "best_f1_threshold": best.threshold,
+                "best_f1": best.f1,
+                "eer_threshold": eer.threshold,
+                "eer": eer.eer,
+            }
+        )
 
     print(f"Generated scenario pairs: {len(scored_pairs)}")
     print()
     print("Scenario Type Means:")
     print(_format_table(scenario_rows))
+    print("Per-threshold table (overall):")
+    print(_format_table(per_threshold_rows))
+    print("Benchmark summary:")
+    print(_format_table(summary_rows))
     print("Threshold Comparison (F1):")
     print(_format_table(threshold_f1_rows))
     print("Threshold Comparison (FAR/FRR Gap):")
     print(_format_table(threshold_gap_rows))
-    for name in ["overall", "same_instance", "same_environment", "same_device", "same_entity"]:
-        best = best_by_score[name]
-        print(
-            f"Best {name} (F1): threshold={best.threshold}, "
-            f"f1={best.f1:.3f}, far_frr_gap={best.far_frr_gap:.3f}"
-        )
-    print()
-    for name in ["overall", "same_instance", "same_environment", "same_device", "same_entity"]:
-        eer = true_eer_by_score[name]
-        print(
-            f"True EER {name}: eer={eer.eer:.3f}, "
-            f"threshold≈{eer.threshold:.2f}, "
-            f"far={eer.far:.3f}, frr={eer.frr:.3f}, method={eer.method}"
-        )
 
 
 def main():
diff --git a/src/devicer/benchmarks/scoring_breakdown.py b/src/devicer/benchmarks/scoring_breakdown.py
index ef77341..8ecd055 100644
--- a/src/devicer/benchmarks/scoring_breakdown.py
+++ b/src/devicer/benchmarks/scoring_breakdown.py
@@ -915,30 +915,45 @@ def demo_large_dataset_comparison():
         name: calculate_true_eer(rows)
         for name, rows in metrics_by_score.items()
     }
+    per_threshold_rows = [
+        {
+            "threshold": row.threshold,
+            "precision": row.precision,
+            "recall": row.recall,
+            "f1": row.f1,
+            "far": row.far,
+            "frr": row.frr,
+            "gap_far_frr": row.far_frr_gap,
+        }
+        for row in metrics_by_score["legacy"]
+    ]
+    summary_rows = []
+    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
+        best = best_by_profile[name]
+        eer = true_eer_by_profile[name]
+        summary_rows.append(
+            {
+                "profile": name,
+                "best_f1_threshold": best.threshold,
+                "best_f1": best.f1,
+                "eer_threshold": eer.threshold,
+                "eer": eer.eer,
+            }
+        )
 
     print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
     print(f"Compared pairs: {len(pairs)}")
     print()
     print("Cohort Summary (means):")
     print(_format_table(cohort_rows))
+    print("Per-threshold table (legacy):")
+    print(_format_table(per_threshold_rows))
+    print("Benchmark summary:")
+    print(_format_table(summary_rows))
     print("Threshold Comparison (F1):")
     print(_format_table(threshold_f1_rows))
     print("Threshold Comparison (FAR/FRR Gap):")
     print(_format_table(threshold_gap_rows))
-    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
-        best = best_by_profile[name]
-        print(
-            f"Best {name}: "
-            f"threshold={best.threshold}, f1={best.f1:.3f}, far_frr_gap={best.far_frr_gap:.3f}"
-        )
-    print()
-    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
-        eer = true_eer_by_profile[name]
-        print(
-            f"True EER {name}: eer={eer.eer:.3f}, "
-            f"threshold≈{eer.threshold:.2f}, far={eer.far:.3f}, "
-            f"frr={eer.frr:.3f}, method={eer.method}"
-        )
 
 
 def demo_basic_comparison():
```


---

### Navigation
[← Previous (Commit 24)](12b11d3_use_small_ep.md) | [Back to Index](./index.md) | [Next (Commit 26) →](cdc9e0f_commit_accur.md)
