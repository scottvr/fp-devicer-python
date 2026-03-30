# Commit: test profile/family ideas, and missingness-aware coverage
**Hash:** `3d41024655ae0b20c333259169ab48b614fb5479`  
**Date:** 2026-03-19  

## Editorial Rationale

>  In the previous comit, I had begun referring to your original confidence value as "legacy"; don't take it personally, it was just meant to make things clear that what I was doing was "new" and that the current canonical score was "legacy". In this change I cgrouped the various fields into "families":
```diff
+# Field families
+FAMILY_RENDERING = "rendering"
+FAMILY_STRUCTURAL = "structural"
+FAMILY_SOFTWARE = "software"
+FAMILY_LOCALE = "locale"
+FAMILY_MISC = "misc"
```

See [FAMILY GROUPING](#family-grouping) below.

---

## Technical Diffs
```diff
commit 3d41024655ae0b20c333259169ab48b614fb5479
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 08:50:32 2026 -0500

    test profile/family ideas, and missingness-aware coverage

diff --git a/src/devicer/benchmarks/demo_scoring_breakdown.py b/src/devicer/benchmarks/demo_scoring_breakdown.py
index 71f1734..ae33fb1 100644
--- a/src/devicer/benchmarks/demo_scoring_breakdown.py
+++ b/src/devicer/benchmarks/demo_scoring_breakdown.py
@@ -59,9 +59,15 @@ def _score_pair(
     same_device: bool,
 ) -> Dict[str, Any]:
     breakdown = decompose_confidence(left.data, right.data, top_n=0)
+    profile_scores = breakdown.profile_scores
     return {
         "legacyScore": float(calculate_confidence(left.data, right.data)),
-        "breakdownScore": float(breakdown.overall_confidence),
+        "breakdownScore": float(profile_scores.get("same_device", breakdown.overall_confidence)),
+        "same_instance": float(profile_scores.get("same_instance", breakdown.overall_confidence)),
+        "same_environment": float(profile_scores.get("same_environment", breakdown.overall_confidence)),
+        "same_device": float(profile_scores.get("same_device", breakdown.overall_confidence)),
+        "same_entity": float(profile_scores.get("same_entity", breakdown.overall_confidence)),
+        "evidenceRichness": float(breakdown.evidence_richness),
         "deviceSimilarity": float(breakdown.device_similarity),
         "entropyContribution": float(breakdown.entropy_contribution),
         "attractorRisk": float(breakdown.attractor_risk),
@@ -144,20 +150,41 @@ def demo_large_dataset_comparison():
 
     pairs = _generate_comparison_pairs(groups, iterations=2500)
 
-    legacy_results = calculate_metrics(_as_metric_inputs(pairs, "legacyScore"))
-    breakdown_results = calculate_metrics(_as_metric_inputs(pairs, "breakdownScore"))
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
 
-    threshold_rows: List[Dict[str, Any]] = []
-    for legacy_row, breakdown_row in zip(legacy_results, breakdown_results):
-        threshold_rows.append(
+        threshold_f1_rows.append(
             {
                 "threshold": legacy_row.threshold,
                 "legacy_f1": legacy_row.f1,
-                "breakdown_f1": breakdown_row.f1,
-                "f1_delta": breakdown_row.f1 - legacy_row.f1,
+                "instance_f1": instance_row.f1,
+                "environment_f1": env_row.f1,
+                "device_f1": device_row.f1,
+                "entity_f1": entity_row.f1,
+            }
+        )
+        threshold_eer_rows.append(
+            {
+                "threshold": legacy_row.threshold,
                 "legacy_eer": legacy_row.eer,
-                "breakdown_eer": breakdown_row.eer,
-                "eer_delta": legacy_row.eer - breakdown_row.eer,
+                "instance_eer": instance_row.eer,
+                "environment_eer": env_row.eer,
+                "device_eer": device_row.eer,
+                "entity_eer": entity_row.eer,
             }
         )
 
@@ -178,9 +205,11 @@ def demo_large_dataset_comparison():
                 "cohort": name,
                 "pairs": len(bucket),
                 "legacy_mean": _average([float(p["legacyScore"]) for p in bucket]),
-                "breakdown_mean": _average([float(p["breakdownScore"]) for p in bucket]),
-                "device_similarity_mean": _average([float(p["deviceSimilarity"]) for p in bucket]),
-                "entropy_mean": _average([float(p["entropyContribution"]) for p in bucket]),
+                "same_instance_mean": _average([float(p["same_instance"]) for p in bucket]),
+                "same_environment_mean": _average([float(p["same_environment"]) for p in bucket]),
+                "same_device_mean": _average([float(p["same_device"]) for p in bucket]),
+                "same_entity_mean": _average([float(p["same_entity"]) for p in bucket]),
+                "richness_mean": _average([float(p["evidenceRichness"]) for p in bucket]),
                 "attractor_risk_mean": _average([float(p["attractorRisk"]) for p in bucket]),
             }
         )
@@ -190,31 +219,35 @@ def demo_large_dataset_comparison():
             "cohort": "separation(same-diff)",
             "pairs": "-",
             "legacy_mean": cohort_rows[0]["legacy_mean"] - cohort_rows[1]["legacy_mean"],
-            "breakdown_mean": cohort_rows[0]["breakdown_mean"] - cohort_rows[1]["breakdown_mean"],
-            "device_similarity_mean": "-",
-            "entropy_mean": "-",
+            "same_instance_mean": cohort_rows[0]["same_instance_mean"] - cohort_rows[1]["same_instance_mean"],
+            "same_environment_mean": cohort_rows[0]["same_environment_mean"] - cohort_rows[1]["same_environment_mean"],
+            "same_device_mean": cohort_rows[0]["same_device_mean"] - cohort_rows[1]["same_device_mean"],
+            "same_entity_mean": cohort_rows[0]["same_entity_mean"] - cohort_rows[1]["same_entity_mean"],
+            "richness_mean": cohort_rows[0]["richness_mean"] - cohort_rows[1]["richness_mean"],
             "attractor_risk_mean": "-",
         }
     )
 
-    best_legacy = max(legacy_results, key=lambda item: item.f1)
-    best_breakdown = max(breakdown_results, key=lambda item: item.f1)
+    best_by_profile = {
+        name: max(rows, key=lambda item: item.f1)
+        for name, rows in metrics_by_score.items()
+    }
 
     print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
     print(f"Compared pairs: {len(pairs)}")
     print()
     print("Cohort Summary (means):")
     print(_format_table(cohort_rows))
-    print("Threshold Comparison (legacy vs scoring_breakdown overall):")
-    print(_format_table(threshold_rows))
-    print(
-        "Best legacy: "
-        f"threshold={best_legacy.threshold}, f1={best_legacy.f1:.3f}, eer={best_legacy.eer:.3f}"
-    )
-    print(
-        "Best breakdown: "
-        f"threshold={best_breakdown.threshold}, f1={best_breakdown.f1:.3f}, eer={best_breakdown.eer:.3f}"
-    )
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
 
 
 def demo_basic_comparison():
diff --git a/src/devicer/benchmarks/scoring_breakdown.py b/src/devicer/benchmarks/scoring_breakdown.py
index 877d772..108e400 100644
--- a/src/devicer/benchmarks/scoring_breakdown.py
+++ b/src/devicer/benchmarks/scoring_breakdown.py
@@ -2,7 +2,6 @@ from __future__ import annotations
 
 from dataclasses import dataclass, field
 from typing import Any, Dict, List, Optional, Set, Tuple
-import math
 
 
 @dataclass(frozen=True)
@@ -45,35 +44,98 @@ class ScoreBreakdown:
     total_fields_compared: int = 0
     structural_fields_compared: int = 0
     entropy_fields_compared: int = 0
+    one_side_missing_fields: int = 0
+    both_side_missing_fields: int = 0
+    profile_scores: Dict[str, float] = field(default_factory=dict)
+    family_similarities: Dict[str, float] = field(default_factory=dict)
+    family_coverages: Dict[str, float] = field(default_factory=dict)
+    family_effective_scores: Dict[str, float] = field(default_factory=dict)
```

## FAMILY GROUPING 

```diff
-# Field importance weights (sum to 1.0 across all fields)
+# Field importance weights for family-level scoring and explainability.
 FIELD_WEIGHTS = {
-    # High-entropy fields (strongest signals)
-    "canvas": 0.25,
-    "webgl": 0.20,
-    "audio": 0.10,
-    
-    # Structural/stable fields (medium-high signal)
-    "screen.width": 0.08,
-    "screen.height": 0.08,
-    "hardwareConcurrency": 0.05,
-    "deviceMemory": 0.04,
-    "timezone": 0.03,
-    
-    # Semi-stable fields (medium signal)
+    # Rendering entropy family
+    "canvas": 0.10,
+    "webgl": 0.0875,
+    "audio": 0.0625,
+
+    # Structural family
+    "screen.width": 0.10,
+    "screen.height": 0.10,
+    "screen.colorDepth": 0.04,
+    "screen.pixelDepth": 0.03,
+    "hardwareConcurrency": 0.06,
+    "deviceMemory": 0.05,
+
+    # Browser/software family
     "fonts": 0.06,
-    "plugins": 0.02,
-    "platform": 0.02,
-    "language": 0.01,
-    
-    # Volatile fields (lower signal, expect drift)
+    "plugins": 0.03,
+    "mimeTypes": 0.02,
+    "platform": 0.04,
     "userAgent": 0.03,
-    "appVersion": 0.01,
-    "highEntropyValues": 0.02,
-    
+    "appVersion": 0.02,
+    "highEntropyValues": 0.04,
+
+    # Locale/context family
+    "timezone": 0.03,
+    "language": 0.02,
+    "languages": 0.02,
+
     # Everything else gets minimal weight
-    "_default": 0.001,
+    "_default": 0.005,
+}
+
+# Field families
+FAMILY_RENDERING = "rendering"
+FAMILY_STRUCTURAL = "structural"
+FAMILY_SOFTWARE = "software"
+FAMILY_LOCALE = "locale"
+FAMILY_MISC = "misc"
+
+FAMILY_NAMES = [
+    FAMILY_RENDERING,
+    FAMILY_STRUCTURAL,
+    FAMILY_SOFTWARE,
+    FAMILY_LOCALE,
+    FAMILY_MISC,
+]
+
+FAMILY_COVERAGE_INFLUENCE = 0.30
+
+# Profile family weights. `richness` is a profile-level component.
+PROFILE_WEIGHTS = {
+    "same_instance": {
+        FAMILY_RENDERING: 0.35,
+        FAMILY_STRUCTURAL: 0.25,
+        FAMILY_SOFTWARE: 0.25,
+        FAMILY_LOCALE: 0.05,
+        FAMILY_MISC: 0.00,
+        "richness": 0.10,
+    },
+    "same_environment": {
+        FAMILY_RENDERING: 0.25,
+        FAMILY_STRUCTURAL: 0.30,
+        FAMILY_SOFTWARE: 0.25,
+        FAMILY_LOCALE: 0.10,
+        FAMILY_MISC: 0.00,
+        "richness": 0.10,
+    },
+    "same_device": {
+        FAMILY_RENDERING: 0.20,
+        FAMILY_STRUCTURAL: 0.35,
+        FAMILY_SOFTWARE: 0.20,
+        FAMILY_LOCALE: 0.05,
+        FAMILY_MISC: 0.00,
+        "richness": 0.20,
+    },
+    "same_entity": {
+        FAMILY_RENDERING: 0.10,
+        FAMILY_STRUCTURAL: 0.20,
+        FAMILY_SOFTWARE: 0.15,
+        FAMILY_LOCALE: 0.15,
+        FAMILY_MISC: 0.00,
+        "richness": 0.20,
+    },
 }
 
 # Stable fields that shouldn't change much
@@ -220,14 +282,57 @@ def _get_field_weight(field_name: str) -> float:
     return FIELD_WEIGHTS.get(field_name, FIELD_WEIGHTS["_default"])
 
 
+def _get_field_family(field_name: str) -> str:
+    """Map a field into a scoring family."""
+    if field_name in ENTROPY_FIELDS:
+        return FAMILY_RENDERING
+    if field_name.startswith("screen.") or field_name in {"hardwareConcurrency", "deviceMemory"}:
+        return FAMILY_STRUCTURAL
+    if field_name in {
+        "fonts",
+        "plugins",
+        "mimeTypes",
+        "platform",
+        "userAgent",
+        "appVersion",
+        "highEntropyValues",
+    }:
+        return FAMILY_SOFTWARE
+    if field_name in {"timezone", "language", "languages"}:
+        return FAMILY_LOCALE
+    return FAMILY_MISC
+
+
+def _weighted_mean(pairs: List[Tuple[float, float]]) -> float:
+    total_weight = sum(weight for _, weight in pairs)
+    if total_weight <= 0:
+        return 0.0
+    return sum(value * weight for value, weight in pairs) / total_weight
+
+
+def _coverage_damped_similarity(similarity: float, coverage: float) -> float:
+    alpha = max(0.0, min(1.0, FAMILY_COVERAGE_INFLUENCE))
+    return similarity * ((1.0 - alpha) + alpha * coverage)
+
+
+def _apply_gentle_attractor_penalty(score: float, attractor_risk: float, evidence_richness: float) -> float:
+    """
+    Dampen score only when risk is high and evidence is sparse.
+    Max penalty is intentionally small.
+    """
+    risk = max(0.0, min(100.0, attractor_risk)) / 100.0
+    richness = max(0.0, min(100.0, evidence_richness)) / 100.0
+    penalty_points = 8.0 * risk * (1.0 - richness)
+    return max(0.0, score - penalty_points)
+
+
 def _flatten_fingerprint(fp: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
     """Flatten nested fingerprint dict into dot-notation keys"""
     result = {}
     for key, value in fp.items():
         full_key = f"{prefix}.{key}" if prefix else key
         
-        if isinstance(value, dict) and key not in ["screen", "highEntropyValues"]:
-            # Don't flatten these specific nested dicts, treat as single fields
+        if isinstance(value, dict) and key != "highEntropyValues":
             result.update(_flatten_fingerprint(value, full_key))
         else:
             result[full_key] = value
@@ -237,34 +342,23 @@ def _flatten_fingerprint(fp: Dict[str, Any], prefix: str = "") -> Dict[str, Any]
 
 def calculate_evidence_richness(fp: Dict[str, Any]) -> float:
     """
-    Calculate how much data is present vs missing/sparse
+    Calculate weighted evidence coverage for a single fingerprint.
     Returns 0-100 score
     """
     flat = _flatten_fingerprint(fp)
-    
-    # Count present fields
-    present_count = 0
-    expected_count = 0
-    
-    # Core expected fields
-    core_fields = [
-        "userAgent", "platform", "timezone", "language",
-        "canvas", "webgl", "audio",
-        "screen", "fonts", "hardwareConcurrency", "deviceMemory"
-    ]
-    
-    for field in core_fields:
-        expected_count += 1
+
+    expected_fields = [field for field in FIELD_WEIGHTS.keys() if field != "_default"]
+    total_weight = sum(FIELD_WEIGHTS[field] for field in expected_fields)
+    if total_weight <= 0:
+        return 0.0
+
+    present_weight = 0.0
+    for field in expected_fields:
         val = flat.get(field)
         if val is not None and val != "" and val != []:
-            present_count += 1
-    
-    # Bonus for having high-entropy fields
-    entropy_present = sum(1 for f in ENTROPY_FIELDS if flat.get(f))
-    entropy_bonus = (entropy_present / len(ENTROPY_FIELDS)) * 20  # Up to 20 bonus points
-    
-    base_score = (present_count / expected_count) * 80 if expected_count > 0 else 0
-    return min(100.0, base_score + entropy_bonus)
+            present_weight += FIELD_WEIGHTS[field]
+
+    return max(0.0, min(100.0, (present_weight / total_weight) * 100.0))
 
 
 def calculate_attractor_risk(fp: Dict[str, Any], attractor_pool: Optional[List[Dict[str, Any]]] = None) -> float:
@@ -313,7 +407,8 @@ def decompose_confidence(
     fp1: Dict[str, Any],
     fp2: Dict[str, Any],
     attractor_pool: Optional[List[Dict[str, Any]]] = None,
-    top_n: int = 5
+    top_n: int = 5,
+    primary_profile: str = "same_device",
 ) -> ScoreBreakdown:
     """
     Decompose fingerprint comparison into multi-dimensional scores
@@ -330,61 +425,70 @@ def decompose_confidence(
     flat1 = _flatten_fingerprint(fp1)
     flat2 = _flatten_fingerprint(fp2)
     
-    # Get all fields from both fingerprints
-    all_fields = set(flat1.keys()) | set(flat2.keys())
-    
-    # Track missing fields
-    missing_fields = []
-    for field in all_fields:
-        if field not in flat1:
-            missing_fields.append(f"{field} (missing in fp1)")
-        elif field not in flat2:
-            missing_fields.append(f"{field} (missing in fp2)")
-    
-    # Compare each field
+    # Include known weighted fields so "both missing" is modeled as no evidence.
+    weighted_fields = set(FIELD_WEIGHTS.keys()) - {"_default"}
+    all_fields = (set(flat1.keys()) | set(flat2.keys()) | weighted_fields)
+
+    # Compare each field with missingness-awareness.
     matches: List[FieldMatch] = []
     disagreements: List[FieldMismatch] = []
-    
-    total_weight = 0.0
-    weighted_similarity = 0.0
-    
-    structural_weight = 0.0
-    structural_similarity = 0.0
-    
-    entropy_weight = 0.0
-    entropy_similarity = 0.0
-    
+
+    missing_fields: List[str] = []
     comparable_fields = 0
     matching_fields = 0
-    
-    for field in all_fields:
+
+    one_side_missing_fields = 0
+    both_side_missing_fields = 0
+
+    structural_fields_compared = 0
+    entropy_fields_compared = 0
+
+    total_weight = 0.0
+    comparable_weight = 0.0
+
+    family_total_weight = {name: 0.0 for name in FAMILY_NAMES}
+    family_comparable_weight = {name: 0.0 for name in FAMILY_NAMES}
+    family_weighted_similarity = {name: 0.0 for name in FAMILY_NAMES}
+
+    structural_pairs: List[Tuple[float, float]] = []
+    entropy_pairs: List[Tuple[float, float]] = []
+
+    for field in sorted(all_fields):
         val1 = flat1.get(field)
         val2 = flat2.get(field)
-        
-        # Skip if both missing
+
+        weight = _get_field_weight(field)
+        family = _get_field_family(field)
+        family_total_weight[family] += weight
+        total_weight += weight
+
         if val1 is None and val2 is None:
+            both_side_missing_fields += 1
             continue
-        
+
+        if val1 is None or val2 is None:
+            one_side_missing_fields += 1
+            if val1 is None:
+                missing_fields.append(f"{field} (missing in fp1)")
+            else:
+                missing_fields.append(f"{field} (missing in fp2)")
+            continue
+
         comparable_fields += 1
-        
-        # Calculate similarity
+        comparable_weight += weight
+        family_comparable_weight[family] += weight
+
         similarity, str1, str2 = _compare_field(val1, val2)
-        weight = _get_field_weight(field)
-        
-        total_weight += weight
-        weighted_similarity += similarity * weight
-        
-        # Track structural fields
+        family_weighted_similarity[family] += similarity * weight
+
         if field in STRUCTURAL_FIELDS:
-            structural_weight += weight
-            structural_similarity += similarity * weight
-        
-        # Track entropy fields
+            structural_fields_compared += 1
+            structural_pairs.append((similarity, weight))
+
         if field in ENTROPY_FIELDS:
-            entropy_weight += weight
-            entropy_similarity += similarity * weight
-        
-        # Track matches and disagreements
+            entropy_fields_compared += 1
+            entropy_pairs.append((similarity, weight))
+
         if similarity >= 90:
             matching_fields += 1
             matches.append(FieldMatch(
@@ -404,55 +508,86 @@ def decompose_confidence(
                 value_b=str2,
                 penalty=(100 - similarity) * weight
             ))
-    
-    # Calculate dimension scores
-    device_similarity = (weighted_similarity / total_weight) if total_weight > 0 else 0.0
-    
-    evidence_richness = (
-        calculate_evidence_richness(fp1) + calculate_evidence_richness(fp2)
-    ) / 2.0
-    
+
+    # Family similarity / coverage / effective score.
+    family_similarities: Dict[str, float] = {}
+    family_coverages: Dict[str, float] = {}
+    family_effective_scores: Dict[str, float] = {}
+
+    for family in FAMILY_NAMES:
+        total_family_weight = family_total_weight[family]
+        comparable_family_weight = family_comparable_weight[family]
+
+        similarity = (
+            family_weighted_similarity[family] / comparable_family_weight
+            if comparable_family_weight > 0
+            else 0.0
+        )
+        coverage = (
+            comparable_family_weight / total_family_weight
+            if total_family_weight > 0
+            else 0.0
+        )
+        effective = _coverage_damped_similarity(similarity, coverage)
+
+        family_similarities[family] = similarity
+        family_coverages[family] = coverage
+        family_effective_scores[family] = effective
+
+    # Missingness-aware evidence richness is based on comparable weight coverage.
+    evidence_richness = (comparable_weight / total_weight * 100.0) if total_weight > 0 else 0.0
+
     field_agreement = (matching_fields / comparable_fields * 100) if comparable_fields > 0 else 0.0
-    
-    structural_stability = (
-        (structural_similarity / structural_weight) if structural_weight > 0 else 100.0
-    )
-    
-    entropy_contribution = (
-        (entropy_similarity / entropy_weight) if entropy_weight > 0 else 0.0
+
+    structural_stability = _weighted_mean(structural_pairs)
+    entropy_contribution = _weighted_mean(entropy_pairs)
+
+    # Core fingerprint similarity as family-first aggregate (without richness modifier).
+    device_similarity = _weighted_mean(
+        [
+            (family_effective_scores[FAMILY_RENDERING], 0.30),
+            (family_effective_scores[FAMILY_STRUCTURAL], 0.45),
+            (family_effective_scores[FAMILY_SOFTWARE], 0.20),
+            (family_effective_scores[FAMILY_LOCALE], 0.05),
+        ]
     )
-    
+
     attractor_risk = (
         calculate_attractor_risk(fp1, attractor_pool) +
         calculate_attractor_risk(fp2, attractor_pool)
     ) / 2.0
-    
+
+    # Profile scores
+    profile_scores: Dict[str, float] = {}
+    for profile_name, weights in PROFILE_WEIGHTS.items():
+        pairs: List[Tuple[float, float]] = []
+        for family in FAMILY_NAMES:
+            family_weight = weights.get(family, 0.0)
+            if family_weight > 0:
+                pairs.append((family_effective_scores[family], family_weight))
+        richness_weight = weights.get("richness", 0.0)
+        if richness_weight > 0:
+            pairs.append((evidence_richness, richness_weight))
+
+        profile_raw = _weighted_mean(pairs)
+        profile_scores[profile_name] = _apply_gentle_attractor_penalty(
+            profile_raw,
+            attractor_risk,
+            evidence_richness,
+        )
+
+    if primary_profile not in profile_scores:
+        primary_profile = "same_device"
+    overall = profile_scores[primary_profile]
+
     # Sort matches by contribution (highest first)
     matches.sort(key=lambda m: m.contribution, reverse=True)
     top_matches = matches[:top_n]
-    
+
     # Sort disagreements by penalty (highest first)
     disagreements.sort(key=lambda d: d.penalty, reverse=True)
     top_disagreements = disagreements[:top_n]
-    
-    # Calculate overall confidence (weighted composite)
-    # Weight the dimensions:
-    # - Device similarity: 40%
-    # - Entropy contribution: 30%
-    # - Structural stability: 20%
-    # - Evidence richness: 10%
-    # - Penalty for attractor risk
-    overall = (
-        device_similarity * 0.40 +
-        entropy_contribution * 0.30 +
-        structural_stability * 0.20 +
-        evidence_richness * 0.10
-    )
-    
-    # Apply attractor risk penalty (reduce confidence if high risk)
-    attractor_penalty = attractor_risk * 0.15  # Up to 15 point penalty
-    overall = max(0.0, overall - attractor_penalty)
-    
+
     return ScoreBreakdown(
         device_similarity=device_similarity,
         evidence_richness=evidence_richness,
@@ -465,8 +600,14 @@ def decompose_confidence(
         missing_fields=missing_fields,
         overall_confidence=overall,
         total_fields_compared=comparable_fields,
-        structural_fields_compared=int(structural_weight > 0),
-        entropy_fields_compared=int(entropy_weight > 0),
+        structural_fields_compared=structural_fields_compared,
+        entropy_fields_compared=entropy_fields_compared,
+        one_side_missing_fields=one_side_missing_fields,
+        both_side_missing_fields=both_side_missing_fields,
+        profile_scores=profile_scores,
+        family_similarities=family_similarities,
+        family_coverages=family_coverages,
+        family_effective_scores=family_effective_scores,
     )
 
 
@@ -491,8 +632,31 @@ def format_breakdown(breakdown: ScoreBreakdown) -> str:
         f"  Structural Stability:  {breakdown.structural_stability:.1f}/100",
         f"  Entropy Contribution:  {breakdown.entropy_contribution:.1f}/100",
         f"  Attractor Risk:        {breakdown.attractor_risk:.1f}/100",
+        f"  Missing (one-side):    {breakdown.one_side_missing_fields}",
+        f"  Missing (both-side):   {breakdown.both_side_missing_fields}",
         "",
     ]
+
+    if breakdown.profile_scores:
+        lines.append("Profile Scores:")
+        for profile_name in ["same_instance", "same_environment", "same_device", "same_entity"]:
+            if profile_name in breakdown.profile_scores:
+                label = profile_name.replace("_", " ").title()
+                lines.append(f"  {label:17} {breakdown.profile_scores[profile_name]:.1f}/100")
+        lines.append("")
+
+    if breakdown.family_effective_scores:
+        lines.append("Family Scores (similarity / coverage / effective):")
+        for family in [FAMILY_RENDERING, FAMILY_STRUCTURAL, FAMILY_SOFTWARE, FAMILY_LOCALE, FAMILY_MISC]:
+            if family not in breakdown.family_effective_scores:
+                continue
+            similarity = breakdown.family_similarities.get(family, 0.0)
+            coverage = breakdown.family_coverages.get(family, 0.0)
+            effective = breakdown.family_effective_scores.get(family, 0.0)
+            lines.append(
+                f"  {family:10} {similarity:5.1f} / {coverage * 100:5.1f}% / {effective:5.1f}"
+            )
+        lines.append("")
     
     if breakdown.top_matches:
         lines.append("Top Contributing Matches:")
```
