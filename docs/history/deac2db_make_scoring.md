# Commit: make scoring_breakdown more in-line with existing benchmarks, but without adding imports for them
**Hash:** `deac2db6b612dffb1b625ab42d53d3c844a7e57e`  
**Date:** 2026-03-19  

## Editorial Rationale

> This was just getting rid of the separate "demo_" script, and stickign the calls  under a main() it scoring_breakdown.py

---

## Technical Diffs
```diff
commit deac2db6b612dffb1b625ab42d53d3c844a7e57e
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 09:25:33 2026 -0500

    make scoring_breakdown more in-line with existing benchmarks, but without adding imports for them

diff --git a/src/devicer/benchmarks/demo_scoring_breakdown.py b/src/devicer/benchmarks/demo_scoring_breakdown.py
deleted file mode 100644
index ae33fb1..0000000
--- a/src/devicer/benchmarks/demo_scoring_breakdown.py
+++ /dev/null
@@ -1,409 +0,0 @@
-"""
-Demo script for scoring_breakdown.py
-
-Shows how to use the multi-dimensional scoring system
-"""
-
-from __future__ import annotations
-
-from pathlib import Path
-import sys
-from typing import Any, Dict, List
-
-from data_generator import LabeledFingerprint, generate_dataset, mutate, create_base_fingerprint
-from metrics import ScoredPair, calculate_metrics
-from scoring_breakdown import (
-    decompose_confidence,
-    format_breakdown,
-    calculate_evidence_richness,
-    calculate_attractor_risk,
-)
-
-try:
-    from devicer.libs.confidence import calculate_confidence
-except ModuleNotFoundError:
-    # Allows running this script directly from `src/devicer/benchmarks/`.
-    src_root = Path(__file__).resolve().parents[2]
-    if str(src_root) not in sys.path:
-        sys.path.insert(0, str(src_root))
-    from devicer.libs.confidence import calculate_confidence
-
-
-def _format_table(data: List[Dict[str, Any]]) -> str:
-    if not data:
-        return "(empty)\n"
-
-    keys = list(data[0].keys())
-    rows: List[List[str]] = []
-    for row in data:
-        values: List[str] = []
-        for key in keys:
-            val = row.get(key)
-            values.append(f"{val:.3f}" if isinstance(val, float) else str(val))
-        rows.append(values)
-
-    col_widths = [max(len(keys[i]), *(len(row[i]) for row in rows)) for i in range(len(keys))]
-    sep = "-+-".join("-" * width for width in col_widths)
-    header = " | ".join(keys[i].ljust(col_widths[i]) for i in range(len(keys)))
-    body = "\n".join(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(keys))) for row in rows)
-    return f"{header}\n{sep}\n{body}\n"
-
-
-def _average(values: List[float]) -> float:
-    return (sum(values) / len(values)) if values else 0.0
-
-
-def _score_pair(
-    left: LabeledFingerprint,
-    right: LabeledFingerprint,
-    same_device: bool,
-) -> Dict[str, Any]:
-    breakdown = decompose_confidence(left.data, right.data, top_n=0)
-    profile_scores = breakdown.profile_scores
-    return {
-        "legacyScore": float(calculate_confidence(left.data, right.data)),
-        "breakdownScore": float(profile_scores.get("same_device", breakdown.overall_confidence)),
-        "same_instance": float(profile_scores.get("same_instance", breakdown.overall_confidence)),
-        "same_environment": float(profile_scores.get("same_environment", breakdown.overall_confidence)),
-        "same_device": float(profile_scores.get("same_device", breakdown.overall_confidence)),
-        "same_entity": float(profile_scores.get("same_entity", breakdown.overall_confidence)),
-        "evidenceRichness": float(breakdown.evidence_richness),
-        "deviceSimilarity": float(breakdown.device_similarity),
-        "entropyContribution": float(breakdown.entropy_contribution),
-        "attractorRisk": float(breakdown.attractor_risk),
-        "sameDevice": same_device,
-        "isAttractor": bool(left.is_attractor or right.is_attractor),
-    }
-
-
-def _generate_comparison_pairs(
-    groups: Dict[str, List[LabeledFingerprint]],
-    iterations: int = 2500,
-) -> List[Dict[str, Any]]:
-    devices = list(groups.keys())
-    sorted_by_size = sorted(devices, key=lambda x: len(groups[x]), reverse=True)
-    attractor_pool_size = max(1, int(len(sorted_by_size) * 0.1 + 0.9999))
-
-    scored_pairs: List[Dict[str, Any]] = []
-    for i in range(iterations):
-        dev = devices[i % len(devices)]
-        samples = groups[dev]
-        if len(samples) < 2:
-            continue
-
-        idx1 = i % len(samples)
-        idx2 = (idx1 + 1 + i) % len(samples)
-        a = samples[idx1]
-        b = samples[idx2]
-        scored_pairs.append(_score_pair(a, b, same_device=True))
-
-        dev2 = devices[(i + 1) % len(devices)]
-        c = groups[dev2][i % len(groups[dev2])]
-        d = groups[dev][(idx1 + 3) % len(samples)]
-
-        use_cross_browser = (i % 10) < 3
-        if use_cross_browser and len(samples) >= 2:
-            idx3 = (idx1 + (len(samples) // 2)) % len(samples)
-            cross_a = samples[idx3]
-            attractor_dev = sorted_by_size[i % attractor_pool_size]
-            attractor_samples = groups[attractor_dev]
-            attractor_sample = attractor_samples[i % len(attractor_samples)]
-            cross_b = (
-                attractor_sample
-                if attractor_dev != dev
-                else groups[dev2][i % len(groups[dev2])]
-            )
-            scored_pairs.append(_score_pair(cross_a, cross_b, same_device=False))
-
-        scored_pairs.append(_score_pair(c, d, same_device=False))
-
-    return scored_pairs
-
-
-def _as_metric_inputs(
-    pairs: List[Dict[str, Any]],
-    score_key: str,
-) -> List[ScoredPair]:
-    return [
-        {
-            "score": float(pair[score_key]),
-            "sameDevice": bool(pair["sameDevice"]),
-            "isAttractor": bool(pair["isAttractor"]),
-        }
-        for pair in pairs
-    ]
-
-
-def demo_large_dataset_comparison():
-    """Demo: large-sample benchmark comparing scalar confidence vs breakdown score."""
-    print("=" * 70)
-    print("DEMO 7: Large Dataset Threshold Comparison")
-    print("=" * 70)
-
-    dataset_size = 2000
-    sessions_per_device = 5
-
-    dataset = generate_dataset(size=dataset_size, sessions_per_device=sessions_per_device)
-    groups: Dict[str, List[LabeledFingerprint]] = {}
-    for item in dataset:
-        groups.setdefault(item.device_label, []).append(item)
-
-    pairs = _generate_comparison_pairs(groups, iterations=2500)
-
-    metrics_by_score = {
-        "legacy": calculate_metrics(_as_metric_inputs(pairs, "legacyScore")),
-        "same_instance": calculate_metrics(_as_metric_inputs(pairs, "same_instance")),
-        "same_environment": calculate_metrics(_as_metric_inputs(pairs, "same_environment")),
-        "same_device": calculate_metrics(_as_metric_inputs(pairs, "same_device")),
-        "same_entity": calculate_metrics(_as_metric_inputs(pairs, "same_entity")),
-    }
-
-    threshold_f1_rows: List[Dict[str, Any]] = []
-    threshold_eer_rows: List[Dict[str, Any]] = []
-    for index in range(len(metrics_by_score["legacy"])):
-        legacy_row = metrics_by_score["legacy"][index]
-        instance_row = metrics_by_score["same_instance"][index]
-        env_row = metrics_by_score["same_environment"][index]
-        device_row = metrics_by_score["same_device"][index]
-        entity_row = metrics_by_score["same_entity"][index]
-
-        threshold_f1_rows.append(
-            {
-                "threshold": legacy_row.threshold,
-                "legacy_f1": legacy_row.f1,
-                "instance_f1": instance_row.f1,
-                "environment_f1": env_row.f1,
-                "device_f1": device_row.f1,
-                "entity_f1": entity_row.f1,
-            }
-        )
-        threshold_eer_rows.append(
-            {
-                "threshold": legacy_row.threshold,
-                "legacy_eer": legacy_row.eer,
-                "instance_eer": instance_row.eer,
-                "environment_eer": env_row.eer,
-                "device_eer": device_row.eer,
-                "entity_eer": entity_row.eer,
-            }
-        )
-
-    same_pairs = [pair for pair in pairs if pair["sameDevice"]]
-    diff_pairs = [pair for pair in pairs if not pair["sameDevice"]]
-    attractor_impostors = [
-        pair for pair in diff_pairs if pair["isAttractor"]
-    ]
-
-    cohort_rows = []
-    for name, bucket in [
-        ("sameDevice", same_pairs),
-        ("differentDevice", diff_pairs),
-        ("attractorImpostor", attractor_impostors),
-    ]:
-        cohort_rows.append(
-            {
-                "cohort": name,
-                "pairs": len(bucket),
-                "legacy_mean": _average([float(p["legacyScore"]) for p in bucket]),
-                "same_instance_mean": _average([float(p["same_instance"]) for p in bucket]),
-                "same_environment_mean": _average([float(p["same_environment"]) for p in bucket]),
-                "same_device_mean": _average([float(p["same_device"]) for p in bucket]),
-                "same_entity_mean": _average([float(p["same_entity"]) for p in bucket]),
-                "richness_mean": _average([float(p["evidenceRichness"]) for p in bucket]),
-                "attractor_risk_mean": _average([float(p["attractorRisk"]) for p in bucket]),
-            }
-        )
-
-    cohort_rows.append(
-        {
-            "cohort": "separation(same-diff)",
-            "pairs": "-",
-            "legacy_mean": cohort_rows[0]["legacy_mean"] - cohort_rows[1]["legacy_mean"],
-            "same_instance_mean": cohort_rows[0]["same_instance_mean"] - cohort_rows[1]["same_instance_mean"],
-            "same_environment_mean": cohort_rows[0]["same_environment_mean"] - cohort_rows[1]["same_environment_mean"],
-            "same_device_mean": cohort_rows[0]["same_device_mean"] - cohort_rows[1]["same_device_mean"],
-            "same_entity_mean": cohort_rows[0]["same_entity_mean"] - cohort_rows[1]["same_entity_mean"],
-            "richness_mean": cohort_rows[0]["richness_mean"] - cohort_rows[1]["richness_mean"],
-            "attractor_risk_mean": "-",
-        }
-    )
-
-    best_by_profile = {
-        name: max(rows, key=lambda item: item.f1)
-        for name, rows in metrics_by_score.items()
-    }
-
-    print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
-    print(f"Compared pairs: {len(pairs)}")
-    print()
-    print("Cohort Summary (means):")
-    print(_format_table(cohort_rows))
-    print("Threshold Comparison (F1):")
-    print(_format_table(threshold_f1_rows))
-    print("Threshold Comparison (EER):")
-    print(_format_table(threshold_eer_rows))
-    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
-        best = best_by_profile[name]
-        print(
-            f"Best {name}: "
-            f"threshold={best.threshold}, f1={best.f1:.3f}, eer={best.eer:.3f}"
-        )
-
-
-def demo_basic_comparison():
-    """Demo: Compare two fingerprints from same device"""
-    print("=" * 70)
-    print("DEMO 1: Same Device, Minor Drift")
-    print("=" * 70)
-    
-    # Generate base fingerprint
-    base = create_base_fingerprint(12345)
-    
-    # Create slightly mutated version (low drift)
-    mutated = mutate(base, "low")
-    
-    # Decompose the comparison
-    breakdown = decompose_confidence(base, mutated, top_n=5)
-    
-    print(format_breakdown(breakdown))
-
-
-def demo_cross_browser():
-    """Demo: Same device, different browser"""
-    print("=" * 70)
-    print("DEMO 2: Same Device, High Drift (Cross-Browser Simulation)")
-    print("=" * 70)
-    
-    base = create_base_fingerprint(12345)
-    high_drift = mutate(base, "high")
-    
-    breakdown = decompose_confidence(base, high_drift, top_n=5)
-    
-    print(format_breakdown(breakdown))
-
-
-def demo_different_devices():
-    """Demo: Different devices"""
-    print("=" * 70)
-    print("DEMO 3: Different Devices")
-    print("=" * 70)
-    
-    device_a = create_base_fingerprint(11111)
-    device_b = create_base_fingerprint(22222)
-    
-    breakdown = decompose_confidence(device_a, device_b, top_n=5)
-    
-    print(format_breakdown(breakdown))
-
-
-def demo_evidence_richness():
-    """Demo: Evidence richness calculation"""
-    print("=" * 70)
-    print("DEMO 4: Evidence Richness")
-    print("=" * 70)
-    
-    rich_fp = create_base_fingerprint(12345)
-    
-    # Create sparse fingerprint (missing fields)
-    sparse_fp = {
-        "userAgent": rich_fp["userAgent"],
-        "platform": rich_fp["platform"],
-        "timezone": "America/New_York",
-    }
-    
-    rich_score = calculate_evidence_richness(rich_fp)
-    sparse_score = calculate_evidence_richness(sparse_fp)
-    
-    print(f"Rich fingerprint evidence score: {rich_score:.1f}/100")
-    print(f"Sparse fingerprint evidence score: {sparse_score:.1f}/100")
-    print()
-    
-    # Compare them
-    breakdown = decompose_confidence(rich_fp, sparse_fp, top_n=5)
-    print(format_breakdown(breakdown))
-
-
-def demo_attractor_risk():
-    """Demo: Attractor risk calculation"""
-    print("=" * 70)
-    print("DEMO 5: Attractor Risk Detection")
-    print("=" * 70)
-    
-    # Generic Windows + Chrome fingerprint (high attractor risk)
-    generic_fp = {
-        "platform": "Win32",
-        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
-        "deviceMemory": 8,
-        "hardwareConcurrency": 8,
-        "language": "en-US",
-        "timezone": "America/New_York",
-        "fonts": ["Arial", "Times New Roman"],  # Very few fonts
-    }
-    
-    # Unique fingerprint (low attractor risk)
-    unique_fp = create_base_fingerprint(99999)
-    
-    generic_risk = calculate_attractor_risk(generic_fp)
-    unique_risk = calculate_attractor_risk(unique_fp)
-    
-    print(f"Generic fingerprint attractor risk: {generic_risk:.1f}/100")
-    print(f"Unique fingerprint attractor risk: {unique_risk:.1f}/100")
-    print()
-
-
-def demo_dataset_analysis():
-    """Demo: Analyze a small dataset"""
-    print("=" * 70)
-    print("DEMO 6: Dataset Analysis")
-    print("=" * 70)
-    
-    # Generate small dataset
-    dataset = generate_dataset(size=5, sessions_per_device=2)
-    
-    # Compare first two sessions of same device
-    device_sessions = {}
-    for item in dataset:
-        device_sessions.setdefault(item.device_label, []).append(item)
-    
-    for device_id, sessions in list(device_sessions.items())[:2]:
-        if len(sessions) >= 2:
-            print(f"\n--- Device: {device_id[:12]}... ---")
-            print(f"Is Attractor: {sessions[0].is_attractor}")
-            
-            breakdown = decompose_confidence(
-                sessions[0].data,
-                sessions[1].data,
-                top_n=3
-            )
-            
-            print(f"Overall Confidence: {breakdown.overall_confidence:.1f}/100")
-            print(f"Device Similarity: {breakdown.device_similarity:.1f}/100")
-            print(f"Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
-            print(f"Attractor Risk: {breakdown.attractor_risk:.1f}/100")
-
-
-def main():
-    """Run all demos"""
-    demo_basic_comparison()
-    print("\n\n")
-    
-    demo_cross_browser()
-    print("\n\n")
-    
-    demo_different_devices()
-    print("\n\n")
-    
-    demo_evidence_richness()
-    print("\n\n")
-    
-    demo_attractor_risk()
-    print("\n\n")
-    
-    demo_dataset_analysis()
-    print("\n\n")
-
-    demo_large_dataset_comparison()
-
-
-if __name__ == "__main__":
-    main()
diff --git a/src/devicer/benchmarks/scoring_breakdown.py b/src/devicer/benchmarks/scoring_breakdown.py
index 108e400..c01701d 100644
--- a/src/devicer/benchmarks/scoring_breakdown.py
+++ b/src/devicer/benchmarks/scoring_breakdown.py
@@ -687,3 +687,394 @@ def format_breakdown(breakdown: ScoreBreakdown) -> str:
         lines.append("")
     
     return "\n".join(lines)
+
+#### DEMO
+
+from typing import Any, Dict, List
+
+from data_generator import LabeledFingerprint, generate_dataset, mutate, create_base_fingerprint
+from metrics import ScoredPair, calculate_metrics
+
+try:
+    from devicer.libs.confidence import calculate_confidence
+except ModuleNotFoundError:
+    # Allows running this script directly from `src/devicer/benchmarks/`.
+    # get rid of this eventually by adding scripts stubs to   pyproject.toml 
+    from pathlib import Path
+    import sys
+    src_root = Path(__file__).resolve().parents[2]
+    if str(src_root) not in sys.path:
+        sys.path.insert(0, str(src_root))
+    from devicer.libs.confidence import calculate_confidence
+
+
+def _format_table(data: List[Dict[str, Any]]) -> str:
+    if not data:
+        return "(empty)\n"
+
+    keys = list(data[0].keys())
+    rows: List[List[str]] = []
+    for row in data:
+        values: List[str] = []
+        for key in keys:
+            val = row.get(key)
+            values.append(f"{val:.3f}" if isinstance(val, float) else str(val))
+        rows.append(values)
+
+    col_widths = [max(len(keys[i]), *(len(row[i]) for row in rows)) for i in range(len(keys))]
+    sep = "-+-".join("-" * width for width in col_widths)
+    header = " | ".join(keys[i].ljust(col_widths[i]) for i in range(len(keys)))
+    body = "\n".join(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(keys))) for row in rows)
+    return f"{header}\n{sep}\n{body}\n"
+
+
+def _average(values: List[float]) -> float:
+    return (sum(values) / len(values)) if values else 0.0
+
+
+def _score_pair(
+    left: LabeledFingerprint,
+    right: LabeledFingerprint,
+    same_device: bool,
+) -> Dict[str, Any]:
+    breakdown = decompose_confidence(left.data, right.data, top_n=0)
+    profile_scores = breakdown.profile_scores
+    return {
+        "legacyScore": float(calculate_confidence(left.data, right.data)),
+        "breakdownScore": float(profile_scores.get("same_device", breakdown.overall_confidence)),
+        "same_instance": float(profile_scores.get("same_instance", breakdown.overall_confidence)),
+        "same_environment": float(profile_scores.get("same_environment", breakdown.overall_confidence)),
+        "same_device": float(profile_scores.get("same_device", breakdown.overall_confidence)),
+        "same_entity": float(profile_scores.get("same_entity", breakdown.overall_confidence)),
+        "evidenceRichness": float(breakdown.evidence_richness),
+        "deviceSimilarity": float(breakdown.device_similarity),
+        "entropyContribution": float(breakdown.entropy_contribution),
+        "attractorRisk": float(breakdown.attractor_risk),
+        "sameDevice": same_device,
+        "isAttractor": bool(left.is_attractor or right.is_attractor),
+    }
+
+
+def _generate_comparison_pairs(
+    groups: Dict[str, List[LabeledFingerprint]],
+    iterations: int = 2500,
+) -> List[Dict[str, Any]]:
+    devices = list(groups.keys())
+    sorted_by_size = sorted(devices, key=lambda x: len(groups[x]), reverse=True)
+    attractor_pool_size = max(1, int(len(sorted_by_size) * 0.1 + 0.9999))
+
+    scored_pairs: List[Dict[str, Any]] = []
+    for i in range(iterations):
+        dev = devices[i % len(devices)]
+        samples = groups[dev]
+        if len(samples) < 2:
+            continue
+
+        idx1 = i % len(samples)
+        idx2 = (idx1 + 1 + i) % len(samples)
+        a = samples[idx1]
+        b = samples[idx2]
+        scored_pairs.append(_score_pair(a, b, same_device=True))
+
+        dev2 = devices[(i + 1) % len(devices)]
+        c = groups[dev2][i % len(groups[dev2])]
+        d = groups[dev][(idx1 + 3) % len(samples)]
+
+        use_cross_browser = (i % 10) < 3
+        if use_cross_browser and len(samples) >= 2:
+            idx3 = (idx1 + (len(samples) // 2)) % len(samples)
+            cross_a = samples[idx3]
+            attractor_dev = sorted_by_size[i % attractor_pool_size]
+            attractor_samples = groups[attractor_dev]
+            attractor_sample = attractor_samples[i % len(attractor_samples)]
+            cross_b = (
+                attractor_sample
+                if attractor_dev != dev
+                else groups[dev2][i % len(groups[dev2])]
+            )
+            scored_pairs.append(_score_pair(cross_a, cross_b, same_device=False))
+
+        scored_pairs.append(_score_pair(c, d, same_device=False))
+
+    return scored_pairs
+
+
+def _as_metric_inputs(
+    pairs: List[Dict[str, Any]],
+    score_key: str,
+) -> List[ScoredPair]:
+    return [
+        {
+            "score": float(pair[score_key]),
+            "sameDevice": bool(pair["sameDevice"]),
+            "isAttractor": bool(pair["isAttractor"]),
+        }
+        for pair in pairs
+    ]
+
+
+def demo_large_dataset_comparison():
+    """Demo: large-sample benchmark comparing scalar confidence vs breakdown score."""
+    print("=" * 70)
+    print("DEMO 7: Large Dataset Threshold Comparison")
+    print("=" * 70)
+
+    dataset_size = 2000
+    sessions_per_device = 5
+
+    dataset = generate_dataset(size=dataset_size, sessions_per_device=sessions_per_device)
+    groups: Dict[str, List[LabeledFingerprint]] = {}
+    for item in dataset:
+        groups.setdefault(item.device_label, []).append(item)
+
+    pairs = _generate_comparison_pairs(groups, iterations=2500)
+
+    metrics_by_score = {
+        "legacy": calculate_metrics(_as_metric_inputs(pairs, "legacyScore")),
+        "same_instance": calculate_metrics(_as_metric_inputs(pairs, "same_instance")),
+        "same_environment": calculate_metrics(_as_metric_inputs(pairs, "same_environment")),
+        "same_device": calculate_metrics(_as_metric_inputs(pairs, "same_device")),
+        "same_entity": calculate_metrics(_as_metric_inputs(pairs, "same_entity")),
+    }
+
+    threshold_f1_rows: List[Dict[str, Any]] = []
+    threshold_eer_rows: List[Dict[str, Any]] = []
+    for index in range(len(metrics_by_score["legacy"])):
+        legacy_row = metrics_by_score["legacy"][index]
+        instance_row = metrics_by_score["same_instance"][index]
+        env_row = metrics_by_score["same_environment"][index]
+        device_row = metrics_by_score["same_device"][index]
+        entity_row = metrics_by_score["same_entity"][index]
+
+        threshold_f1_rows.append(
+            {
+                "threshold": legacy_row.threshold,
+                "legacy_f1": legacy_row.f1,
+                "instance_f1": instance_row.f1,
+                "environment_f1": env_row.f1,
+                "device_f1": device_row.f1,
+                "entity_f1": entity_row.f1,
+            }
+        )
+        threshold_eer_rows.append(
+            {
+                "threshold": legacy_row.threshold,
+                "legacy_eer": legacy_row.eer,
+                "instance_eer": instance_row.eer,
+                "environment_eer": env_row.eer,
+                "device_eer": device_row.eer,
+                "entity_eer": entity_row.eer,
+            }
+        )
+
+    same_pairs = [pair for pair in pairs if pair["sameDevice"]]
+    diff_pairs = [pair for pair in pairs if not pair["sameDevice"]]
+    attractor_impostors = [
+        pair for pair in diff_pairs if pair["isAttractor"]
+    ]
+
+    cohort_rows = []
+    for name, bucket in [
+        ("sameDevice", same_pairs),
+        ("differentDevice", diff_pairs),
+        ("attractorImpostor", attractor_impostors),
+    ]:
+        cohort_rows.append(
+            {
+                "cohort": name,
+                "pairs": len(bucket),
+                "legacy_mean": _average([float(p["legacyScore"]) for p in bucket]),
+                "same_instance_mean": _average([float(p["same_instance"]) for p in bucket]),
+                "same_environment_mean": _average([float(p["same_environment"]) for p in bucket]),
+                "same_device_mean": _average([float(p["same_device"]) for p in bucket]),
+                "same_entity_mean": _average([float(p["same_entity"]) for p in bucket]),
+                "richness_mean": _average([float(p["evidenceRichness"]) for p in bucket]),
+                "attractor_risk_mean": _average([float(p["attractorRisk"]) for p in bucket]),
+            }
+        )
+
+    cohort_rows.append(
+        {
+            "cohort": "separation(same-diff)",
+            "pairs": "-",
+            "legacy_mean": cohort_rows[0]["legacy_mean"] - cohort_rows[1]["legacy_mean"],
+            "same_instance_mean": cohort_rows[0]["same_instance_mean"] - cohort_rows[1]["same_instance_mean"],
+            "same_environment_mean": cohort_rows[0]["same_environment_mean"] - cohort_rows[1]["same_environment_mean"],
+            "same_device_mean": cohort_rows[0]["same_device_mean"] - cohort_rows[1]["same_device_mean"],
+            "same_entity_mean": cohort_rows[0]["same_entity_mean"] - cohort_rows[1]["same_entity_mean"],
+            "richness_mean": cohort_rows[0]["richness_mean"] - cohort_rows[1]["richness_mean"],
+            "attractor_risk_mean": "-",
+        }
+    )
+
+    best_by_profile = {
+        name: max(rows, key=lambda item: item.f1)
+        for name, rows in metrics_by_score.items()
+    }
+
+    print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
+    print(f"Compared pairs: {len(pairs)}")
+    print()
+    print("Cohort Summary (means):")
+    print(_format_table(cohort_rows))
+    print("Threshold Comparison (F1):")
+    print(_format_table(threshold_f1_rows))
+    print("Threshold Comparison (EER):")
+    print(_format_table(threshold_eer_rows))
+    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
+        best = best_by_profile[name]
+        print(
+            f"Best {name}: "
+            f"threshold={best.threshold}, f1={best.f1:.3f}, eer={best.eer:.3f}"
+        )
+
+
+def demo_basic_comparison():
+    """Demo: Compare two fingerprints from same device"""
+    print("=" * 70)
+    print("DEMO 1: Same Device, Minor Drift")
+    print("=" * 70)
+    
+    # Generate base fingerprint
+    base = create_base_fingerprint(12345)
+    
+    # Create slightly mutated version (low drift)
+    mutated = mutate(base, "low")
+    
+    # Decompose the comparison
+    breakdown = decompose_confidence(base, mutated, top_n=5)
+    
+    print(format_breakdown(breakdown))
+
+
+def demo_cross_browser():
+    """Demo: Same device, different browser"""
+    print("=" * 70)
+    print("DEMO 2: Same Device, High Drift (Cross-Browser Simulation)")
+    print("=" * 70)
+    
+    base = create_base_fingerprint(12345)
+    high_drift = mutate(base, "high")
+    
+    breakdown = decompose_confidence(base, high_drift, top_n=5)
+    
+    print(format_breakdown(breakdown))
+
+
+def demo_different_devices():
+    """Demo: Different devices"""
+    print("=" * 70)
+    print("DEMO 3: Different Devices")
+    print("=" * 70)
+    
+    device_a = create_base_fingerprint(11111)
+    device_b = create_base_fingerprint(22222)
+    
+    breakdown = decompose_confidence(device_a, device_b, top_n=5)
+    
+    print(format_breakdown(breakdown))
+
+
+def demo_evidence_richness():
+    """Demo: Evidence richness calculation"""
+    print("=" * 70)
+    print("DEMO 4: Evidence Richness")
+    print("=" * 70)
+    
+    rich_fp = create_base_fingerprint(12345)
+    
+    # Create sparse fingerprint (missing fields)
+    sparse_fp = {
+        "userAgent": rich_fp["userAgent"],
+        "platform": rich_fp["platform"],
+        "timezone": "America/New_York",
+    }
+    
+    rich_score = calculate_evidence_richness(rich_fp)
+    sparse_score = calculate_evidence_richness(sparse_fp)
+    
+    print(f"Rich fingerprint evidence score: {rich_score:.1f}/100")
+    print(f"Sparse fingerprint evidence score: {sparse_score:.1f}/100")
+    print()
+    
+    # Compare them
+    breakdown = decompose_confidence(rich_fp, sparse_fp, top_n=5)
+    print(format_breakdown(breakdown))
+
+
+def demo_attractor_risk():
+    """Demo: Attractor risk calculation"""
+    print("=" * 70)
+    print("DEMO 5: Attractor Risk Detection")
+    print("=" * 70)
+    
+    # Generic Windows + Chrome fingerprint (high attractor risk)
+    generic_fp = {
+        "platform": "Win32",
+        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
+        "deviceMemory": 8,
+        "hardwareConcurrency": 8,
+        "language": "en-US",
+        "timezone": "America/New_York",
+        "fonts": ["Arial", "Times New Roman"],  # Very few fonts
+    }
+    
+    # Unique fingerprint (low attractor risk)
+    unique_fp = create_base_fingerprint(99999)
+    
+    generic_risk = calculate_attractor_risk(generic_fp)
+    unique_risk = calculate_attractor_risk(unique_fp)
+    
+    print(f"Generic fingerprint attractor risk: {generic_risk:.1f}/100")
+    print(f"Unique fingerprint attractor risk: {unique_risk:.1f}/100")
+    print()
+
+
+def demo_dataset_analysis():
+    """Demo: Analyze a small dataset"""
+    print("=" * 70)
+    print("DEMO 6: Dataset Analysis")
+    print("=" * 70)
+    
+    # Generate small dataset
+    dataset = generate_dataset(size=5, sessions_per_device=2)
+    
+    # Compare first two sessions of same device
+    device_sessions = {}
+    for item in dataset:
+        device_sessions.setdefault(item.device_label, []).append(item)
+    
+    for device_id, sessions in list(device_sessions.items())[:2]:
+        if len(sessions) >= 2:
+            print(f"\n--- Device: {device_id[:12]}... ---")
+            print(f"Is Attractor: {sessions[0].is_attractor}")
+            
+            breakdown = decompose_confidence(
+                sessions[0].data,
+                sessions[1].data,
+                top_n=3
+            )
+            
+            print(f"Overall Confidence: {breakdown.overall_confidence:.1f}/100")
+            print(f"Device Similarity: {breakdown.device_similarity:.1f}/100")
+            print(f"Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
+            print(f"Attractor Risk: {breakdown.attractor_risk:.1f}/100")
+
+
+def main():
+    demo_basic_comparison()
+    print("\n\n")
+    demo_cross_browser()
+    print("\n\n")
+    demo_different_devices()
+    print("\n\n")
+    demo_evidence_richness()
+    print("\n\n")
+    demo_attractor_risk()
+    print("\n\n")
+    demo_dataset_analysis()
+    print("\n\n")
+    demo_large_dataset_comparison()
+
+if __name__ == "__main__":
+    main()
```
