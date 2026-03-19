from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
import sys

try:
    from devicer.libs.confidence import (
        ENTROPY_FIELDS,
        FAMILY_LOCALE,
        FAMILY_MISC,
        FAMILY_NAMES,
        FAMILY_RENDERING,
        FAMILY_SOFTWARE,
        FAMILY_STRUCTURAL,
        DEFAULT_DECISION_THRESHOLD,
        DEFAULT_UNCERTAINTY_BAND,
        PROFILE_FIELD_WEIGHTS,
        STRUCTURAL_FIELDS,
        calculate_confidence,
        calculate_confidence_breakdown as lib_calculate_confidence_breakdown,
    )
except ModuleNotFoundError:
    # Allows running this script directly from `src/devicer/benchmarks/`.
    src_root = Path(__file__).resolve().parents[2]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from devicer.libs.confidence import (
        ENTROPY_FIELDS,
        FAMILY_LOCALE,
        FAMILY_MISC,
        FAMILY_NAMES,
        FAMILY_RENDERING,
        FAMILY_SOFTWARE,
        FAMILY_STRUCTURAL,
        DEFAULT_DECISION_THRESHOLD,
        DEFAULT_UNCERTAINTY_BAND,
        PROFILE_FIELD_WEIGHTS,
        STRUCTURAL_FIELDS,
        calculate_confidence,
        calculate_confidence_breakdown as lib_calculate_confidence_breakdown,
    )


@dataclass(frozen=True)
class FieldMatch:
    """Represents a contributing field similarity"""
    field_name: str
    similarity: float  # 0-100
    weight: float  # contribution weight
    value_a: str
    value_b: str
    contribution: float  # similarity * weight


@dataclass(frozen=True)
class FieldMismatch:
    """Represents a disagreeing field"""
    field_name: str
    similarity: float  # 0-100
    weight: float
    value_a: str
    value_b: str
    penalty: float  # (100 - similarity) * weight


@dataclass(frozen=True)
class ScoreBreakdown:
    """Multi-dimensional fingerprint comparison breakdown"""
    device_similarity: float  # 0-100: Core fingerprint match strength
    raw_similarity_score: float  # 0-100: Profile score before trust/commonness adjustment
    commonness_score: float  # 0-100: Higher means more generic/common fingerprint
    distinctiveness_score: float  # 0-100: Higher means more unique fingerprint evidence
    collision_risk: float  # 0-100: Estimated collision-prone risk used for trust adjustment
    insufficiency_risk: float  # 0-100: Evidence insufficiency/sparsity risk
    trust_adjustment: float  # absolute trust-layer shift magnitude in points
    trust_shift: float  # signed trust-layer shift (adjusted - raw)
    uncertainty_zone: bool  # True when score should not be treated as ordinary confidence
    confidence_label: str  # ordinary | low_confidence | uncertain_zone | abstain
    policy_action: str  # normal | low_confidence | challenge | review | abstain
    decision_threshold: float  # threshold used for uncertainty policy checks
    threshold_distance: float  # abs(final - decision_threshold)
    evidence_richness: float  # 0-100: How much data is present vs missing
    field_agreement: float  # 0-100: Percentage of comparable fields that match
    structural_stability: float  # 0-100: Agreement on stable fields (screen, hardware)
    entropy_contribution: float  # 0-100: TLSH/high-entropy field contribution
    attractor_risk: float  # 0-100: Likelihood this is a common/generic fingerprint
    top_matches: List[FieldMatch]  # Top N contributing field similarities
    top_disagreements: List[FieldMismatch]  # Top N disagreeing fields
    missing_fields: List[str]  # Fields present in one but not the other
    overall_confidence: float  # 0-100: Weighted composite (backward compat)
    
    # Additional metadata
    total_fields_compared: int = 0
    structural_fields_compared: int = 0
    entropy_fields_compared: int = 0
    one_side_missing_fields: int = 0
    both_side_missing_fields: int = 0
    profile_scores: Dict[str, float] = field(default_factory=dict)
    raw_profile_scores: Dict[str, float] = field(default_factory=dict)
    policy_flags: List[str] = field(default_factory=list)
    family_similarities: Dict[str, float] = field(default_factory=dict)
    family_coverages: Dict[str, float] = field(default_factory=dict)
    family_effective_scores: Dict[str, float] = field(default_factory=dict)


# Reuse the library's profile/family weighting configuration in benchmarks.
FIELD_WEIGHTS = PROFILE_FIELD_WEIGHTS


def get_field_importance_weights() -> Dict[str, float]:
    """Returns the field importance weight map"""
    return FIELD_WEIGHTS.copy()


def _calculate_jaccard_similarity(set_a: Set[Any], set_b: Set[Any]) -> float:
    """Calculate Jaccard similarity between two sets"""
    if not set_a and not set_b:
        return 100.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return (intersection / union * 100.0) if union > 0 else 0.0


def _to_hashable(value: Any) -> Any:
    """Convert nested containers into hashable forms for set-based comparisons."""
    if isinstance(value, dict):
        return frozenset((k, _to_hashable(v)) for k, v in value.items())
    if isinstance(value, list):
        return tuple(_to_hashable(item) for item in value)
    if isinstance(value, set):
        return frozenset(_to_hashable(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_to_hashable(item) for item in value)
    try:
        hash(value)
    except TypeError:
        return str(value)
    return value


def _calculate_string_similarity(str_a: str, str_b: str) -> float:
    """Calculate similarity between two strings (simple char overlap)"""
    if str_a == str_b:
        return 100.0
    if not str_a or not str_b:
        return 0.0
    
    # Simple character-level Jaccard for strings
    set_a = set(str_a.lower())
    set_b = set(str_b.lower())
    return _calculate_jaccard_similarity(set_a, set_b)


def _compare_field(val_a: Any, val_b: Any) -> Tuple[float, str, str]:
    """
    Compare two field values, return (similarity 0-100, str_repr_a, str_repr_b)
    """
    # Exact match
    if val_a == val_b:
        return 100.0, str(val_a), str(val_b)
    
    # Both None/missing
    if val_a is None and val_b is None:
        return 100.0, "None", "None"
    
    # One missing
    if val_a is None or val_b is None:
        return 0.0, str(val_a), str(val_b)
    
    # Lists (fonts, plugins, etc.)
    if isinstance(val_a, list) and isinstance(val_b, list):
        set_a = {_to_hashable(item) for item in val_a}
        set_b = {_to_hashable(item) for item in val_b}
        similarity = _calculate_jaccard_similarity(set_a, set_b)
        return similarity, f"[{len(val_a)} items]", f"[{len(val_b)} items]"
    
    # Dicts (screen, highEntropyValues, etc.)
    if isinstance(val_a, dict) and isinstance(val_b, dict):
        # Compare dict keys and values
        keys_a, keys_b = set(val_a.keys()), set(val_b.keys())
        common_keys = keys_a & keys_b
        if not common_keys:
            return 0.0, str(val_a), str(val_b)
        
        matches = sum(1 for k in common_keys if val_a[k] == val_b[k])
        similarity = (matches / len(common_keys)) * 100.0
        return similarity, str(val_a), str(val_b)
    
    # Numbers
    if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
        # Calculate percentage difference
        avg = (abs(val_a) + abs(val_b)) / 2
        if avg == 0:
            return 100.0, str(val_a), str(val_b)
        diff_pct = abs(val_a - val_b) / avg * 100
        similarity = max(0, 100 - diff_pct)
        return similarity, str(val_a), str(val_b)
    
    # Strings
    if isinstance(val_a, str) and isinstance(val_b, str):
        similarity = _calculate_string_similarity(val_a, val_b)
        return similarity, val_a, val_b
    
    # Type mismatch
    return 0.0, str(val_a), str(val_b)


def _get_field_weight(field_name: str) -> float:
    """Get weight for a field"""
    return FIELD_WEIGHTS.get(field_name, FIELD_WEIGHTS["_default"])


def _flatten_fingerprint(fp: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten nested fingerprint dict into dot-notation keys"""
    result = {}
    for key, value in fp.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict) and key != "highEntropyValues":
            result.update(_flatten_fingerprint(value, full_key))
        else:
            result[full_key] = value
    
    return result


def calculate_evidence_richness(fp: Dict[str, Any]) -> float:
    """
    Calculate weighted evidence coverage for a single fingerprint.
    Returns 0-100 score
    """
    return float(lib_calculate_confidence_breakdown(fp, fp).evidence_richness)


def calculate_attractor_risk(fp: Dict[str, Any], attractor_pool: Optional[List[Dict[str, Any]]] = None) -> float:
    """
    Calculate likelihood this is a common/generic fingerprint
    Returns 0-100 risk score (higher = more likely to be attractor)
    """
    del attractor_pool  # Reserved for backwards compatibility in benchmark API.
    return float(lib_calculate_confidence_breakdown(fp, fp).attractor_risk)


def decompose_confidence(
    fp1: Dict[str, Any],
    fp2: Dict[str, Any],
    attractor_pool: Optional[List[Dict[str, Any]]] = None,
    top_n: int = 5,
    primary_profile: str = "same_device",
    decision_threshold: float = DEFAULT_DECISION_THRESHOLD,
    uncertainty_band: float = DEFAULT_UNCERTAINTY_BAND,
) -> ScoreBreakdown:
    """
    Decompose fingerprint comparison into multi-dimensional scores
    
    Args:
        fp1: First fingerprint
        fp2: Second fingerprint
        attractor_pool: Optional list of known attractor fingerprints
        top_n: Number of top matches/disagreements to return
    
    Returns:
        ScoreBreakdown with detailed comparison metrics
    """
    del attractor_pool  # Reserved for backwards compatibility in benchmark API.

    core = lib_calculate_confidence_breakdown(
        fp1,
        fp2,
        primary_profile=primary_profile,
        decision_threshold=decision_threshold,
        uncertainty_band=uncertainty_band,
    )

    flat1 = _flatten_fingerprint(fp1)
    flat2 = _flatten_fingerprint(fp2)
    weighted_fields = set(FIELD_WEIGHTS.keys()) - {"_default"}
    all_fields = (set(flat1.keys()) | set(flat2.keys()) | weighted_fields)

    matches: List[FieldMatch] = []
    disagreements: List[FieldMismatch] = []
    missing_fields: List[str] = []
    structural_fields_compared = 0
    entropy_fields_compared = 0

    for field in sorted(all_fields):
        val1 = flat1.get(field)
        val2 = flat2.get(field)
        weight = _get_field_weight(field)

        if val1 is None and val2 is None:
            continue

        if val1 is None or val2 is None:
            if val1 is None:
                missing_fields.append(f"{field} (missing in fp1)")
            else:
                missing_fields.append(f"{field} (missing in fp2)")
            continue

        similarity, str1, str2 = _compare_field(val1, val2)

        if field in STRUCTURAL_FIELDS:
            structural_fields_compared += 1
        if field in ENTROPY_FIELDS:
            entropy_fields_compared += 1

        if similarity >= 90:
            matches.append(FieldMatch(
                field_name=field,
                similarity=similarity,
                weight=weight,
                value_a=str1,
                value_b=str2,
                contribution=similarity * weight
            ))
        elif similarity < 70:
            disagreements.append(FieldMismatch(
                field_name=field,
                similarity=similarity,
                weight=weight,
                value_a=str1,
                value_b=str2,
                penalty=(100 - similarity) * weight
            ))

    family_similarities = (
        {name: float(value) for name, value in core.family_similarities.items()}
        if core.family_similarities
        else {
            family: float(family_score.similarity)
            for family, family_score in core.family_scores.items()
        }
    )
    family_coverages = (
        {name: float(value) for name, value in core.family_coverages.items()}
        if core.family_coverages
        else {
            family: float(family_score.coverage) / 100.0
            for family, family_score in core.family_scores.items()
        }
    )
    family_effective_scores = (
        {name: float(value) for name, value in core.family_effective_scores.items()}
        if core.family_effective_scores
        else {
            family: float(family_score.effective)
            for family, family_score in core.family_scores.items()
        }
    )
    profile_scores = {name: float(score) for name, score in core.profile_scores.items()}
    raw_profile_scores = {name: float(score) for name, score in core.raw_profile_scores.items()}

    # Sort matches by contribution (highest first)
    matches.sort(key=lambda m: m.contribution, reverse=True)
    top_matches = matches[:top_n]

    # Sort disagreements by penalty (highest first)
    disagreements.sort(key=lambda d: d.penalty, reverse=True)
    top_disagreements = disagreements[:top_n]

    return ScoreBreakdown(
        device_similarity=float(core.device_similarity),
        raw_similarity_score=float(core.raw_similarity_score),
        commonness_score=float(core.commonness_score),
        distinctiveness_score=float(core.distinctiveness_score),
        collision_risk=float(core.collision_risk),
        insufficiency_risk=float(core.insufficiency_risk),
        trust_adjustment=float(core.trust_adjustment),
        trust_shift=float(core.trust_shift),
        uncertainty_zone=bool(core.uncertainty_zone),
        confidence_label=str(core.confidence_label),
        policy_action=str(core.policy_action),
        decision_threshold=float(core.decision_threshold),
        threshold_distance=float(core.threshold_distance),
        evidence_richness=float(core.evidence_richness),
        field_agreement=float(core.field_agreement),
        structural_stability=float(core.structural_stability),
        entropy_contribution=float(core.entropy_contribution),
        attractor_risk=float(core.attractor_risk),
        top_matches=top_matches,
        top_disagreements=top_disagreements,
        missing_fields=missing_fields,
        overall_confidence=float(core.overall_confidence),
        total_fields_compared=int(core.total_fields_compared),
        structural_fields_compared=structural_fields_compared,
        entropy_fields_compared=entropy_fields_compared,
        one_side_missing_fields=int(core.one_side_missing_fields),
        both_side_missing_fields=int(core.both_side_missing_fields),
        profile_scores=profile_scores,
        raw_profile_scores=raw_profile_scores,
        policy_flags=list(core.policy_flags),
        family_similarities=family_similarities,
        family_coverages=family_coverages,
        family_effective_scores=family_effective_scores,
    )


def format_breakdown(breakdown: ScoreBreakdown) -> str:
    """
    Format a ScoreBreakdown as human-readable text
    
    Args:
        breakdown: The ScoreBreakdown to format
    
    Returns:
        Formatted string representation
    """
    lines = [
        "=== Score Breakdown ===",
        f"Overall Confidence: {breakdown.overall_confidence:.1f}/100",
        "",
        "Identity Layer:",
        f"  Raw Similarity:        {breakdown.raw_similarity_score:.1f}/100",
        f"  Commonness Score:      {breakdown.commonness_score:.1f}/100",
        f"  Distinctiveness Score: {breakdown.distinctiveness_score:.1f}/100",
        f"  Collision Risk:        {breakdown.collision_risk:.1f}/100",
        f"  Insufficiency Risk:    {breakdown.insufficiency_risk:.1f}/100",
        f"  Trust-Adjusted:        {breakdown.overall_confidence:.1f}/100",
        f"  Trust Shift:           {breakdown.trust_shift:+.1f}",
        f"  Trust Adjustment:      {breakdown.trust_adjustment:.1f}",
        f"  Confidence Label:      {breakdown.confidence_label}",
        f"  Policy Action:         {breakdown.policy_action}",
        f"  Uncertainty Zone:      {breakdown.uncertainty_zone}",
        f"  Decision Threshold:    {breakdown.decision_threshold:.1f}",
        f"  Threshold Distance:    {breakdown.threshold_distance:.1f}",
        "",
        "Dimensions:",
        f"  Device Similarity:     {breakdown.device_similarity:.1f}/100",
        f"  Evidence Richness:     {breakdown.evidence_richness:.1f}/100",
        f"  Field Agreement:       {breakdown.field_agreement:.1f}% ({breakdown.total_fields_compared} fields)",
        f"  Structural Stability:  {breakdown.structural_stability:.1f}/100",
        f"  Entropy Contribution:  {breakdown.entropy_contribution:.1f}/100",
        f"  Attractor Risk:        {breakdown.attractor_risk:.1f}/100",
        f"  Missing (one-side):    {breakdown.one_side_missing_fields}",
        f"  Missing (both-side):   {breakdown.both_side_missing_fields}",
        "",
    ]

    if breakdown.profile_scores:
        lines.append("Profile Scores:")
        for profile_name in ["same_instance", "same_environment", "same_device", "same_entity"]:
            if profile_name in breakdown.profile_scores:
                label = profile_name.replace("_", " ").title()
                raw_value = breakdown.raw_profile_scores.get(profile_name, breakdown.profile_scores[profile_name])
                adjusted_value = breakdown.profile_scores[profile_name]
                lines.append(f"  {label:17} raw={raw_value:5.1f} adjusted={adjusted_value:5.1f}")
        lines.append("")

    if breakdown.policy_flags:
        lines.append("Trust Policy Flags:")
        for flag in breakdown.policy_flags:
            lines.append(f"  - {flag}")
        lines.append("")

    if breakdown.family_effective_scores:
        lines.append("Family Scores (similarity / coverage / effective):")
        for family in [FAMILY_RENDERING, FAMILY_STRUCTURAL, FAMILY_SOFTWARE, FAMILY_LOCALE, FAMILY_MISC]:
            if family not in breakdown.family_effective_scores:
                continue
            similarity = breakdown.family_similarities.get(family, 0.0)
            coverage = breakdown.family_coverages.get(family, 0.0)
            effective = breakdown.family_effective_scores.get(family, 0.0)
            lines.append(
                f"  {family:10} {similarity:5.1f} / {coverage * 100:5.1f}% / {effective:5.1f}"
            )
        lines.append("")
    
    if breakdown.top_matches:
        lines.append("Top Contributing Matches:")
        for match in breakdown.top_matches:
            lines.append(
                f" {match.field_name}: {match.similarity:.0f}% "
                f"(weight: {match.weight:.3f}, contribution: {match.contribution:.2f})"
            )
        lines.append("")
    
    if breakdown.top_disagreements:
        lines.append("Top Disagreements:")
        for dis in breakdown.top_disagreements:
            lines.append(
                f"{dis.field_name}: {dis.similarity:.0f}% "
                f"(weight: {dis.weight:.3f}, penalty: {dis.penalty:.2f})"
            )
            lines.append(f"      A: {dis.value_a[:50]}")
            lines.append(f"      B: {dis.value_b[:50]}")
        lines.append("")
    
    if breakdown.missing_fields:
        lines.append(f"Missing Fields ({len(breakdown.missing_fields)}):")
        for mf in breakdown.missing_fields[:5]:  # Show first 5
            lines.append(f"  - {mf}")
        if len(breakdown.missing_fields) > 5:
            lines.append(f"  ... and {len(breakdown.missing_fields) - 5} more")
        lines.append("")
    
    return "\n".join(lines)

#### DEMO

from data_generator import LabeledFingerprint, generate_dataset, mutate, create_base_fingerprint
from metrics import ScoredPair, calculate_metrics, calculate_true_eer


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


def _score_pair(
    left: LabeledFingerprint,
    right: LabeledFingerprint,
    same_device: bool,
) -> Dict[str, Any]:
    breakdown = decompose_confidence(left.data, right.data, top_n=0)
    profile_scores = breakdown.profile_scores
    return {
        "legacyScore": float(calculate_confidence(left.data, right.data)),
        "breakdownScore": float(profile_scores.get("same_device", breakdown.overall_confidence)),
        "same_instance": float(profile_scores.get("same_instance", breakdown.overall_confidence)),
        "same_environment": float(profile_scores.get("same_environment", breakdown.overall_confidence)),
        "same_device": float(profile_scores.get("same_device", breakdown.overall_confidence)),
        "same_entity": float(profile_scores.get("same_entity", breakdown.overall_confidence)),
        "evidenceRichness": float(breakdown.evidence_richness),
        "deviceSimilarity": float(breakdown.device_similarity),
        "entropyContribution": float(breakdown.entropy_contribution),
        "attractorRisk": float(breakdown.attractor_risk),
        "sameDevice": same_device,
        "isAttractor": bool(left.is_attractor or right.is_attractor),
    }


def _generate_comparison_pairs(
    groups: Dict[str, List[LabeledFingerprint]],
    iterations: int = 2500,
) -> List[Dict[str, Any]]:
    devices = list(groups.keys())
    sorted_by_size = sorted(devices, key=lambda x: len(groups[x]), reverse=True)
    attractor_pool_size = max(1, int(len(sorted_by_size) * 0.1 + 0.9999))

    scored_pairs: List[Dict[str, Any]] = []
    for i in range(iterations):
        dev = devices[i % len(devices)]
        samples = groups[dev]
        if len(samples) < 2:
            continue

        idx1 = i % len(samples)
        idx2 = (idx1 + 1 + i) % len(samples)
        a = samples[idx1]
        b = samples[idx2]
        scored_pairs.append(_score_pair(a, b, same_device=True))

        dev2 = devices[(i + 1) % len(devices)]
        c = groups[dev2][i % len(groups[dev2])]
        d = groups[dev][(idx1 + 3) % len(samples)]

        use_cross_browser = (i % 10) < 3
        if use_cross_browser and len(samples) >= 2:
            idx3 = (idx1 + (len(samples) // 2)) % len(samples)
            cross_a = samples[idx3]
            attractor_dev = sorted_by_size[i % attractor_pool_size]
            attractor_samples = groups[attractor_dev]
            attractor_sample = attractor_samples[i % len(attractor_samples)]
            cross_b = (
                attractor_sample
                if attractor_dev != dev
                else groups[dev2][i % len(groups[dev2])]
            )
            scored_pairs.append(_score_pair(cross_a, cross_b, same_device=False))

        scored_pairs.append(_score_pair(c, d, same_device=False))

    return scored_pairs


def _as_metric_inputs(
    pairs: List[Dict[str, Any]],
    score_key: str,
) -> List[ScoredPair]:
    return [
        {
            "score": float(pair[score_key]),
            "sameDevice": bool(pair["sameDevice"]),
            "isAttractor": bool(pair["isAttractor"]),
        }
        for pair in pairs
    ]


def demo_large_dataset_comparison():
    """Demo: large-sample benchmark comparing scalar confidence vs breakdown score."""
    print("=" * 70)
    print("DEMO 7: Large Dataset Threshold Comparison")
    print("=" * 70)

    dataset_size = 2000
    sessions_per_device = 5

    dataset = generate_dataset(size=dataset_size, sessions_per_device=sessions_per_device)
    groups: Dict[str, List[LabeledFingerprint]] = {}
    for item in dataset:
        groups.setdefault(item.device_label, []).append(item)

    pairs = _generate_comparison_pairs(groups, iterations=2500)

    metrics_by_score = {
        "legacy": calculate_metrics(_as_metric_inputs(pairs, "legacyScore")),
        "same_instance": calculate_metrics(_as_metric_inputs(pairs, "same_instance")),
        "same_environment": calculate_metrics(_as_metric_inputs(pairs, "same_environment")),
        "same_device": calculate_metrics(_as_metric_inputs(pairs, "same_device")),
        "same_entity": calculate_metrics(_as_metric_inputs(pairs, "same_entity")),
    }

    threshold_f1_rows: List[Dict[str, Any]] = []
    threshold_gap_rows: List[Dict[str, Any]] = []
    for index in range(len(metrics_by_score["legacy"])):
        legacy_row = metrics_by_score["legacy"][index]
        instance_row = metrics_by_score["same_instance"][index]
        env_row = metrics_by_score["same_environment"][index]
        device_row = metrics_by_score["same_device"][index]
        entity_row = metrics_by_score["same_entity"][index]

        threshold_f1_rows.append(
            {
                "threshold": legacy_row.threshold,
                "legacy_f1": legacy_row.f1,
                "instance_f1": instance_row.f1,
                "environment_f1": env_row.f1,
                "device_f1": device_row.f1,
                "entity_f1": entity_row.f1,
            }
        )
        threshold_gap_rows.append(
            {
                "threshold": legacy_row.threshold,
                "legacy_gap": legacy_row.far_frr_gap,
                "instance_gap": instance_row.far_frr_gap,
                "environment_gap": env_row.far_frr_gap,
                "device_gap": device_row.far_frr_gap,
                "entity_gap": entity_row.far_frr_gap,
            }
        )

    same_pairs = [pair for pair in pairs if pair["sameDevice"]]
    diff_pairs = [pair for pair in pairs if not pair["sameDevice"]]
    attractor_impostors = [
        pair for pair in diff_pairs if pair["isAttractor"]
    ]

    cohort_rows = []
    for name, bucket in [
        ("sameDevice", same_pairs),
        ("differentDevice", diff_pairs),
        ("attractorImpostor", attractor_impostors),
    ]:
        cohort_rows.append(
            {
                "cohort": name,
                "pairs": len(bucket),
                "legacy_mean": _average([float(p["legacyScore"]) for p in bucket]),
                "same_instance_mean": _average([float(p["same_instance"]) for p in bucket]),
                "same_environment_mean": _average([float(p["same_environment"]) for p in bucket]),
                "same_device_mean": _average([float(p["same_device"]) for p in bucket]),
                "same_entity_mean": _average([float(p["same_entity"]) for p in bucket]),
                "richness_mean": _average([float(p["evidenceRichness"]) for p in bucket]),
                "attractor_risk_mean": _average([float(p["attractorRisk"]) for p in bucket]),
            }
        )

    cohort_rows.append(
        {
            "cohort": "separation(same-diff)",
            "pairs": "-",
            "legacy_mean": cohort_rows[0]["legacy_mean"] - cohort_rows[1]["legacy_mean"],
            "same_instance_mean": cohort_rows[0]["same_instance_mean"] - cohort_rows[1]["same_instance_mean"],
            "same_environment_mean": cohort_rows[0]["same_environment_mean"] - cohort_rows[1]["same_environment_mean"],
            "same_device_mean": cohort_rows[0]["same_device_mean"] - cohort_rows[1]["same_device_mean"],
            "same_entity_mean": cohort_rows[0]["same_entity_mean"] - cohort_rows[1]["same_entity_mean"],
            "richness_mean": cohort_rows[0]["richness_mean"] - cohort_rows[1]["richness_mean"],
            "attractor_risk_mean": "-",
        }
    )

    best_by_profile = {
        name: max(rows, key=lambda item: item.f1)
        for name, rows in metrics_by_score.items()
    }
    true_eer_by_profile = {
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
        for row in metrics_by_score["legacy"]
    ]
    summary_rows = []
    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
        best = best_by_profile[name]
        eer = true_eer_by_profile[name]
        summary_rows.append(
            {
                "profile": name,
                "best_f1_threshold": best.threshold,
                "best_f1": best.f1,
                "eer_threshold": eer.threshold,
                "eer": eer.eer,
            }
        )

    print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
    print(f"Compared pairs: {len(pairs)}")
    print()
    print("Cohort Summary (means):")
    print(_format_table(cohort_rows))
    print("Per-threshold table (legacy):")
    print(_format_table(per_threshold_rows))
    print("Benchmark summary:")
    print(_format_table(summary_rows))
    print("Threshold Comparison (F1):")
    print(_format_table(threshold_f1_rows))
    print("Threshold Comparison (FAR/FRR Gap):")
    print(_format_table(threshold_gap_rows))


def demo_basic_comparison():
    """Demo: Compare two fingerprints from same device"""
    print("=" * 70)
    print("DEMO 1: Same Device, Minor Drift")
    print("=" * 70)
    
    # Generate base fingerprint
    base = create_base_fingerprint(12345)
    
    # Create slightly mutated version (low drift)
    mutated = mutate(base, "low")
    
    # Decompose the comparison
    breakdown = decompose_confidence(base, mutated, top_n=5)
    
    print(format_breakdown(breakdown))


def demo_cross_browser():
    """Demo: Same device, different browser"""
    print("=" * 70)
    print("DEMO 2: Same Device, High Drift (Cross-Browser Simulation)")
    print("=" * 70)
    
    base = create_base_fingerprint(12345)
    high_drift = mutate(base, "high")
    
    breakdown = decompose_confidence(base, high_drift, top_n=5)
    
    print(format_breakdown(breakdown))


def demo_different_devices():
    """Demo: Different devices"""
    print("=" * 70)
    print("DEMO 3: Different Devices")
    print("=" * 70)
    
    device_a = create_base_fingerprint(11111)
    device_b = create_base_fingerprint(22222)
    
    breakdown = decompose_confidence(device_a, device_b, top_n=5)
    
    print(format_breakdown(breakdown))


def demo_evidence_richness():
    """Demo: Evidence richness calculation"""
    print("=" * 70)
    print("DEMO 4: Evidence Richness")
    print("=" * 70)
    
    rich_fp = create_base_fingerprint(12345)
    
    # Create sparse fingerprint (missing fields)
    sparse_fp = {
        "userAgent": rich_fp["userAgent"],
        "platform": rich_fp["platform"],
        "timezone": "America/New_York",
    }
    
    rich_score = calculate_evidence_richness(rich_fp)
    sparse_score = calculate_evidence_richness(sparse_fp)
    
    print(f"Rich fingerprint evidence score: {rich_score:.1f}/100")
    print(f"Sparse fingerprint evidence score: {sparse_score:.1f}/100")
    print()
    
    # Compare them
    breakdown = decompose_confidence(rich_fp, sparse_fp, top_n=5)
    print(format_breakdown(breakdown))


def demo_attractor_risk():
    """Demo: Attractor risk calculation"""
    print("=" * 70)
    print("DEMO 5: Attractor Risk Detection")
    print("=" * 70)
    
    # Generic Windows + Chrome fingerprint (high attractor risk)
    generic_fp = {
        "platform": "Win32",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "deviceMemory": 8,
        "hardwareConcurrency": 8,
        "language": "en-US",
        "timezone": "America/New_York",
        "fonts": ["Arial", "Times New Roman"],  # Very few fonts
    }
    
    # Unique fingerprint (low attractor risk)
    unique_fp = create_base_fingerprint(99999)
    
    generic_risk = calculate_attractor_risk(generic_fp)
    unique_risk = calculate_attractor_risk(unique_fp)
    
    print(f"Generic fingerprint attractor risk: {generic_risk:.1f}/100")
    print(f"Unique fingerprint attractor risk: {unique_risk:.1f}/100")
    print()


def demo_dataset_analysis():
    """Demo: Analyze a small dataset"""
    print("=" * 70)
    print("DEMO 6: Dataset Analysis")
    print("=" * 70)
    
    # Generate small dataset
    dataset = generate_dataset(size=5, sessions_per_device=2)
    
    # Compare first two sessions of same device
    device_sessions = {}
    for item in dataset:
        device_sessions.setdefault(item.device_label, []).append(item)
    
    for device_id, sessions in list(device_sessions.items())[:2]:
        if len(sessions) >= 2:
            print(f"\n--- Device: {device_id[:12]}... ---")
            print(f"Is Attractor: {sessions[0].is_attractor}")
            
            breakdown = decompose_confidence(
                sessions[0].data,
                sessions[1].data,
                top_n=3
            )
            
            print(f"Overall Confidence: {breakdown.overall_confidence:.1f}/100")
            print(f"Device Similarity: {breakdown.device_similarity:.1f}/100")
            print(f"Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
            print(f"Attractor Risk: {breakdown.attractor_risk:.1f}/100")


def main():
    demo_basic_comparison()
    print("\n\n")
    demo_cross_browser()
    print("\n\n")
    demo_different_devices()
    print("\n\n")
    demo_evidence_richness()
    print("\n\n")
    demo_attractor_risk()
    print("\n\n")
    demo_dataset_analysis()
    print("\n\n")
    demo_large_dataset_comparison()

if __name__ == "__main__":
    main()
