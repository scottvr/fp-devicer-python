from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


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
    family_similarities: Dict[str, float] = field(default_factory=dict)
    family_coverages: Dict[str, float] = field(default_factory=dict)
    family_effective_scores: Dict[str, float] = field(default_factory=dict)


# Field importance weights for family-level scoring and explainability.
FIELD_WEIGHTS = {
    # Rendering entropy family
    "canvas": 0.10,
    "webgl": 0.0875,
    "audio": 0.0625,

    # Structural family
    "screen.width": 0.10,
    "screen.height": 0.10,
    "screen.colorDepth": 0.04,
    "screen.pixelDepth": 0.03,
    "hardwareConcurrency": 0.06,
    "deviceMemory": 0.05,

    # Browser/software family
    "fonts": 0.06,
    "plugins": 0.03,
    "mimeTypes": 0.02,
    "platform": 0.04,
    "userAgent": 0.03,
    "appVersion": 0.02,
    "highEntropyValues": 0.04,

    # Locale/context family
    "timezone": 0.03,
    "language": 0.02,
    "languages": 0.02,

    # Everything else gets minimal weight
    "_default": 0.005,
}

# Field families
FAMILY_RENDERING = "rendering"
FAMILY_STRUCTURAL = "structural"
FAMILY_SOFTWARE = "software"
FAMILY_LOCALE = "locale"
FAMILY_MISC = "misc"

FAMILY_NAMES = [
    FAMILY_RENDERING,
    FAMILY_STRUCTURAL,
    FAMILY_SOFTWARE,
    FAMILY_LOCALE,
    FAMILY_MISC,
]

FAMILY_COVERAGE_INFLUENCE = 0.30

# Profile family weights. `richness` is a profile-level component.
PROFILE_WEIGHTS = {
    "same_instance": {
        FAMILY_RENDERING: 0.35,
        FAMILY_STRUCTURAL: 0.25,
        FAMILY_SOFTWARE: 0.25,
        FAMILY_LOCALE: 0.05,
        FAMILY_MISC: 0.00,
        "richness": 0.10,
    },
    "same_environment": {
        FAMILY_RENDERING: 0.25,
        FAMILY_STRUCTURAL: 0.30,
        FAMILY_SOFTWARE: 0.25,
        FAMILY_LOCALE: 0.10,
        FAMILY_MISC: 0.00,
        "richness": 0.10,
    },
    "same_device": {
        FAMILY_RENDERING: 0.20,
        FAMILY_STRUCTURAL: 0.35,
        FAMILY_SOFTWARE: 0.20,
        FAMILY_LOCALE: 0.05,
        FAMILY_MISC: 0.00,
        "richness": 0.20,
    },
    "same_entity": {
        FAMILY_RENDERING: 0.10,
        FAMILY_STRUCTURAL: 0.20,
        FAMILY_SOFTWARE: 0.15,
        FAMILY_LOCALE: 0.15,
        FAMILY_MISC: 0.00,
        "richness": 0.20,
    },
}

# Stable fields that shouldn't change much
STRUCTURAL_FIELDS = {
    "screen.width", "screen.height", "screen.colorDepth", "screen.pixelDepth",
    "hardwareConcurrency", "deviceMemory", "platform", "timezone"
}

# High-entropy fields (canvas, webgl, audio)
ENTROPY_FIELDS = {"canvas", "webgl", "audio"}

# Attractor patterns (common generic fingerprints)
ATTRACTOR_PATTERNS = [
    {"platform": "Win32", "userAgent": "Chrome"},
    {"platform": "MacIntel", "userAgent": "Safari"},
    {"platform": "iPhone", "deviceMemory": 8},
    {"platform": "Linux armv8l", "userAgent": "Chrome"},
]


def get_field_importance_weights() -> Dict[str, float]:
    """Returns the field importance weight map"""
    return FIELD_WEIGHTS.copy()


def _get_nested_value(data: Dict[str, Any], path: str) -> Optional[Any]:
    """Get value from nested dict using dot notation"""
    keys = path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _set_contains_nested(data: Dict[str, Any], field_set: Set[str]) -> bool:
    """Check if any field from set exists in nested dict"""
    for field_path in field_set:
        if _get_nested_value(data, field_path) is not None:
            return True
    return False


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


def _get_field_family(field_name: str) -> str:
    """Map a field into a scoring family."""
    if field_name in ENTROPY_FIELDS:
        return FAMILY_RENDERING
    if field_name.startswith("screen.") or field_name in {"hardwareConcurrency", "deviceMemory"}:
        return FAMILY_STRUCTURAL
    if field_name in {
        "fonts",
        "plugins",
        "mimeTypes",
        "platform",
        "userAgent",
        "appVersion",
        "highEntropyValues",
    }:
        return FAMILY_SOFTWARE
    if field_name in {"timezone", "language", "languages"}:
        return FAMILY_LOCALE
    return FAMILY_MISC


def _weighted_mean(pairs: List[Tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        return 0.0
    return sum(value * weight for value, weight in pairs) / total_weight


def _coverage_damped_similarity(similarity: float, coverage: float) -> float:
    alpha = max(0.0, min(1.0, FAMILY_COVERAGE_INFLUENCE))
    return similarity * ((1.0 - alpha) + alpha * coverage)


def _apply_gentle_attractor_penalty(score: float, attractor_risk: float, evidence_richness: float) -> float:
    """
    Dampen score only when risk is high and evidence is sparse.
    Max penalty is intentionally small.
    """
    risk = max(0.0, min(100.0, attractor_risk)) / 100.0
    richness = max(0.0, min(100.0, evidence_richness)) / 100.0
    penalty_points = 8.0 * risk * (1.0 - richness)
    return max(0.0, score - penalty_points)


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
    flat = _flatten_fingerprint(fp)

    expected_fields = [field for field in FIELD_WEIGHTS.keys() if field != "_default"]
    total_weight = sum(FIELD_WEIGHTS[field] for field in expected_fields)
    if total_weight <= 0:
        return 0.0

    present_weight = 0.0
    for field in expected_fields:
        val = flat.get(field)
        if val is not None and val != "" and val != []:
            present_weight += FIELD_WEIGHTS[field]

    return max(0.0, min(100.0, (present_weight / total_weight) * 100.0))


def calculate_attractor_risk(fp: Dict[str, Any], attractor_pool: Optional[List[Dict[str, Any]]] = None) -> float:
    """
    Calculate likelihood this is a common/generic fingerprint
    Returns 0-100 risk score (higher = more likely to be attractor)
    """
    risk_score = 0.0
    
    # Check against known attractor patterns
    for pattern in ATTRACTOR_PATTERNS:
        matches = all(
            str(fp.get(key, "")).find(str(val)) >= 0
            for key, val in pattern.items()
        )
        if matches:
            risk_score += 30.0
    
    # Check for generic values
    generic_markers = {
        "platform": ["Win32", "MacIntel"],
        "deviceMemory": [8, 16],
        "hardwareConcurrency": [4, 8],
        "language": ["en-US"],
    }
    
    for field, generic_values in generic_markers.items():
        if fp.get(field) in generic_values:
            risk_score += 10.0
    
    # Low entropy in high-entropy fields is suspicious
    fonts = fp.get("fonts", [])
    if isinstance(fonts, list) and len(fonts) < 8:
        risk_score += 15.0
    
    # If attractor pool provided, check similarity to pool
    if attractor_pool:
        # This would compare against known attractors
        # For now, placeholder - could use clustering distance
        pass
    
    return min(100.0, risk_score)


def decompose_confidence(
    fp1: Dict[str, Any],
    fp2: Dict[str, Any],
    attractor_pool: Optional[List[Dict[str, Any]]] = None,
    top_n: int = 5,
    primary_profile: str = "same_device",
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
    flat1 = _flatten_fingerprint(fp1)
    flat2 = _flatten_fingerprint(fp2)
    
    # Include known weighted fields so "both missing" is modeled as no evidence.
    weighted_fields = set(FIELD_WEIGHTS.keys()) - {"_default"}
    all_fields = (set(flat1.keys()) | set(flat2.keys()) | weighted_fields)

    # Compare each field with missingness-awareness.
    matches: List[FieldMatch] = []
    disagreements: List[FieldMismatch] = []

    missing_fields: List[str] = []
    comparable_fields = 0
    matching_fields = 0

    one_side_missing_fields = 0
    both_side_missing_fields = 0

    structural_fields_compared = 0
    entropy_fields_compared = 0

    total_weight = 0.0
    comparable_weight = 0.0

    family_total_weight = {name: 0.0 for name in FAMILY_NAMES}
    family_comparable_weight = {name: 0.0 for name in FAMILY_NAMES}
    family_weighted_similarity = {name: 0.0 for name in FAMILY_NAMES}

    structural_pairs: List[Tuple[float, float]] = []
    entropy_pairs: List[Tuple[float, float]] = []

    for field in sorted(all_fields):
        val1 = flat1.get(field)
        val2 = flat2.get(field)

        weight = _get_field_weight(field)
        family = _get_field_family(field)
        family_total_weight[family] += weight
        total_weight += weight

        if val1 is None and val2 is None:
            both_side_missing_fields += 1
            continue

        if val1 is None or val2 is None:
            one_side_missing_fields += 1
            if val1 is None:
                missing_fields.append(f"{field} (missing in fp1)")
            else:
                missing_fields.append(f"{field} (missing in fp2)")
            continue

        comparable_fields += 1
        comparable_weight += weight
        family_comparable_weight[family] += weight

        similarity, str1, str2 = _compare_field(val1, val2)
        family_weighted_similarity[family] += similarity * weight

        if field in STRUCTURAL_FIELDS:
            structural_fields_compared += 1
            structural_pairs.append((similarity, weight))

        if field in ENTROPY_FIELDS:
            entropy_fields_compared += 1
            entropy_pairs.append((similarity, weight))

        if similarity >= 90:
            matching_fields += 1
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

    # Family similarity / coverage / effective score.
    family_similarities: Dict[str, float] = {}
    family_coverages: Dict[str, float] = {}
    family_effective_scores: Dict[str, float] = {}

    for family in FAMILY_NAMES:
        total_family_weight = family_total_weight[family]
        comparable_family_weight = family_comparable_weight[family]

        similarity = (
            family_weighted_similarity[family] / comparable_family_weight
            if comparable_family_weight > 0
            else 0.0
        )
        coverage = (
            comparable_family_weight / total_family_weight
            if total_family_weight > 0
            else 0.0
        )
        effective = _coverage_damped_similarity(similarity, coverage)

        family_similarities[family] = similarity
        family_coverages[family] = coverage
        family_effective_scores[family] = effective

    # Missingness-aware evidence richness is based on comparable weight coverage.
    evidence_richness = (comparable_weight / total_weight * 100.0) if total_weight > 0 else 0.0

    field_agreement = (matching_fields / comparable_fields * 100) if comparable_fields > 0 else 0.0

    structural_stability = _weighted_mean(structural_pairs)
    entropy_contribution = _weighted_mean(entropy_pairs)

    # Core fingerprint similarity as family-first aggregate (without richness modifier).
    device_similarity = _weighted_mean(
        [
            (family_effective_scores[FAMILY_RENDERING], 0.30),
            (family_effective_scores[FAMILY_STRUCTURAL], 0.45),
            (family_effective_scores[FAMILY_SOFTWARE], 0.20),
            (family_effective_scores[FAMILY_LOCALE], 0.05),
        ]
    )

    attractor_risk = (
        calculate_attractor_risk(fp1, attractor_pool) +
        calculate_attractor_risk(fp2, attractor_pool)
    ) / 2.0

    # Profile scores
    profile_scores: Dict[str, float] = {}
    for profile_name, weights in PROFILE_WEIGHTS.items():
        pairs: List[Tuple[float, float]] = []
        for family in FAMILY_NAMES:
            family_weight = weights.get(family, 0.0)
            if family_weight > 0:
                pairs.append((family_effective_scores[family], family_weight))
        richness_weight = weights.get("richness", 0.0)
        if richness_weight > 0:
            pairs.append((evidence_richness, richness_weight))

        profile_raw = _weighted_mean(pairs)
        profile_scores[profile_name] = _apply_gentle_attractor_penalty(
            profile_raw,
            attractor_risk,
            evidence_richness,
        )

    if primary_profile not in profile_scores:
        primary_profile = "same_device"
    overall = profile_scores[primary_profile]

    # Sort matches by contribution (highest first)
    matches.sort(key=lambda m: m.contribution, reverse=True)
    top_matches = matches[:top_n]

    # Sort disagreements by penalty (highest first)
    disagreements.sort(key=lambda d: d.penalty, reverse=True)
    top_disagreements = disagreements[:top_n]

    return ScoreBreakdown(
        device_similarity=device_similarity,
        evidence_richness=evidence_richness,
        field_agreement=field_agreement,
        structural_stability=structural_stability,
        entropy_contribution=entropy_contribution,
        attractor_risk=attractor_risk,
        top_matches=top_matches,
        top_disagreements=top_disagreements,
        missing_fields=missing_fields,
        overall_confidence=overall,
        total_fields_compared=comparable_fields,
        structural_fields_compared=structural_fields_compared,
        entropy_fields_compared=entropy_fields_compared,
        one_side_missing_fields=one_side_missing_fields,
        both_side_missing_fields=both_side_missing_fields,
        profile_scores=profile_scores,
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
                lines.append(f"  {label:17} {breakdown.profile_scores[profile_name]:.1f}/100")
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

from typing import Any, Dict, List

from data_generator import LabeledFingerprint, generate_dataset, mutate, create_base_fingerprint
from metrics import ScoredPair, calculate_metrics

try:
    from devicer.libs.confidence import calculate_confidence
except ModuleNotFoundError:
    # Allows running this script directly from `src/devicer/benchmarks/`.
    # get rid of this eventually by adding scripts stubs to   pyproject.toml 
    from pathlib import Path
    import sys
    src_root = Path(__file__).resolve().parents[2]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from devicer.libs.confidence import calculate_confidence


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
    threshold_eer_rows: List[Dict[str, Any]] = []
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
        threshold_eer_rows.append(
            {
                "threshold": legacy_row.threshold,
                "legacy_eer": legacy_row.eer,
                "instance_eer": instance_row.eer,
                "environment_eer": env_row.eer,
                "device_eer": device_row.eer,
                "entity_eer": entity_row.eer,
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

    print(f"Dataset size: {dataset_size} devices x {sessions_per_device} sessions")
    print(f"Compared pairs: {len(pairs)}")
    print()
    print("Cohort Summary (means):")
    print(_format_table(cohort_rows))
    print("Threshold Comparison (F1):")
    print(_format_table(threshold_f1_rows))
    print("Threshold Comparison (EER):")
    print(_format_table(threshold_eer_rows))
    for name in ["legacy", "same_instance", "same_environment", "same_device", "same_entity"]:
        best = best_by_profile[name]
        print(
            f"Best {name}: "
            f"threshold={best.threshold}, f1={best.f1:.3f}, eer={best.eer:.3f}"
        )


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
