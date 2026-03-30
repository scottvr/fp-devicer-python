# Commit: add the big pairing samples and table for apples-to-apples comparison of the existing confidence metric and the proposed additional scoring metrics
**Hash:** `619d4efe96d0dee3aefddec41a4cf09366d51caa`  
**Date:** 2026-03-19  

## Editorial Rationale

>  so this might be a little misleading, or at least make it feel like something is missing from being accounted for.  If you scroll to line 400 or so, you will see this also contains the initial commit of the scoring_breakdown itself which  stemmed from me just wanting to see what  role each of the fields in the two structures you "sum and diff" to get the confidence_score. This was in part to answer the question: "85% confidence meansa what? You are 85% confident they are the same? There is an 85% probbability that they are the same? What is this confidence value derived from?"  After decomposition and examination, this is the first iteration of the "wild-ass guess" constants I said were intuittive responses to benchmark numbers, and that they were in need of soe form of paramteter-tuning.

---

## Technical Diffs
```diff
commit 619d4efe96d0dee3aefddec41a4cf09366d51caa
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 08:18:03 2026 -0500

    add the big pairing samples and table for apples-to-apples comparison of the existing confidence metric and the proposed additional scoring metrics

diff --git a/src/devicer/benchmarks/demo_scoring_breakdown.py b/src/devicer/benchmarks/demo_scoring_breakdown.py
new file mode 100644
index 0000000..71f1734
--- /dev/null
+++ b/src/devicer/benchmarks/demo_scoring_breakdown.py
@@ -0,0 +1,376 @@
+"""
+Demo script for scoring_breakdown.py
+
+Shows how to use the multi-dimensional scoring system
+"""
+
+from __future__ import annotations
+
+from pathlib import Path
+import sys
+from typing import Any, Dict, List
+
+from data_generator import LabeledFingerprint, generate_dataset, mutate, create_base_fingerprint
+from metrics import ScoredPair, calculate_metrics
+from scoring_breakdown import (
+    decompose_confidence,
+    format_breakdown,
+    calculate_evidence_richness,
+    calculate_attractor_risk,
+)
+
+try:
+    from devicer.libs.confidence import calculate_confidence
+except ModuleNotFoundError:
+    # Allows running this script directly from `src/devicer/benchmarks/`.
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
+    return {
+        "legacyScore": float(calculate_confidence(left.data, right.data)),
+        "breakdownScore": float(breakdown.overall_confidence),
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
+    legacy_results = calculate_metrics(_as_metric_inputs(pairs, "legacyScore"))
+    breakdown_results = calculate_metrics(_as_metric_inputs(pairs, "breakdownScore"))
+
+    threshold_rows: List[Dict[str, Any]] = []
+    for legacy_row, breakdown_row in zip(legacy_results, breakdown_results):
+        threshold_rows.append(
+            {
+                "threshold": legacy_row.threshold,
+                "legacy_f1": legacy_row.f1,
+                "breakdown_f1": breakdown_row.f1,
+                "f1_delta": breakdown_row.f1 - legacy_row.f1,
+                "legacy_eer": legacy_row.eer,
+                "breakdown_eer": breakdown_row.eer,
+                "eer_delta": legacy_row.eer - breakdown_row.eer,
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
+                "breakdown_mean": _average([float(p["breakdownScore"]) for p in bucket]),
+                "device_similarity_mean": _average([float(p["deviceSimilarity"]) for p in bucket]),
+                "entropy_mean": _average([float(p["entropyContribution"]) for p in bucket]),
+                "attractor_risk_mean": _average([float(p["attractorRisk"]) for p in bucket]),
+            }
+        )
+
+    cohort_rows.append(
+        {
+            "cohort": "separation(same-diff)",
+            "pairs": "-",
+            "legacy_mean": cohort_rows[0]["legacy_mean"] - cohort_rows[1]["legacy_mean"],
+            "breakdown_mean": cohort_rows[0]["breakdown_mean"] - cohort_rows[1]["breakdown_mean"],
+            "device_similarity_mean": "-",
+            "entropy_mean": "-",
+            "attractor_risk_mean": "-",
+        }
+    )
+
+    best_legacy = max(legacy_results, key=lambda item: item.f1)
+    best_breakdown = max(breakdown_results, key=lambda item: item.f1)
+
+    print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
+    print(f"Compared pairs: {len(pairs)}")
+    print()
+    print("Cohort Summary (means):")
+    print(_format_table(cohort_rows))
+    print("Threshold Comparison (legacy vs scoring_breakdown overall):")
+    print(_format_table(threshold_rows))
+    print(
+        "Best legacy: "
+        f"threshold={best_legacy.threshold}, f1={best_legacy.f1:.3f}, eer={best_legacy.eer:.3f}"
+    )
+    print(
+        "Best breakdown: "
+        f"threshold={best_breakdown.threshold}, f1={best_breakdown.f1:.3f}, eer={best_breakdown.eer:.3f}"
+    )
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
+    """Run all demos"""
+    demo_basic_comparison()
+    print("\n\n")
+    
+    demo_cross_browser()
+    print("\n\n")
+    
+    demo_different_devices()
+    print("\n\n")
+    
+    demo_evidence_richness()
+    print("\n\n")
+    
+    demo_attractor_risk()
+    print("\n\n")
+    
+    demo_dataset_analysis()
+    print("\n\n")
+
+    demo_large_dataset_comparison()
+
+
+if __name__ == "__main__":
+    main()
diff --git a/src/devicer/benchmarks/scoring_breakdown.py b/src/devicer/benchmarks/scoring_breakdown.py
new file mode 100644
index 0000000..877d772
--- /dev/null
+++ b/src/devicer/benchmarks/scoring_breakdown.py
@@ -0,0 +1,525 @@
+from __future__ import annotations
+
+from dataclasses import dataclass, field
+from typing import Any, Dict, List, Optional, Set, Tuple
+import math
+
+
+@dataclass(frozen=True)
+class FieldMatch:
+    """Represents a contributing field similarity"""
+    field_name: str
+    similarity: float  # 0-100
+    weight: float  # contribution weight
+    value_a: str
+    value_b: str
+    contribution: float  # similarity * weight
+
+
+@dataclass(frozen=True)
+class FieldMismatch:
+    """Represents a disagreeing field"""
+    field_name: str
+    similarity: float  # 0-100
+    weight: float
+    value_a: str
+    value_b: str
+    penalty: float  # (100 - similarity) * weight
+
+
+@dataclass(frozen=True)
+class ScoreBreakdown:
+    """Multi-dimensional fingerprint comparison breakdown"""
+    device_similarity: float  # 0-100: Core fingerprint match strength
+    evidence_richness: float  # 0-100: How much data is present vs missing
+    field_agreement: float  # 0-100: Percentage of comparable fields that match
+    structural_stability: float  # 0-100: Agreement on stable fields (screen, hardware)
+    entropy_contribution: float  # 0-100: TLSH/high-entropy field contribution
+    attractor_risk: float  # 0-100: Likelihood this is a common/generic fingerprint
+    top_matches: List[FieldMatch]  # Top N contributing field similarities
+    top_disagreements: List[FieldMismatch]  # Top N disagreeing fields
+    missing_fields: List[str]  # Fields present in one but not the other
+    overall_confidence: float  # 0-100: Weighted composite (backward compat)
+    
+    # Additional metadata
+    total_fields_compared: int = 0
+    structural_fields_compared: int = 0
+    entropy_fields_compared: int = 0
+
+
+# Field importance weights (sum to 1.0 across all fields)
+FIELD_WEIGHTS = {
+    # High-entropy fields (strongest signals)
+    "canvas": 0.25,
+    "webgl": 0.20,
+    "audio": 0.10,
+    
+    # Structural/stable fields (medium-high signal)
+    "screen.width": 0.08,
+    "screen.height": 0.08,
+    "hardwareConcurrency": 0.05,
+    "deviceMemory": 0.04,
+    "timezone": 0.03,
+    
+    # Semi-stable fields (medium signal)
+    "fonts": 0.06,
+    "plugins": 0.02,
+    "platform": 0.02,
+    "language": 0.01,
+    
+    # Volatile fields (lower signal, expect drift)
+    "userAgent": 0.03,
+    "appVersion": 0.01,
+    "highEntropyValues": 0.02,
+    
+    # Everything else gets minimal weight
+    "_default": 0.001,
+}
+
+# Stable fields that shouldn't change much
+STRUCTURAL_FIELDS = {
+    "screen.width", "screen.height", "screen.colorDepth", "screen.pixelDepth",
+    "hardwareConcurrency", "deviceMemory", "platform", "timezone"
+}
+
+# High-entropy fields (canvas, webgl, audio)
+ENTROPY_FIELDS = {"canvas", "webgl", "audio"}
+
+# Attractor patterns (common generic fingerprints)
+ATTRACTOR_PATTERNS = [
+    {"platform": "Win32", "userAgent": "Chrome"},
+    {"platform": "MacIntel", "userAgent": "Safari"},
+    {"platform": "iPhone", "deviceMemory": 8},
+    {"platform": "Linux armv8l", "userAgent": "Chrome"},
+]
+
+
+def get_field_importance_weights() -> Dict[str, float]:
+    """Returns the field importance weight map"""
+    return FIELD_WEIGHTS.copy()
+
+
+def _get_nested_value(data: Dict[str, Any], path: str) -> Optional[Any]:
+    """Get value from nested dict using dot notation"""
+    keys = path.split(".")
+    current = data
+    for key in keys:
+        if not isinstance(current, dict):
+            return None
+        current = current.get(key)
+        if current is None:
+            return None
+    return current
+
+
+def _set_contains_nested(data: Dict[str, Any], field_set: Set[str]) -> bool:
+    """Check if any field from set exists in nested dict"""
+    for field_path in field_set:
+        if _get_nested_value(data, field_path) is not None:
+            return True
+    return False
+
+
+def _calculate_jaccard_similarity(set_a: Set[Any], set_b: Set[Any]) -> float:
+    """Calculate Jaccard similarity between two sets"""
+    if not set_a and not set_b:
+        return 100.0
+    if not set_a or not set_b:
+        return 0.0
+    intersection = len(set_a & set_b)
+    union = len(set_a | set_b)
+    return (intersection / union * 100.0) if union > 0 else 0.0
+
+
+def _to_hashable(value: Any) -> Any:
+    """Convert nested containers into hashable forms for set-based comparisons."""
+    if isinstance(value, dict):
+        return frozenset((k, _to_hashable(v)) for k, v in value.items())
+    if isinstance(value, list):
+        return tuple(_to_hashable(item) for item in value)
+    if isinstance(value, set):
+        return frozenset(_to_hashable(item) for item in value)
+    if isinstance(value, tuple):
+        return tuple(_to_hashable(item) for item in value)
+    try:
+        hash(value)
+    except TypeError:
+        return str(value)
+    return value
+
+
+def _calculate_string_similarity(str_a: str, str_b: str) -> float:
+    """Calculate similarity between two strings (simple char overlap)"""
+    if str_a == str_b:
+        return 100.0
+    if not str_a or not str_b:
+        return 0.0
+    
+    # Simple character-level Jaccard for strings
+    set_a = set(str_a.lower())
+    set_b = set(str_b.lower())
+    return _calculate_jaccard_similarity(set_a, set_b)
+
+
+def _compare_field(val_a: Any, val_b: Any) -> Tuple[float, str, str]:
+    """
+    Compare two field values, return (similarity 0-100, str_repr_a, str_repr_b)
+    """
+    # Exact match
+    if val_a == val_b:
+        return 100.0, str(val_a), str(val_b)
+    
+    # Both None/missing
+    if val_a is None and val_b is None:
+        return 100.0, "None", "None"
+    
+    # One missing
+    if val_a is None or val_b is None:
+        return 0.0, str(val_a), str(val_b)
+    
+    # Lists (fonts, plugins, etc.)
+    if isinstance(val_a, list) and isinstance(val_b, list):
+        set_a = {_to_hashable(item) for item in val_a}
+        set_b = {_to_hashable(item) for item in val_b}
+        similarity = _calculate_jaccard_similarity(set_a, set_b)
+        return similarity, f"[{len(val_a)} items]", f"[{len(val_b)} items]"
+    
+    # Dicts (screen, highEntropyValues, etc.)
+    if isinstance(val_a, dict) and isinstance(val_b, dict):
+        # Compare dict keys and values
+        keys_a, keys_b = set(val_a.keys()), set(val_b.keys())
+        common_keys = keys_a & keys_b
+        if not common_keys:
+            return 0.0, str(val_a), str(val_b)
+        
+        matches = sum(1 for k in common_keys if val_a[k] == val_b[k])
+        similarity = (matches / len(common_keys)) * 100.0
+        return similarity, str(val_a), str(val_b)
+    
+    # Numbers
+    if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
+        # Calculate percentage difference
+        avg = (abs(val_a) + abs(val_b)) / 2
+        if avg == 0:
+            return 100.0, str(val_a), str(val_b)
+        diff_pct = abs(val_a - val_b) / avg * 100
+        similarity = max(0, 100 - diff_pct)
+        return similarity, str(val_a), str(val_b)
+    
+    # Strings
+    if isinstance(val_a, str) and isinstance(val_b, str):
+        similarity = _calculate_string_similarity(val_a, val_b)
+        return similarity, val_a, val_b
+    
+    # Type mismatch
+    return 0.0, str(val_a), str(val_b)
+
+
+def _get_field_weight(field_name: str) -> float:
+    """Get weight for a field"""
+    return FIELD_WEIGHTS.get(field_name, FIELD_WEIGHTS["_default"])
+
+
+def _flatten_fingerprint(fp: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
+    """Flatten nested fingerprint dict into dot-notation keys"""
+    result = {}
+    for key, value in fp.items():
+        full_key = f"{prefix}.{key}" if prefix else key
+        
+        if isinstance(value, dict) and key not in ["screen", "highEntropyValues"]:
+            # Don't flatten these specific nested dicts, treat as single fields
+            result.update(_flatten_fingerprint(value, full_key))
+        else:
+            result[full_key] = value
+    
+    return result
+
+
+def calculate_evidence_richness(fp: Dict[str, Any]) -> float:
+    """
+    Calculate how much data is present vs missing/sparse
+    Returns 0-100 score
+    """
+    flat = _flatten_fingerprint(fp)
+    
+    # Count present fields
+    present_count = 0
+    expected_count = 0
+    
+    # Core expected fields
+    core_fields = [
+        "userAgent", "platform", "timezone", "language",
+        "canvas", "webgl", "audio",
+        "screen", "fonts", "hardwareConcurrency", "deviceMemory"
+    ]
+    
+    for field in core_fields:
+        expected_count += 1
+        val = flat.get(field)
+        if val is not None and val != "" and val != []:
+            present_count += 1
+    
+    # Bonus for having high-entropy fields
+    entropy_present = sum(1 for f in ENTROPY_FIELDS if flat.get(f))
+    entropy_bonus = (entropy_present / len(ENTROPY_FIELDS)) * 20  # Up to 20 bonus points
+    
+    base_score = (present_count / expected_count) * 80 if expected_count > 0 else 0
+    return min(100.0, base_score + entropy_bonus)
+
+
+def calculate_attractor_risk(fp: Dict[str, Any], attractor_pool: Optional[List[Dict[str, Any]]] = None) -> float:
+    """
+    Calculate likelihood this is a common/generic fingerprint
+    Returns 0-100 risk score (higher = more likely to be attractor)
+    """
+    risk_score = 0.0
+    
+    # Check against known attractor patterns
+    for pattern in ATTRACTOR_PATTERNS:
+        matches = all(
+            str(fp.get(key, "")).find(str(val)) >= 0
+            for key, val in pattern.items()
+        )
+        if matches:
+            risk_score += 30.0
+    
+    # Check for generic values
+    generic_markers = {
+        "platform": ["Win32", "MacIntel"],
+        "deviceMemory": [8, 16],
+        "hardwareConcurrency": [4, 8],
+        "language": ["en-US"],
+    }
+    
+    for field, generic_values in generic_markers.items():
+        if fp.get(field) in generic_values:
+            risk_score += 10.0
+    
+    # Low entropy in high-entropy fields is suspicious
+    fonts = fp.get("fonts", [])
+    if isinstance(fonts, list) and len(fonts) < 8:
+        risk_score += 15.0
+    
+    # If attractor pool provided, check similarity to pool
+    if attractor_pool:
+        # This would compare against known attractors
+        # For now, placeholder - could use clustering distance
+        pass
+    
+    return min(100.0, risk_score)
+
+
+def decompose_confidence(
+    fp1: Dict[str, Any],
+    fp2: Dict[str, Any],
+    attractor_pool: Optional[List[Dict[str, Any]]] = None,
+    top_n: int = 5
+) -> ScoreBreakdown:
+    """
+    Decompose fingerprint comparison into multi-dimensional scores
+    
+    Args:
+        fp1: First fingerprint
+        fp2: Second fingerprint
+        attractor_pool: Optional list of known attractor fingerprints
+        top_n: Number of top matches/disagreements to return
+    
+    Returns:
+        ScoreBreakdown with detailed comparison metrics
+    """
+    flat1 = _flatten_fingerprint(fp1)
+    flat2 = _flatten_fingerprint(fp2)
+    
+    # Get all fields from both fingerprints
+    all_fields = set(flat1.keys()) | set(flat2.keys())
+    
+    # Track missing fields
+    missing_fields = []
+    for field in all_fields:
+        if field not in flat1:
+            missing_fields.append(f"{field} (missing in fp1)")
+        elif field not in flat2:
+            missing_fields.append(f"{field} (missing in fp2)")
+    
+    # Compare each field
+    matches: List[FieldMatch] = []
+    disagreements: List[FieldMismatch] = []
+    
+    total_weight = 0.0
+    weighted_similarity = 0.0
+    
+    structural_weight = 0.0
+    structural_similarity = 0.0
+    
+    entropy_weight = 0.0
+    entropy_similarity = 0.0
+    
+    comparable_fields = 0
+    matching_fields = 0
+    
+    for field in all_fields:
+        val1 = flat1.get(field)
+        val2 = flat2.get(field)
+        
+        # Skip if both missing
+        if val1 is None and val2 is None:
+            continue
+        
+        comparable_fields += 1
+        
+        # Calculate similarity
+        similarity, str1, str2 = _compare_field(val1, val2)
+        weight = _get_field_weight(field)
+        
+        total_weight += weight
+        weighted_similarity += similarity * weight
+        
+        # Track structural fields
+        if field in STRUCTURAL_FIELDS:
+            structural_weight += weight
+            structural_similarity += similarity * weight
+        
+        # Track entropy fields
+        if field in ENTROPY_FIELDS:
+            entropy_weight += weight
+            entropy_similarity += similarity * weight
+        
+        # Track matches and disagreements
+        if similarity >= 90:
+            matching_fields += 1
+            matches.append(FieldMatch(
+                field_name=field,
+                similarity=similarity,
+                weight=weight,
+                value_a=str1,
+                value_b=str2,
+                contribution=similarity * weight
+            ))
+        elif similarity < 70:
+            disagreements.append(FieldMismatch(
+                field_name=field,
+                similarity=similarity,
+                weight=weight,
+                value_a=str1,
+                value_b=str2,
+                penalty=(100 - similarity) * weight
+            ))
+    
+    # Calculate dimension scores
+    device_similarity = (weighted_similarity / total_weight) if total_weight > 0 else 0.0
+    
+    evidence_richness = (
+        calculate_evidence_richness(fp1) + calculate_evidence_richness(fp2)
+    ) / 2.0
+    
+    field_agreement = (matching_fields / comparable_fields * 100) if comparable_fields > 0 else 0.0
+    
+    structural_stability = (
+        (structural_similarity / structural_weight) if structural_weight > 0 else 100.0
+    )
+    
+    entropy_contribution = (
+        (entropy_similarity / entropy_weight) if entropy_weight > 0 else 0.0
+    )
+    
+    attractor_risk = (
+        calculate_attractor_risk(fp1, attractor_pool) +
+        calculate_attractor_risk(fp2, attractor_pool)
+    ) / 2.0
+    
+    # Sort matches by contribution (highest first)
+    matches.sort(key=lambda m: m.contribution, reverse=True)
+    top_matches = matches[:top_n]
+    
+    # Sort disagreements by penalty (highest first)
+    disagreements.sort(key=lambda d: d.penalty, reverse=True)
+    top_disagreements = disagreements[:top_n]
+    
+    # Calculate overall confidence (weighted composite)
+    # Weight the dimensions:
+    # - Device similarity: 40%
+    # - Entropy contribution: 30%
+    # - Structural stability: 20%
+    # - Evidence richness: 10%
+    # - Penalty for attractor risk
+    overall = (
+        device_similarity * 0.40 +
+        entropy_contribution * 0.30 +
+        structural_stability * 0.20 +
+        evidence_richness * 0.10
+    )
+    
+    # Apply attractor risk penalty (reduce confidence if high risk)
+    attractor_penalty = attractor_risk * 0.15  # Up to 15 point penalty
+    overall = max(0.0, overall - attractor_penalty)
+    
+    return ScoreBreakdown(
+        device_similarity=device_similarity,
+        evidence_richness=evidence_richness,
+        field_agreement=field_agreement,
+        structural_stability=structural_stability,
+        entropy_contribution=entropy_contribution,
+        attractor_risk=attractor_risk,
+        top_matches=top_matches,
+        top_disagreements=top_disagreements,
+        missing_fields=missing_fields,
+        overall_confidence=overall,
+        total_fields_compared=comparable_fields,
+        structural_fields_compared=int(structural_weight > 0),
+        entropy_fields_compared=int(entropy_weight > 0),
+    )
+
+
+def format_breakdown(breakdown: ScoreBreakdown) -> str:
+    """
+    Format a ScoreBreakdown as human-readable text
+    
+    Args:
+        breakdown: The ScoreBreakdown to format
+    
+    Returns:
+        Formatted string representation
+    """
+    lines = [
+        "=== Score Breakdown ===",
+        f"Overall Confidence: {breakdown.overall_confidence:.1f}/100",
+        "",
+        "Dimensions:",
+        f"  Device Similarity:     {breakdown.device_similarity:.1f}/100",
+        f"  Evidence Richness:     {breakdown.evidence_richness:.1f}/100",
+        f"  Field Agreement:       {breakdown.field_agreement:.1f}% ({breakdown.total_fields_compared} fields)",
+        f"  Structural Stability:  {breakdown.structural_stability:.1f}/100",
+        f"  Entropy Contribution:  {breakdown.entropy_contribution:.1f}/100",
+        f"  Attractor Risk:        {breakdown.attractor_risk:.1f}/100",
+        "",
+    ]
+    
+    if breakdown.top_matches:
+        lines.append("Top Contributing Matches:")
+        for match in breakdown.top_matches:
+            lines.append(
+                f" {match.field_name}: {match.similarity:.0f}% "
+                f"(weight: {match.weight:.3f}, contribution: {match.contribution:.2f})"
+            )
+        lines.append("")
+    
+    if breakdown.top_disagreements:
+        lines.append("Top Disagreements:")
+        for dis in breakdown.top_disagreements:
+            lines.append(
+                f"{dis.field_name}: {dis.similarity:.0f}% "
+                f"(weight: {dis.weight:.3f}, penalty: {dis.penalty:.2f})"
+            )
+            lines.append(f"      A: {dis.value_a[:50]}")
+            lines.append(f"      B: {dis.value_b[:50]}")
+        lines.append("")
+    
+    if breakdown.missing_fields:
+        lines.append(f"Missing Fields ({len(breakdown.missing_fields)}):")
+        for mf in breakdown.missing_fields[:5]:  # Show first 5
+            lines.append(f"  - {mf}")
+        if len(breakdown.missing_fields) > 5:
+            lines.append(f"  ... and {len(breakdown.missing_fields) - 5} more")
+        lines.append("")
+    
+    return "\n".join(lines)
```
