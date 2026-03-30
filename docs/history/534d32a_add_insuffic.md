# Commit: add insufficiency_risk to breakdown model, narrow commonness semantics, explicit sparsity/insiffiency from low richness + missing families, trust adjustment combined both paths with profile-specific penalty strengths
**Hash:** `534d32a8300961c8ab76c7d0220ca703ebcacc06`  
**Timestamp:** 2026-03-19 11:31:40 -0500  

## Editorial Rationale

>  This is a pretty bit update to the display of the report, after grouping fields into families . It's also testing out  my own notions of what the difference between two datasets look like with soe specific contrived fingerprintes, such as those in the scenario_generator.py

---

## Technical Diffs
```diff
commit 534d32a8300961c8ab76c7d0220ca703ebcacc06
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 11:31:40 2026 -0500

    add insufficiency_risj to breakdown model, narrow commonness semantics, explicit sparsity/insiffiency from low richness + missing families, trust adjustment combined both paths with profile-specific penalty strengths

diff --git a/src/devicer/benchmarks/demo_scenario_generator.py b/src/devicer/benchmarks/demo_scenario_generator.py
index b15f89f..0b35092 100644
--- a/src/devicer/benchmarks/demo_scenario_generator.py
+++ b/src/devicer/benchmarks/demo_scenario_generator.py
@@ -6,6 +6,7 @@ Shows realistic adversarial scenarios and their characteristics
 
 from __future__ import annotations
 
+import copy
 from typing import Any, Dict, List
 
 from scenario_generator import (
@@ -14,6 +15,7 @@ from scenario_generator import (
     get_scenario_types,
     get_scenario_categories,
 )
+from data_generator import create_base_fingerprint
 from metrics import ScoredPair, calculate_metrics, calculate_true_eer
 from scoring_breakdown import decompose_confidence, format_breakdown
 
@@ -42,6 +44,31 @@ def _average(values: List[float]) -> float:
     return (sum(values) / len(values)) if values else 0.0
 
 
+def _band(value: float, low_to_med: float, med_to_high: float) -> str:
+    if value < low_to_med:
+        return "low"
+    if value < med_to_high:
+        return "med"
+    return "high"
+
+
+def _expected_band_set(spec: str) -> set[str]:
+    mapping = {
+        "low": "low",
+        "med": "med",
+        "medium": "med",
+        "high": "high",
+    }
+    tokens = [tok.strip().lower() for tok in spec.replace("-", "/").split("/") if tok.strip()]
+    normalized = {mapping.get(tok, tok) for tok in tokens}
+    return {tok for tok in normalized if tok in {"low", "med", "high"}}
+
+
+def _band_matches(spec: str, observed: str) -> bool:
+    expected = _expected_band_set(spec)
+    return observed in expected if expected else False
+
+
 def _as_metric_inputs(pairs: List[Dict[str, Any]], score_key: str) -> List[ScoredPair]:
     return [
         {
@@ -53,6 +80,161 @@ def _as_metric_inputs(pairs: List[Dict[str, Any]], score_key: str) -> List[Score
     ]
 
 
+def _sparsify_fingerprint(fp: Dict[str, Any]) -> Dict[str, Any]:
+    keep_fields = [
+        "userAgent",
+        "platform",
+        "timezone",
+        "language",
+        "languages",
+        "hardwareConcurrency",
+        "deviceMemory",
+        "screen",
+    ]
+    sparse: Dict[str, Any] = {}
+    for field in keep_fields:
+        if field in fp:
+            sparse[field] = copy.deepcopy(fp[field])
+    return sparse
+
+
+def demo_trust_semantics_truth_table():
+    """Demo: targeted semantic checks for trust/commonness layer."""
+    print("\n" + "=" * 70)
+    print("DEMO 9: Trust/Commonness Semantic Truth Table")
+    print("=" * 70)
+
+    # Fixed seeds keep this table stable across runs.
+    tor_pair = generate_scenario_pair("PrivacyHardening/TorBrowser", seed=91001)
+    corporate_pair = generate_scenario_pair("CommodityCollision/CorporateFleet", seed=91002)
+    minor_pair = generate_scenario_pair("BrowserDrift/Minor", seed=91003)
+    cross_pair = generate_scenario_pair("BrowserDrift/CrossBrowser", seed=91004)
+
+    base_a = create_base_fingerprint(13579)
+    base_b = create_base_fingerprint(24680)
+    sparse_a = _sparsify_fingerprint(base_a)
+    sparse_b = _sparsify_fingerprint(base_b)
+
+    cases = [
+        {
+            "case": "Tor vs Tor (different users)",
+            "fp1": tor_pair.fp1,
+            "fp2": tor_pair.fp2,
+            "expected_match": False,
+            "should_commonness": "high",
+            "should_distinctiveness": "low",
+            "should_insufficiency": "low",
+            "should_trust_adjustment": "high",
+        },
+        {
+            "case": "Corporate fleet (different users)",
+            "fp1": corporate_pair.fp1,
+            "fp2": corporate_pair.fp2,
+            "expected_match": False,
+            "should_commonness": "high",
+            "should_distinctiveness": "low",
+            "should_insufficiency": "low",
+            "should_trust_adjustment": "high",
+        },
+        {
+            "case": "Minor drift (same device)",
+            "fp1": minor_pair.fp1,
+            "fp2": minor_pair.fp2,
+            "expected_match": True,
+            "should_commonness": "low/med",
+            "should_distinctiveness": "med/high",
+            "should_insufficiency": "low",
+            "should_trust_adjustment": "low",
+        },
+        {
+            "case": "Cross-browser (same device)",
+            "fp1": cross_pair.fp1,
+            "fp2": cross_pair.fp2,
+            "expected_match": True,
+            "should_commonness": "low/med",
+            "should_distinctiveness": "med/high",
+            "should_insufficiency": "low/med",
+            "should_trust_adjustment": "low/med",
+        },
+        {
+            "case": "Sparse fp (same device)",
+            "fp1": base_a,
+            "fp2": sparse_a,
+            "expected_match": True,
+            "should_commonness": "med/high",
+            "should_distinctiveness": "low/med",
+            "should_insufficiency": "high",
+            "should_trust_adjustment": "med",
+        },
+        {
+            "case": "Sparse fp (different device)",
+            "fp1": sparse_a,
+            "fp2": sparse_b,
+            "expected_match": False,
+            "should_commonness": "high",
+            "should_distinctiveness": "low",
+            "should_insufficiency": "high",
+            "should_trust_adjustment": "med/high",
+        },
+    ]
+
+    rows: List[Dict[str, Any]] = []
+    for case in cases:
+        breakdown = decompose_confidence(case["fp1"], case["fp2"], top_n=0)
+        raw_same_device = breakdown.raw_profile_scores.get("same_device", breakdown.raw_similarity_score)
+        final_same_device = breakdown.profile_scores.get("same_device", breakdown.overall_confidence)
+        # Metric-aware bands:
+        # - commonness/distinctiveness are 0-100 style.
+        # - trust adjustment is in score points; values >20 are already substantial.
+        commonness_band = _band(breakdown.commonness_score, low_to_med=40.0, med_to_high=70.0)
+        distinctiveness_band = _band(breakdown.distinctiveness_score, low_to_med=40.0, med_to_high=70.0)
+        insufficiency_band = _band(breakdown.insufficiency_risk, low_to_med=35.0, med_to_high=65.0)
+        trust_band = _band(breakdown.trust_adjustment, low_to_med=8.0, med_to_high=20.0)
+
+        commonness_ok = _band_matches(case["should_commonness"], commonness_band)
+        distinctiveness_ok = _band_matches(case["should_distinctiveness"], distinctiveness_band)
+        insufficiency_ok = _band_matches(case["should_insufficiency"], insufficiency_band)
+        trust_ok = _band_matches(case["should_trust_adjustment"], trust_band)
+        pass_count = int(commonness_ok) + int(distinctiveness_ok) + int(insufficiency_ok) + int(trust_ok)
+
+        mismatches: List[str] = []
+        if not commonness_ok:
+            mismatches.append("commonness")
+        if not distinctiveness_ok:
+            mismatches.append("distinctiveness")
+        if not insufficiency_ok:
+            mismatches.append("insufficiency")
+        if not trust_ok:
+            mismatches.append("trust")
+
+        rows.append(
+            {
+                "case": case["case"],
+                "expected_match": case["expected_match"],
+                "raw_device_similarity": raw_same_device,
+                "commonness": breakdown.commonness_score,
+                "distinctiveness": breakdown.distinctiveness_score,
+                "collision_risk": breakdown.collision_risk,
+                "insufficiency_risk": breakdown.insufficiency_risk,
+                "trust_adjustment": breakdown.trust_adjustment,
+                "final_profile_score": final_same_device,
+                "obs_commonness_band": commonness_band,
+                "obs_distinctiveness_band": distinctiveness_band,
+                "obs_insufficiency_band": insufficiency_band,
+                "obs_trust_band": trust_band,
+                "should_commonness": case["should_commonness"],
+                "should_distinctiveness": case["should_distinctiveness"],
+                "should_insufficiency": case["should_insufficiency"],
+                "should_trust_adjustment": case["should_trust_adjustment"],
+                "semantic_check": "PASS" if pass_count == 4 else f"FAIL ({pass_count}/4)",
+                "semantic_mismatches": ",".join(mismatches) if mismatches else "-",
+                "policy_flags": ",".join(breakdown.policy_flags) if breakdown.policy_flags else "-",
+            }
+        )
+
+    print(_format_table(rows))
+
+
 def demo_single_scenarios():
     """Demo: Show each scenario type"""
     print("=" * 70)
@@ -79,11 +261,22 @@ def demo_single_scenarios():
         # Quick score
         breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=3)
         profile_scores = breakdown.profile_scores
+        raw_profile_scores = breakdown.raw_profile_scores
         print(f"Overall Confidence: {breakdown.overall_confidence:.1f}/100")
+        print(f"Raw Similarity: {breakdown.raw_similarity_score:.1f}/100")
+        print(f"Collision Risk: {breakdown.collision_risk:.1f}/100")
+        print(f"Insufficiency Risk: {breakdown.insufficiency_risk:.1f}/100")
+        print(f"Trust Adjustment: -{breakdown.trust_adjustment:.1f}")
+        print(f"Distinctiveness: {breakdown.distinctiveness_score:.1f}/100")
+        print(f"Commonness: {breakdown.commonness_score:.1f}/100")
         print(f"Same Instance: {profile_scores.get('same_instance', breakdown.overall_confidence):.1f}/100")
         print(f"Same Environment: {profile_scores.get('same_environment', breakdown.overall_confidence):.1f}/100")
         print(f"Same Device: {profile_scores.get('same_device', breakdown.overall_confidence):.1f}/100")
         print(f"Same Entity: {profile_scores.get('same_entity', breakdown.overall_confidence):.1f}/100")
+        print(
+            f"Raw Same Device: "
+            f"{raw_profile_scores.get('same_device', breakdown.raw_similarity_score):.1f}/100"
+        )
         print(f"Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
         print(f"Attractor Risk: {breakdown.attractor_risk:.1f}/100")
 
@@ -277,7 +470,13 @@ def demo_profiled_scenario_benchmark():
                 "difficulty": pair.metadata.difficulty,
                 "sameDevice": pair.metadata.expected_match,
                 "isAttractor": pair.metadata.difficulty == "extreme",
+                "raw_overall": breakdown.raw_similarity_score,
                 "overall": breakdown.overall_confidence,
+                "trust_adjustment": breakdown.trust_adjustment,
+                "collision_risk": breakdown.collision_risk,
+                "insufficiency_risk": breakdown.insufficiency_risk,
+                "distinctiveness": breakdown.distinctiveness_score,
+                "commonness": breakdown.commonness_score,
                 "same_instance": profile_scores.get("same_instance", breakdown.overall_confidence),
                 "same_environment": profile_scores.get("same_environment", breakdown.overall_confidence),
                 "same_device": profile_scores.get("same_device", breakdown.overall_confidence),
@@ -288,6 +487,7 @@ def demo_profiled_scenario_benchmark():
         )
 
     metrics_by_score = {
+        "raw_overall": calculate_metrics(_as_metric_inputs(scored_pairs, "raw_overall")),
         "overall": calculate_metrics(_as_metric_inputs(scored_pairs, "overall")),
         "same_instance": calculate_metrics(_as_metric_inputs(scored_pairs, "same_instance")),
         "same_environment": calculate_metrics(_as_metric_inputs(scored_pairs, "same_environment")),
@@ -307,6 +507,7 @@ def demo_profiled_scenario_benchmark():
         threshold_f1_rows.append(
             {
                 "threshold": overall_row.threshold,
+                "raw_overall_f1": metrics_by_score["raw_overall"][index].f1,
                 "overall_f1": overall_row.f1,
                 "instance_f1": instance_row.f1,
                 "environment_f1": environment_row.f1,
@@ -317,6 +518,7 @@ def demo_profiled_scenario_benchmark():
         threshold_gap_rows.append(
             {
                 "threshold": overall_row.threshold,
+                "raw_overall_gap": metrics_by_score["raw_overall"][index].far_frr_gap,
                 "overall_gap": overall_row.far_frr_gap,
                 "instance_gap": instance_row.far_frr_gap,
                 "environment_gap": environment_row.far_frr_gap,
@@ -337,7 +539,13 @@ def demo_profiled_scenario_benchmark():
                 "scenario_type": scenario_type,
                 "pairs": len(bucket),
                 "expected_match_pct": _average([100.0 if b["sameDevice"] else 0.0 for b in bucket]),
+                "raw_overall_mean": _average([float(b["raw_overall"]) for b in bucket]),
                 "overall_mean": _average([float(b["overall"]) for b in bucket]),
+                "trust_adjustment_mean": _average([float(b["trust_adjustment"]) for b in bucket]),
+                "collision_risk_mean": _average([float(b["collision_risk"]) for b in bucket]),
+                "insufficiency_risk_mean": _average([float(b["insufficiency_risk"]) for b in bucket]),
+                "distinctiveness_mean": _average([float(b["distinctiveness"]) for b in bucket]),
+                "commonness_mean": _average([float(b["commonness"]) for b in bucket]),
                 "instance_mean": _average([float(b["same_instance"]) for b in bucket]),
                 "environment_mean": _average([float(b["same_environment"]) for b in bucket]),
                 "device_mean": _average([float(b["same_device"]) for b in bucket]),
@@ -368,7 +576,7 @@ def demo_profiled_scenario_benchmark():
         for row in metrics_by_score["overall"]
     ]
     summary_rows = []
-    for name in ["overall", "same_instance", "same_environment", "same_device", "same_entity"]:
+    for name in ["raw_overall", "overall", "same_instance", "same_environment", "same_device", "same_entity"]:
         best = best_by_score[name]
         eer = true_eer_by_score[name]
         summary_rows.append(
@@ -405,6 +613,7 @@ def main():
     demo_dataset_generation()
     demo_custom_distribution()
     demo_profiled_scenario_benchmark()
+    demo_trust_semantics_truth_table()
     
     print("\n" + "=" * 70)
     print("All scenarios available:")
diff --git a/src/devicer/benchmarks/scoring_breakdown.py b/src/devicer/benchmarks/scoring_breakdown.py
index 8ecd055..2699592 100644
--- a/src/devicer/benchmarks/scoring_breakdown.py
+++ b/src/devicer/benchmarks/scoring_breakdown.py
@@ -30,6 +30,12 @@ class FieldMismatch:
 class ScoreBreakdown:
     """Multi-dimensional fingerprint comparison breakdown"""
     device_similarity: float  # 0-100: Core fingerprint match strength
+    raw_similarity_score: float  # 0-100: Profile score before trust/commonness adjustment
+    commonness_score: float  # 0-100: Higher means more generic/common fingerprint
+    distinctiveness_score: float  # 0-100: Higher means more unique fingerprint evidence
+    collision_risk: float  # 0-100: Estimated collision-prone risk used for trust adjustment
+    insufficiency_risk: float  # 0-100: Evidence insufficiency/sparsity risk
+    trust_adjustment: float  # points subtracted from raw similarity
     evidence_richness: float  # 0-100: How much data is present vs missing
     field_agreement: float  # 0-100: Percentage of comparable fields that match
     structural_stability: float  # 0-100: Agreement on stable fields (screen, hardware)
@@ -47,6 +53,8 @@ class ScoreBreakdown:
     one_side_missing_fields: int = 0
     both_side_missing_fields: int = 0
     profile_scores: Dict[str, float] = field(default_factory=dict)
+    raw_profile_scores: Dict[str, float] = field(default_factory=dict)
+    policy_flags: List[str] = field(default_factory=list)
     family_similarities: Dict[str, float] = field(default_factory=dict)
     family_coverages: Dict[str, float] = field(default_factory=dict)
     family_effective_scores: Dict[str, float] = field(default_factory=dict)
@@ -315,15 +323,256 @@ def _coverage_damped_similarity(similarity: float, coverage: float) -> float:
     return similarity * ((1.0 - alpha) + alpha * coverage)
 
 
-def _apply_gentle_attractor_penalty(score: float, attractor_risk: float, evidence_richness: float) -> float:
+def _clamp_0_100(value: float) -> float:
+    return max(0.0, min(100.0, value))
+
+
+def _clamp_01(value: float) -> float:
+    return max(0.0, min(1.0, value))
+
+
+def _compute_commonness_and_flags(
+    attractor_risk: float,
+    evidence_richness: float,
+    entropy_contribution: float,
+    family_similarities: Dict[str, float],
+    family_coverages: Dict[str, float],
+) -> Tuple[float, float, List[str]]:
+    """
+    Produce a pair-level commonness/distinctiveness estimate.
+
+    Commonness is intentionally narrow:
+    standardized/default/commodity profile likelihood, not generic uncertainty.
+    """
+    rendering_similarity = family_similarities.get(FAMILY_RENDERING, 0.0)
+    rendering_coverage = family_coverages.get(FAMILY_RENDERING, 0.0) * 100.0
+    software_similarity = family_similarities.get(FAMILY_SOFTWARE, 0.0)
+    locale_similarity = family_similarities.get(FAMILY_LOCALE, 0.0)
+
+    standardized_entropy = rendering_similarity * (rendering_coverage / 100.0)
+    software_locale_genericness = _clamp_0_100((software_similarity * 0.6) + (locale_similarity * 0.4))
+
+    commonness = (
+        0.70 * attractor_risk
+        + 0.20 * standardized_entropy
+        + 0.10 * software_locale_genericness
+    )
+
+    flags: List[str] = []
+    if attractor_risk >= 55:
+        flags.append("high_commonness_profile")
+    if standardized_entropy >= 82 and entropy_contribution >= 75:
+        flags.append("entropy_standardized")
+    if evidence_richness >= 75 and commonness >= 55:
+        flags.append("rich_but_common")
+    if software_locale_genericness >= 88:
+        flags.append("generic_software_locale")
+
+    if "high_commonness_profile" in flags and "entropy_standardized" in flags:
+        commonness += 10.0
+    if "rich_but_common" in flags:
+        commonness += 5.0
+
+    commonness = _clamp_0_100(commonness)
+    distinctiveness = 100.0 - commonness
+    return commonness, distinctiveness, flags
+
+
+def _compute_insufficiency_risk_and_flags(
+    evidence_richness: float,
+    family_coverages: Dict[str, float],
+) -> Tuple[float, List[str]]:
+    """
+    Compute 0-1 insufficiency/sparsity risk from missing coverage and low richness.
+    """
+    rendering_cov = _clamp_01(family_coverages.get(FAMILY_RENDERING, 0.0))
+    structural_cov = _clamp_01(family_coverages.get(FAMILY_STRUCTURAL, 0.0))
+    software_cov = _clamp_01(family_coverages.get(FAMILY_SOFTWARE, 0.0))
+    locale_cov = _clamp_01(family_coverages.get(FAMILY_LOCALE, 0.0))
+
+    richness_shortfall = _clamp_01((72.0 - evidence_richness) / 42.0)
+    structural_absence = _clamp_01((0.65 - structural_cov) / 0.65)
+    rendering_absence = _clamp_01((0.55 - rendering_cov) / 0.55)
+    software_absence = _clamp_01((0.55 - software_cov) / 0.55)
+    key_family_absence = (
+        0.50 * structural_absence
+        + 0.30 * rendering_absence
+        + 0.20 * software_absence
+    )
+    weak_context = _clamp_01((0.45 - locale_cov) / 0.45)
+
+    insufficiency_risk = (
+        0.60 * richness_shortfall
+        + 0.30 * key_family_absence
+        + 0.10 * weak_context
+    )
+
+    flags: List[str] = []
+    if evidence_richness < 65:
+        flags.append("insufficient_evidence")
+    if structural_cov < 0.55 or rendering_cov < 0.45 or software_cov < 0.45:
+        flags.append("missing_key_families")
+    if rendering_cov < 0.15:
+        flags.append("missing_rendering_family")
+    if software_cov < 0.35:
+        flags.append("thin_software_family")
+    if evidence_richness < 60 and (rendering_cov < 0.20 or software_cov < 0.35):
+        flags.append("sparse_observation")
+    if evidence_richness < 50 and rendering_cov < 0.15 and software_cov < 0.35:
+        flags.append("too_incomplete_for_identity")
+
+    if "missing_key_families" in flags:
+        insufficiency_risk += 0.10
+    if "missing_rendering_family" in flags:
+        insufficiency_risk += 0.10
+    if "thin_software_family" in flags:
+        insufficiency_risk += 0.05
+    if "sparse_observation" in flags:
+        insufficiency_risk += 0.12
+    if "too_incomplete_for_identity" in flags:
+        insufficiency_risk += 0.15
+
+    return _clamp_01(insufficiency_risk), flags
+
+
+def _compute_collision_risk(
+    commonness_score: float,
+    distinctiveness_score: float,
+    evidence_richness: float,
+    policy_flags: List[str],
+) -> float:
     """
-    Dampen score only when risk is high and evidence is sparse.
-    Max penalty is intentionally small.
+    Compute 0-1 collision risk used by trust adjustment and collision caps.
+
+    Design goals:
+    - commonness starts biting around 50 and becomes strong by ~75
+    - risk rises mostly in clearly collision-prone combinations
+    - policy flags can push risk into cap territory
     """
-    risk = max(0.0, min(100.0, attractor_risk)) / 100.0
-    richness = max(0.0, min(100.0, evidence_richness)) / 100.0
-    penalty_points = 8.0 * risk * (1.0 - richness)
-    return max(0.0, score - penalty_points)
+    # Steeper/nonlinear commonness ramp: 0 below 50, near 1 by 75.
+    commonness_linear = _clamp_01((commonness_score - 50.0) / 25.0)
+    commonness_factor = commonness_linear ** 2
+
+    # Low distinctiveness only starts to matter meaningfully below ~50.
+    low_distinctiveness_linear = _clamp_01((50.0 - distinctiveness_score) / 25.0)
+    low_distinctiveness = low_distinctiveness_linear ** 2
+
+    # Rich evidence should amplify risk only once richness is clearly high.
+    richness_factor = _clamp_01((evidence_richness - 70.0) / 20.0)
+
+    collision_risk = (
+        0.45 * commonness_factor
+        + 0.35 * low_distinctiveness
+        + 0.20 * richness_factor
+    )
+
+    if "high_commonness_profile" in policy_flags:
+        collision_risk += 0.15
+    if "entropy_standardized" in policy_flags:
+        collision_risk += 0.20
+    if "rich_but_common" in policy_flags:
+        collision_risk += 0.15
+
+    return _clamp_01(collision_risk)
+
+
+def _apply_trust_adjustment_to_profiles(
+    raw_profile_scores: Dict[str, float],
+    collision_risk: float,
+    insufficiency_risk: float,
+) -> Dict[str, float]:
+    """
+    Convert raw profile similarity into trust-adjusted identity confidence.
+    """
+    adjusted_scores: Dict[str, float] = {}
+    collision = _clamp_01(collision_risk)
+    insufficiency = _clamp_01(insufficiency_risk)
+
+    # Broader profiles should be more conservative in collision-prone classes.
+    profile_collision_penalty_strength = {
+        "same_instance": 0.28,
+        "same_environment": 0.34,
+        "same_device": 0.42,
+        "same_entity": 0.55,
+    }
+    profile_insufficiency_penalty_strength = {
+        "same_instance": 0.36,
+        "same_environment": 0.46,
+        "same_device": 0.58,
+        "same_entity": 0.72,
+    }
+    profile_collision_threshold = {
+        "same_instance": 0.90,
+        "same_environment": 0.82,
+        "same_device": 0.74,
+        "same_entity": 0.65,
+    }
+    profile_collision_cap = {
+        "same_instance": 84.0,
+        "same_environment": 78.0,
+        "same_device": 72.0,
+        "same_entity": 64.0,
+    }
+    profile_hard_collision_cap = {
+        "same_instance": 78.0,
+        "same_environment": 72.0,
+        "same_device": 66.0,
+        "same_entity": 58.0,
+    }
+    profile_insufficiency_threshold = {
+        "same_instance": 0.70,
+        "same_environment": 0.62,
+        "same_device": 0.55,
+        "same_entity": 0.50,
+    }
+    profile_insufficiency_cap = {
+        "same_instance": 82.0,
+        "same_environment": 74.0,
+        "same_device": 68.0,
+        "same_entity": 60.0,
+    }
+    profile_hard_insufficiency_cap = {
+        "same_instance": 74.0,
+        "same_environment": 68.0,
+        "same_device": 62.0,
+        "same_entity": 56.0,
+    }
+    profile_dual_risk_cap = {
+        "same_instance": 72.0,
+        "same_environment": 66.0,
+        "same_device": 60.0,
+        "same_entity": 54.0,
+    }
+
+    for profile_name, raw_score in raw_profile_scores.items():
+        collision_strength = profile_collision_penalty_strength.get(profile_name, 0.42)
+        insufficiency_strength = profile_insufficiency_penalty_strength.get(profile_name, 0.58)
+
+        penalty_fraction = (
+            collision_strength * collision
+            + insufficiency_strength * insufficiency
+        )
+        penalty_fraction = _clamp_01(min(0.92, penalty_fraction))
+        adjusted = raw_score * (1.0 - penalty_fraction)
+
+        collision_threshold = profile_collision_threshold.get(profile_name, 0.75)
+        if collision >= collision_threshold:
+            adjusted = min(adjusted, profile_collision_cap.get(profile_name, 72.0))
+        if collision >= 0.90:
+            adjusted = min(adjusted, profile_hard_collision_cap.get(profile_name, 66.0))
+
+        insufficiency_threshold = profile_insufficiency_threshold.get(profile_name, 0.55)
+        if insufficiency >= insufficiency_threshold:
+            adjusted = min(adjusted, profile_insufficiency_cap.get(profile_name, 68.0))
+        if insufficiency >= 0.85:
+            adjusted = min(adjusted, profile_hard_insufficiency_cap.get(profile_name, 62.0))
+
+        if collision >= 0.70 and insufficiency >= 0.60:
+            adjusted = min(adjusted, profile_dual_risk_cap.get(profile_name, 60.0))
+
+        adjusted_scores[profile_name] = _clamp_0_100(adjusted)
+
+    return adjusted_scores
 
 
 def _flatten_fingerprint(fp: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
@@ -557,8 +806,8 @@ def decompose_confidence(
         calculate_attractor_risk(fp2, attractor_pool)
     ) / 2.0
 
-    # Profile scores
-    profile_scores: Dict[str, float] = {}
+    # Raw profile scores (before trust/commonness adjustment)
+    raw_profile_scores: Dict[str, float] = {}
     for profile_name, weights in PROFILE_WEIGHTS.items():
         pairs: List[Tuple[float, float]] = []
         for family in FAMILY_NAMES:
@@ -569,16 +818,41 @@ def decompose_confidence(
         if richness_weight > 0:
             pairs.append((evidence_richness, richness_weight))
 
-        profile_raw = _weighted_mean(pairs)
-        profile_scores[profile_name] = _apply_gentle_attractor_penalty(
-            profile_raw,
-            attractor_risk,
-            evidence_richness,
-        )
+        raw_profile_scores[profile_name] = _weighted_mean(pairs)
+
+    commonness_score, distinctiveness_score, commonness_flags = _compute_commonness_and_flags(
+        attractor_risk=attractor_risk,
+        evidence_richness=evidence_richness,
+        entropy_contribution=entropy_contribution,
+        family_similarities=family_similarities,
+        family_coverages=family_coverages,
+    )
+    insufficiency_risk, insufficiency_flags = _compute_insufficiency_risk_and_flags(
+        evidence_richness=evidence_richness,
+        family_coverages=family_coverages,
+    )
+    policy_flags: List[str] = []
+    for flag in [*commonness_flags, *insufficiency_flags]:
+        if flag not in policy_flags:
+            policy_flags.append(flag)
+
+    collision_risk = _compute_collision_risk(
+        commonness_score=commonness_score,
+        distinctiveness_score=distinctiveness_score,
+        evidence_richness=evidence_richness,
+        policy_flags=commonness_flags,
+    )
+    profile_scores = _apply_trust_adjustment_to_profiles(
+        raw_profile_scores=raw_profile_scores,
+        collision_risk=collision_risk,
+        insufficiency_risk=insufficiency_risk,
+    )
 
     if primary_profile not in profile_scores:
         primary_profile = "same_device"
     overall = profile_scores[primary_profile]
+    raw_primary = raw_profile_scores.get(primary_profile, overall)
+    trust_adjustment = max(0.0, raw_primary - overall)
 
     # Sort matches by contribution (highest first)
     matches.sort(key=lambda m: m.contribution, reverse=True)
@@ -590,6 +864,12 @@ def decompose_confidence(
 
     return ScoreBreakdown(
         device_similarity=device_similarity,
+        raw_similarity_score=raw_primary,
+        commonness_score=commonness_score,
+        distinctiveness_score=distinctiveness_score,
+        collision_risk=collision_risk * 100.0,
+        insufficiency_risk=insufficiency_risk * 100.0,
+        trust_adjustment=trust_adjustment,
         evidence_richness=evidence_richness,
         field_agreement=field_agreement,
         structural_stability=structural_stability,
@@ -605,6 +885,8 @@ def decompose_confidence(
         one_side_missing_fields=one_side_missing_fields,
         both_side_missing_fields=both_side_missing_fields,
         profile_scores=profile_scores,
+        raw_profile_scores=raw_profile_scores,
+        policy_flags=policy_flags,
         family_similarities=family_similarities,
         family_coverages=family_coverages,
         family_effective_scores=family_effective_scores,
@@ -625,6 +907,15 @@ def format_breakdown(breakdown: ScoreBreakdown) -> str:
         "=== Score Breakdown ===",
         f"Overall Confidence: {breakdown.overall_confidence:.1f}/100",
         "",
+        "Identity Layer:",
+        f"  Raw Similarity:        {breakdown.raw_similarity_score:.1f}/100",
+        f"  Commonness Score:      {breakdown.commonness_score:.1f}/100",
+        f"  Distinctiveness Score: {breakdown.distinctiveness_score:.1f}/100",
+        f"  Collision Risk:        {breakdown.collision_risk:.1f}/100",
+        f"  Insufficiency Risk:    {breakdown.insufficiency_risk:.1f}/100",
+        f"  Trust-Adjusted:        {breakdown.overall_confidence:.1f}/100",
+        f"  Trust Adjustment:      -{breakdown.trust_adjustment:.1f}",
+        "",
         "Dimensions:",
         f"  Device Similarity:     {breakdown.device_similarity:.1f}/100",
         f"  Evidence Richness:     {breakdown.evidence_richness:.1f}/100",
@@ -642,7 +933,15 @@ def format_breakdown(breakdown: ScoreBreakdown) -> str:
         for profile_name in ["same_instance", "same_environment", "same_device", "same_entity"]:
             if profile_name in breakdown.profile_scores:
                 label = profile_name.replace("_", " ").title()
-                lines.append(f"  {label:17} {breakdown.profile_scores[profile_name]:.1f}/100")
+                raw_value = breakdown.raw_profile_scores.get(profile_name, breakdown.profile_scores[profile_name])
+                adjusted_value = breakdown.profile_scores[profile_name]
+                lines.append(f"  {label:17} raw={raw_value:5.1f} adjusted={adjusted_value:5.1f}")
+        lines.append("")
+
+    if breakdown.policy_flags:
+        lines.append("Trust Policy Flags:")
+        for flag in breakdown.policy_flags:
+            lines.append(f"  - {flag}")
         lines.append("")
 
     if breakdown.family_effective_scores:
@@ -739,9 +1038,17 @@ def _score_pair(
 ) -> Dict[str, Any]:
     breakdown = decompose_confidence(left.data, right.data, top_n=0)
     profile_scores = breakdown.profile_scores
+    raw_profile_scores = breakdown.raw_profile_scores
     return {
         "legacyScore": float(calculate_confidence(left.data, right.data)),
         "breakdownScore": float(profile_scores.get("same_device", breakdown.overall_confidence)),
+        "raw_breakdownScore": float(raw_profile_scores.get("same_device", breakdown.raw_similarity_score)),
+        "raw_overall": float(breakdown.raw_similarity_score),
+        "trust_adjustment": float(breakdown.trust_adjustment),
+        "collision_risk": float(breakdown.collision_risk),
+        "insufficiency_risk": float(breakdown.insufficiency_risk),
+        "commonness": float(breakdown.commonness_score),
+        "distinctiveness": float(breakdown.distinctiveness_score),
         "same_instance": float(profile_scores.get("same_instance", breakdown.overall_confidence)),
         "same_environment": float(profile_scores.get("same_environment", breakdown.overall_confidence)),
         "same_device": float(profile_scores.get("same_device", breakdown.overall_confidence)),
@@ -831,6 +1138,7 @@ def demo_large_dataset_comparison():
 
     metrics_by_score = {
         "legacy": calculate_metrics(_as_metric_inputs(pairs, "legacyScore")),
+        "raw_same_device": calculate_metrics(_as_metric_inputs(pairs, "raw_breakdownScore")),
         "same_instance": calculate_metrics(_as_metric_inputs(pairs, "same_instance")),
         "same_environment": calculate_metrics(_as_metric_inputs(pairs, "same_environment")),
         "same_device": calculate_metrics(_as_metric_inputs(pairs, "same_device")),
@@ -850,6 +1158,7 @@ def demo_large_dataset_comparison():
             {
                 "threshold": legacy_row.threshold,
                 "legacy_f1": legacy_row.f1,
+                "raw_device_f1": metrics_by_score["raw_same_device"][index].f1,
                 "instance_f1": instance_row.f1,
                 "environment_f1": env_row.f1,
                 "device_f1": device_row.f1,
@@ -860,6 +1169,7 @@ def demo_large_dataset_comparison():
             {
                 "threshold": legacy_row.threshold,
                 "legacy_gap": legacy_row.far_frr_gap,
+                "raw_device_gap": metrics_by_score["raw_same_device"][index].far_frr_gap,
                 "instance_gap": instance_row.far_frr_gap,
                 "environment_gap": env_row.far_frr_gap,
                 "device_gap": device_row.far_frr_gap,
@@ -884,10 +1194,16 @@ def demo_large_dataset_comparison():
                 "cohort": name,
                 "pairs": len(bucket),
                 "legacy_mean": _average([float(p["legacyScore"]) for p in bucket]),
+                "raw_device_mean": _average([float(p["raw_breakdownScore"]) for p in bucket]),
                 "same_instance_mean": _average([float(p["same_instance"]) for p in bucket]),
                 "same_environment_mean": _average([float(p["same_environment"]) for p in bucket]),
                 "same_device_mean": _average([float(p["same_device"]) for p in bucket]),
                 "same_entity_mean": _average([float(p["same_entity"]) for p in bucket]),
+                "commonness_mean": _average([float(p["commonness"]) for p in bucket]),
+                "distinctiveness_mean": _average([float(p["distinctiveness"]) for p in bucket]),
+                "collision_risk_mean": _average([float(p["collision_risk"]) for p in bucket]),
+                "insufficiency_risk_mean": _average([float(p["insufficiency_risk"]) for p in bucket]),
+                "trust_adjustment_mean": _average([float(p["trust_adjustment"]) for p in bucket]),
                 "richness_mean": _average([float(p["evidenceRichness"]) for p in bucket]),
                 "attractor_risk_mean": _average([float(p["attractorRisk"]) for p in bucket]),
             }
@@ -898,10 +1214,16 @@ def demo_large_dataset_comparison():
             "cohort": "separation(same-diff)",
             "pairs": "-",
             "legacy_mean": cohort_rows[0]["legacy_mean"] - cohort_rows[1]["legacy_mean"],
+            "raw_device_mean": cohort_rows[0]["raw_device_mean"] - cohort_rows[1]["raw_device_mean"],
             "same_instance_mean": cohort_rows[0]["same_instance_mean"] - cohort_rows[1]["same_instance_mean"],
             "same_environment_mean": cohort_rows[0]["same_environment_mean"] - cohort_rows[1]["same_environment_mean"],
             "same_device_mean": cohort_rows[0]["same_device_mean"] - cohort_rows[1]["same_device_mean"],
             "same_entity_mean": cohort_rows[0]["same_entity_mean"] - cohort_rows[1]["same_entity_mean"],
+            "commonness_mean": cohort_rows[0]["commonness_mean"] - cohort_rows[1]["commonness_mean"],
+            "distinctiveness_mean": cohort_rows[0]["distinctiveness_mean"] - cohort_rows[1]["distinctiveness_mean"],
+            "collision_risk_mean": cohort_rows[0]["collision_risk_mean"] - cohort_rows[1]["collision_risk_mean"],
+            "insufficiency_risk_mean": cohort_rows[0]["insufficiency_risk_mean"] - cohort_rows[1]["insufficiency_risk_mean"],
+            "trust_adjustment_mean": cohort_rows[0]["trust_adjustment_mean"] - cohort_rows[1]["trust_adjustment_mean"],
             "richness_mean": cohort_rows[0]["richness_mean"] - cohort_rows[1]["richness_mean"],
             "attractor_risk_mean": "-",
         }
@@ -928,7 +1250,7 @@ def demo_large_dataset_comparison():
         for row in metrics_by_score["legacy"]
     ]
     summary_rows = []
-    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
+    for name in ["legacy", "raw_same_device", "same_instance", "same_environment", "same_device", "same_entity"]:
         best = best_by_profile[name]
         eer = true_eer_by_profile[name]
         summary_rows.append(
```


---

### Navigation
[← Previous (Commit 26)](cdc9e0f_commit_accur.md) | [Back to Index](./index.md) | [Next (Commit 28) →](737a534_add_uncertai.md)
