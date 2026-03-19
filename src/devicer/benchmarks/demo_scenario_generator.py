"""
Demo script for scenario_generator.py

Shows realistic adversarial scenarios and their characteristics
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from scenario_generator import (
    generate_scenario_pair,
    generate_scenario_dataset,
    get_scenario_types,
    get_scenario_categories,
)
from data_generator import create_base_fingerprint
from metrics import ScoredPair, calculate_metrics, calculate_true_eer
from scoring_breakdown import decompose_confidence, format_breakdown


def _format_table(data: List[Dict[str, Any]]) -> str:
    if not data:
        return "(empty)\n"

    keys = list(data[0].keys())
    rows: List[List[str]] = []
    for row in data:
        values: List[str] = []
        for key in keys:
            val = row.get(key)
            values.append(f"{val:.3f}" if isinstance(val, float) else str(val))
        rows.append(values)

    col_widths = [max(len(keys[i]), *(len(row[i]) for row in rows)) for i in range(len(keys))]
    sep = "-+-".join("-" * width for width in col_widths)
    header = " | ".join(keys[i].ljust(col_widths[i]) for i in range(len(keys)))
    body = "\n".join(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(keys))) for row in rows)
    return f"{header}\n{sep}\n{body}\n"


def _average(values: List[float]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _band(value: float, low_to_med: float, med_to_high: float) -> str:
    if value < low_to_med:
        return "low"
    if value < med_to_high:
        return "med"
    return "high"


def _expected_band_set(spec: str) -> set[str]:
    mapping = {
        "low": "low",
        "med": "med",
        "medium": "med",
        "high": "high",
    }
    tokens = [tok.strip().lower() for tok in spec.replace("-", "/").split("/") if tok.strip()]
    normalized = {mapping.get(tok, tok) for tok in tokens}
    return {tok for tok in normalized if tok in {"low", "med", "high"}}


def _band_matches(spec: str, observed: str) -> bool:
    expected = _expected_band_set(spec)
    return observed in expected if expected else False


def _as_metric_inputs(pairs: List[Dict[str, Any]], score_key: str) -> List[ScoredPair]:
    return [
        {
            "score": float(pair[score_key]),
            "sameDevice": bool(pair["sameDevice"]),
            "isAttractor": bool(pair["isAttractor"]),
        }
        for pair in pairs
    ]


def _sparsify_fingerprint(fp: Dict[str, Any]) -> Dict[str, Any]:
    keep_fields = [
        "userAgent",
        "platform",
        "timezone",
        "language",
        "languages",
        "hardwareConcurrency",
        "deviceMemory",
        "screen",
    ]
    sparse: Dict[str, Any] = {}
    for field in keep_fields:
        if field in fp:
            sparse[field] = copy.deepcopy(fp[field])
    return sparse


def demo_trust_semantics_truth_table():
    """Demo: targeted semantic checks for trust/commonness layer."""
    print("\n" + "=" * 70)
    print("DEMO 9: Trust/Commonness Semantic Truth Table")
    print("=" * 70)

    # Fixed seeds keep this table stable across runs.
    tor_pair = generate_scenario_pair("PrivacyHardening/TorBrowser", seed=91001)
    corporate_pair = generate_scenario_pair("CommodityCollision/CorporateFleet", seed=91002)
    minor_pair = generate_scenario_pair("BrowserDrift/Minor", seed=91003)
    cross_pair = generate_scenario_pair("BrowserDrift/CrossBrowser", seed=91004)

    base_a = create_base_fingerprint(13579)
    base_b = create_base_fingerprint(24680)
    sparse_a = _sparsify_fingerprint(base_a)
    sparse_b = _sparsify_fingerprint(base_b)

    cases = [
        {
            "case": "Tor vs Tor (different users)",
            "fp1": tor_pair.fp1,
            "fp2": tor_pair.fp2,
            "expected_match": False,
            "should_commonness": "high",
            "should_distinctiveness": "low",
            "should_insufficiency": "low",
            "should_trust_adjustment": "high",
        },
        {
            "case": "Corporate fleet (different users)",
            "fp1": corporate_pair.fp1,
            "fp2": corporate_pair.fp2,
            "expected_match": False,
            "should_commonness": "high",
            "should_distinctiveness": "low",
            "should_insufficiency": "low",
            "should_trust_adjustment": "high",
        },
        {
            "case": "Minor drift (same device)",
            "fp1": minor_pair.fp1,
            "fp2": minor_pair.fp2,
            "expected_match": True,
            "should_commonness": "low/med",
            "should_distinctiveness": "med/high",
            "should_insufficiency": "low",
            "should_trust_adjustment": "low",
        },
        {
            "case": "Cross-browser (same device)",
            "fp1": cross_pair.fp1,
            "fp2": cross_pair.fp2,
            "expected_match": True,
            "should_commonness": "low/med",
            "should_distinctiveness": "med/high",
            "should_insufficiency": "low/med",
            "should_trust_adjustment": "low/med",
        },
        {
            "case": "Sparse fp (same device)",
            "fp1": base_a,
            "fp2": sparse_a,
            "expected_match": True,
            "should_commonness": "med/high",
            "should_distinctiveness": "low/med",
            "should_insufficiency": "high",
            "should_trust_adjustment": "med",
        },
        {
            "case": "Sparse fp (different device)",
            "fp1": sparse_a,
            "fp2": sparse_b,
            "expected_match": False,
            "should_commonness": "high",
            "should_distinctiveness": "low",
            "should_insufficiency": "high",
            "should_trust_adjustment": "med/high",
        },
    ]

    rows: List[Dict[str, Any]] = []
    for case in cases:
        breakdown = decompose_confidence(case["fp1"], case["fp2"], top_n=0)
        raw_same_device = breakdown.raw_profile_scores.get("same_device", breakdown.raw_similarity_score)
        final_same_device = breakdown.profile_scores.get("same_device", breakdown.overall_confidence)
        # Metric-aware bands:
        # - commonness/distinctiveness are 0-100 style.
        # - trust adjustment is in score points; values >20 are already substantial.
        commonness_band = _band(breakdown.commonness_score, low_to_med=40.0, med_to_high=70.0)
        distinctiveness_band = _band(breakdown.distinctiveness_score, low_to_med=40.0, med_to_high=70.0)
        insufficiency_band = _band(breakdown.insufficiency_risk, low_to_med=35.0, med_to_high=65.0)
        trust_band = _band(breakdown.trust_adjustment, low_to_med=8.0, med_to_high=20.0)

        commonness_ok = _band_matches(case["should_commonness"], commonness_band)
        distinctiveness_ok = _band_matches(case["should_distinctiveness"], distinctiveness_band)
        insufficiency_ok = _band_matches(case["should_insufficiency"], insufficiency_band)
        trust_ok = _band_matches(case["should_trust_adjustment"], trust_band)
        pass_count = int(commonness_ok) + int(distinctiveness_ok) + int(insufficiency_ok) + int(trust_ok)

        mismatches: List[str] = []
        if not commonness_ok:
            mismatches.append("commonness")
        if not distinctiveness_ok:
            mismatches.append("distinctiveness")
        if not insufficiency_ok:
            mismatches.append("insufficiency")
        if not trust_ok:
            mismatches.append("trust")

        rows.append(
            {
                "case": case["case"],
                "expected_match": case["expected_match"],
                "raw_device_similarity": raw_same_device,
                "commonness": breakdown.commonness_score,
                "distinctiveness": breakdown.distinctiveness_score,
                "collision_risk": breakdown.collision_risk,
                "insufficiency_risk": breakdown.insufficiency_risk,
                "trust_adjustment": breakdown.trust_adjustment,
                "final_profile_score": final_same_device,
                "obs_commonness_band": commonness_band,
                "obs_distinctiveness_band": distinctiveness_band,
                "obs_insufficiency_band": insufficiency_band,
                "obs_trust_band": trust_band,
                "should_commonness": case["should_commonness"],
                "should_distinctiveness": case["should_distinctiveness"],
                "should_insufficiency": case["should_insufficiency"],
                "should_trust_adjustment": case["should_trust_adjustment"],
                "semantic_check": "PASS" if pass_count == 4 else f"FAIL ({pass_count}/4)",
                "semantic_mismatches": ",".join(mismatches) if mismatches else "-",
                "policy_flags": ",".join(breakdown.policy_flags) if breakdown.policy_flags else "-",
            }
        )

    print(_format_table(rows))


def demo_single_scenarios():
    """Demo: Show each scenario type"""
    print("=" * 70)
    print("DEMO 1: Individual Scenario Types")
    print("=" * 70)
    
    # Show a few key scenarios
    scenarios_to_demo = [
        "BrowserDrift/Minor",
        "BrowserDrift/CrossBrowser",
        "PrivacyHardening/TorBrowser",
        "AdversarialPerturbation/CanvasNoise",
        "CommodityCollision/CorporateFleet",
    ]
    
    for scenario_type in scenarios_to_demo:
        print(f"\n--- {scenario_type} ---")
        pair = generate_scenario_pair(scenario_type)
        
        print(f"Expected Match: {pair.metadata.expected_match}")
        print(f"Difficulty: {pair.metadata.difficulty}")
        print(f"Description: {pair.metadata.description}")
        
        # Quick score
        breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=3)
        profile_scores = breakdown.profile_scores
        raw_profile_scores = breakdown.raw_profile_scores
        print(f"Overall Confidence: {breakdown.overall_confidence:.1f}/100")
        print(f"Raw Similarity: {breakdown.raw_similarity_score:.1f}/100")
        print(f"Collision Risk: {breakdown.collision_risk:.1f}/100")
        print(f"Insufficiency Risk: {breakdown.insufficiency_risk:.1f}/100")
        print(f"Trust Adjustment: -{breakdown.trust_adjustment:.1f}")
        print(f"Distinctiveness: {breakdown.distinctiveness_score:.1f}/100")
        print(f"Commonness: {breakdown.commonness_score:.1f}/100")
        print(f"Same Instance: {profile_scores.get('same_instance', breakdown.overall_confidence):.1f}/100")
        print(f"Same Environment: {profile_scores.get('same_environment', breakdown.overall_confidence):.1f}/100")
        print(f"Same Device: {profile_scores.get('same_device', breakdown.overall_confidence):.1f}/100")
        print(f"Same Entity: {profile_scores.get('same_entity', breakdown.overall_confidence):.1f}/100")
        print(
            f"Raw Same Device: "
            f"{raw_profile_scores.get('same_device', breakdown.raw_similarity_score):.1f}/100"
        )
        print(f"Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
        print(f"Attractor Risk: {breakdown.attractor_risk:.1f}/100")


def demo_scenario_categories():
    """Demo: Show all scenario categories"""
    print("\n" + "=" * 70)
    print("DEMO 2: Scenario Categories")
    print("=" * 70)
    
    categories = get_scenario_categories()
    
    for category, scenario_types in categories.items():
        print(f"\n{category}:")
        for st in scenario_types:
            print(f"  - {st}")


def demo_detailed_comparison():
    """Demo: Detailed analysis of a hard scenario"""
    print("\n" + "=" * 70)
    print("DEMO 3: Detailed Scenario Analysis")
    print("=" * 70)
    
    # Cross-browser scenario - should match but looks very different
    print("\n--- Cross-Browser Scenario (Hard Case) ---")
    pair = generate_scenario_pair("BrowserDrift/CrossBrowser")
    
    print(f"\nGround Truth: {pair.metadata.expected_match}")
    print(f"Difficulty: {pair.metadata.difficulty}")
    print(f"Description: {pair.metadata.description}\n")
    
    breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=5)
    print(format_breakdown(breakdown))


def demo_attractor_collision():
    """Demo: Attractor collision scenario"""
    print("\n" + "=" * 70)
    print("DEMO 4: Attractor Collision (Extreme Case)")
    print("=" * 70)
    
    # Corporate fleet - different users, identical setups
    print("\n--- Corporate Fleet Collision ---")
    pair = generate_scenario_pair("CommodityCollision/CorporateFleet")
    
    print(f"\nGround Truth: {pair.metadata.expected_match} (different users!)")
    print(f" Difficulty: {pair.metadata.difficulty}")
    print(f" Description: {pair.metadata.description}\n")
    
    breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=5)
    print(format_breakdown(breakdown))
    
    print("\nFalse Positive Risk:")
    print(f" Attractor Risk: {breakdown.attractor_risk:.1f}/100")
    print(f" Evidence Richness: {breakdown.evidence_richness:.1f}/100")
    print(f" Structural Stability: {breakdown.structural_stability:.1f}/100")
    print("High confidence, but they're different users!")


def demo_privacy_hardening():
    """Demo: Privacy hardening scenarios"""
    print("\n" + "=" * 70)
    print("DEMO 5: Privacy Hardening Scenarios")
    print("=" * 70)
    
    privacy_scenarios = [
        "PrivacyHardening/TorBrowser",
        "PrivacyHardening/ResistFingerprinting",
        "PrivacyHardening/CanvasDefender",
    ]
    
    for scenario_type in privacy_scenarios:
        print(f"\n--- {scenario_type} ---")
        pair = generate_scenario_pair(scenario_type)
        
        print(f"Expected Match: {pair.metadata.expected_match}")
        print(f"Description: {pair.metadata.description}")
        
        breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=2)
        
        print(f"\nScores:")
        print(f"  Overall Confidence: {breakdown.overall_confidence:.1f}/100")
        print(f"  Evidence Richness: {breakdown.evidence_richness:.1f}/100")
        print(f"  Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
        print(f"  Missing Fields: {len(breakdown.missing_fields)}")
        
        if breakdown.evidence_richness < 60:
            print("Low evidence - high-entropy fields missing or spoofed")


def demo_dataset_generation():
    """Demo: Generate a balanced dataset"""
    print("\n" + "=" * 70)
    print("DEMO 6: Balanced Dataset Generation")
    print("=" * 70)
    
    # Generate small balanced dataset
    dataset = generate_scenario_dataset(size=20)
    
    # Count by scenario type
    scenario_counts = {}
    expected_match_counts = {"True": 0, "False": 0}
    difficulty_counts = {}
    
    for pair in dataset:
        st = pair.metadata.scenario_type
        scenario_counts[st] = scenario_counts.get(st, 0) + 1
        
        match_key = str(pair.metadata.expected_match)
        expected_match_counts[match_key] += 1
        
        diff = pair.metadata.difficulty
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    print(f"\nGenerated {len(dataset)} scenario pairs\n")
    
    print("By Scenario Type:")
    for st, count in sorted(scenario_counts.items()):
        print(f"  {st}: {count}")
    
    print(f"\nBy Expected Match:")
    print(f"  Should Match: {expected_match_counts['True']}")
    print(f"  Should NOT Match: {expected_match_counts['False']}")
    
    print(f"\nBy Difficulty:")
    for diff, count in sorted(difficulty_counts.items()):
        print(f"  {diff}: {count}")


def demo_custom_distribution():
    """Demo: Custom scenario distribution"""
    print("\n" + "=" * 70)
    print("DEMO 7: Custom Distribution (Focus on Hard Cases)")
    print("=" * 70)
    
    # Focus more on hard/extreme scenarios
    custom_distribution = {
        # Less focus on easy cases
        "BrowserDrift/Minor": 0.05,
        "EnvironmentChange/HomeOffice": 0.05,
        "MobilityChurn/TimezoneTravel": 0.05,
        
        # More focus on hard cases
        "BrowserDrift/CrossBrowser": 0.15,
        "PrivacyHardening/ResistFingerprinting": 0.10,
        "PrivacyHardening/CanvasDefender": 0.10,
        "AdversarialPerturbation/CanvasNoise": 0.10,
        "AdversarialPerturbation/FontRandomization": 0.05,
        
        # Heavy focus on extreme collision cases
        "PrivacyHardening/TorBrowser": 0.15,
        "CommodityCollision/CorporateFleet": 0.10,
        "CommodityCollision/iPhoneDefaults": 0.10,
    }
    
    dataset = generate_scenario_dataset(size=50, scenario_distribution=custom_distribution)
    
    print(f"\nGenerated {len(dataset)} pairs with custom distribution")
    print("Focus: Hard and extreme cases (privacy, collisions, adversarial)\n")
    
    # Analyze difficulty distribution
    difficulty_counts = {}
    for pair in dataset:
        diff = pair.metadata.difficulty
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    print("Difficulty Distribution:")
    for diff in ["easy", "medium", "hard", "extreme"]:
        count = difficulty_counts.get(diff, 0)
        pct = (count / len(dataset)) * 100
        print(f"  {diff}: {count} ({pct:.1f}%)")


def demo_profiled_scenario_benchmark():
    """Demo: scenario benchmark with profile-aware threshold tables."""
    print("\n" + "=" * 70)
    print("DEMO 8: Scenario Benchmark (Profile-Aware)")
    print("=" * 70)

    dataset_size = 500
    dataset = generate_scenario_dataset(size=dataset_size)

    scored_pairs: List[Dict[str, Any]] = []
    for pair in dataset:
        breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=0)
        profile_scores = breakdown.profile_scores
        scored_pairs.append(
            {
                "scenario_type": pair.metadata.scenario_type,
                "difficulty": pair.metadata.difficulty,
                "sameDevice": pair.metadata.expected_match,
                "isAttractor": pair.metadata.difficulty == "extreme",
                "raw_overall": breakdown.raw_similarity_score,
                "overall": breakdown.overall_confidence,
                "trust_adjustment": breakdown.trust_adjustment,
                "collision_risk": breakdown.collision_risk,
                "insufficiency_risk": breakdown.insufficiency_risk,
                "distinctiveness": breakdown.distinctiveness_score,
                "commonness": breakdown.commonness_score,
                "same_instance": profile_scores.get("same_instance", breakdown.overall_confidence),
                "same_environment": profile_scores.get("same_environment", breakdown.overall_confidence),
                "same_device": profile_scores.get("same_device", breakdown.overall_confidence),
                "same_entity": profile_scores.get("same_entity", breakdown.overall_confidence),
                "richness": breakdown.evidence_richness,
                "attractor_risk": breakdown.attractor_risk,
            }
        )

    metrics_by_score = {
        "raw_overall": calculate_metrics(_as_metric_inputs(scored_pairs, "raw_overall")),
        "overall": calculate_metrics(_as_metric_inputs(scored_pairs, "overall")),
        "same_instance": calculate_metrics(_as_metric_inputs(scored_pairs, "same_instance")),
        "same_environment": calculate_metrics(_as_metric_inputs(scored_pairs, "same_environment")),
        "same_device": calculate_metrics(_as_metric_inputs(scored_pairs, "same_device")),
        "same_entity": calculate_metrics(_as_metric_inputs(scored_pairs, "same_entity")),
    }

    threshold_f1_rows: List[Dict[str, Any]] = []
    threshold_gap_rows: List[Dict[str, Any]] = []
    for index in range(len(metrics_by_score["overall"])):
        overall_row = metrics_by_score["overall"][index]
        instance_row = metrics_by_score["same_instance"][index]
        environment_row = metrics_by_score["same_environment"][index]
        device_row = metrics_by_score["same_device"][index]
        entity_row = metrics_by_score["same_entity"][index]

        threshold_f1_rows.append(
            {
                "threshold": overall_row.threshold,
                "raw_overall_f1": metrics_by_score["raw_overall"][index].f1,
                "overall_f1": overall_row.f1,
                "instance_f1": instance_row.f1,
                "environment_f1": environment_row.f1,
                "device_f1": device_row.f1,
                "entity_f1": entity_row.f1,
            }
        )
        threshold_gap_rows.append(
            {
                "threshold": overall_row.threshold,
                "raw_overall_gap": metrics_by_score["raw_overall"][index].far_frr_gap,
                "overall_gap": overall_row.far_frr_gap,
                "instance_gap": instance_row.far_frr_gap,
                "environment_gap": environment_row.far_frr_gap,
                "device_gap": device_row.far_frr_gap,
                "entity_gap": entity_row.far_frr_gap,
            }
        )

    scenario_rows: List[Dict[str, Any]] = []
    by_scenario: Dict[str, List[Dict[str, Any]]] = {}
    for row in scored_pairs:
        by_scenario.setdefault(str(row["scenario_type"]), []).append(row)

    for scenario_type in sorted(by_scenario.keys()):
        bucket = by_scenario[scenario_type]
        scenario_rows.append(
            {
                "scenario_type": scenario_type,
                "pairs": len(bucket),
                "expected_match_pct": _average([100.0 if b["sameDevice"] else 0.0 for b in bucket]),
                "raw_overall_mean": _average([float(b["raw_overall"]) for b in bucket]),
                "overall_mean": _average([float(b["overall"]) for b in bucket]),
                "trust_adjustment_mean": _average([float(b["trust_adjustment"]) for b in bucket]),
                "collision_risk_mean": _average([float(b["collision_risk"]) for b in bucket]),
                "insufficiency_risk_mean": _average([float(b["insufficiency_risk"]) for b in bucket]),
                "distinctiveness_mean": _average([float(b["distinctiveness"]) for b in bucket]),
                "commonness_mean": _average([float(b["commonness"]) for b in bucket]),
                "instance_mean": _average([float(b["same_instance"]) for b in bucket]),
                "environment_mean": _average([float(b["same_environment"]) for b in bucket]),
                "device_mean": _average([float(b["same_device"]) for b in bucket]),
                "entity_mean": _average([float(b["same_entity"]) for b in bucket]),
                "richness_mean": _average([float(b["richness"]) for b in bucket]),
                "attractor_risk_mean": _average([float(b["attractor_risk"]) for b in bucket]),
            }
        )

    best_by_score = {
        name: max(rows, key=lambda item: item.f1)
        for name, rows in metrics_by_score.items()
    }
    true_eer_by_score = {
        name: calculate_true_eer(rows)
        for name, rows in metrics_by_score.items()
    }
    per_threshold_rows = [
        {
            "threshold": row.threshold,
            "precision": row.precision,
            "recall": row.recall,
            "f1": row.f1,
            "far": row.far,
            "frr": row.frr,
            "gap_far_frr": row.far_frr_gap,
        }
        for row in metrics_by_score["overall"]
    ]
    summary_rows = []
    for name in ["raw_overall", "overall", "same_instance", "same_environment", "same_device", "same_entity"]:
        best = best_by_score[name]
        eer = true_eer_by_score[name]
        summary_rows.append(
            {
                "profile": name,
                "best_f1_threshold": best.threshold,
                "best_f1": best.f1,
                "eer_threshold": eer.threshold,
                "eer": eer.eer,
            }
        )

    print(f"Generated scenario pairs: {len(scored_pairs)}")
    print()
    print("Scenario Type Means:")
    print(_format_table(scenario_rows))
    print("Per-threshold table (overall):")
    print(_format_table(per_threshold_rows))
    print("Benchmark summary:")
    print(_format_table(summary_rows))
    print("Threshold Comparison (F1):")
    print(_format_table(threshold_f1_rows))
    print("Threshold Comparison (FAR/FRR Gap):")
    print(_format_table(threshold_gap_rows))


def main():
    """Run all demos"""
    demo_single_scenarios()
    demo_scenario_categories()
    demo_detailed_comparison()
    demo_attractor_collision()
    demo_privacy_hardening()
    demo_dataset_generation()
    demo_custom_distribution()
    demo_profiled_scenario_benchmark()
    demo_trust_semantics_truth_table()
    
    print("\n" + "=" * 70)
    print("All scenarios available:")
    print("=" * 70)
    for st in get_scenario_types():
        print(f"  - {st}")


if __name__ == "__main__":
    main()
