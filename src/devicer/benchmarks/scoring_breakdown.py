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

DEFAULT_DECISION_THRESHOLD = 65.0
DEFAULT_UNCERTAINTY_BAND = 8.0

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


def _clamp_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _compute_commonness_and_flags(
    attractor_risk: float,
    evidence_richness: float,
    entropy_contribution: float,
    family_similarities: Dict[str, float],
    family_coverages: Dict[str, float],
) -> Tuple[float, float, List[str]]:
    """
    Produce a pair-level commonness/distinctiveness estimate.

    Commonness is intentionally narrow:
    standardized/default/commodity profile likelihood, not generic uncertainty.
    """
    rendering_similarity = family_similarities.get(FAMILY_RENDERING, 0.0)
    rendering_coverage = family_coverages.get(FAMILY_RENDERING, 0.0) * 100.0
    software_similarity = family_similarities.get(FAMILY_SOFTWARE, 0.0)
    locale_similarity = family_similarities.get(FAMILY_LOCALE, 0.0)

    standardized_entropy = rendering_similarity * (rendering_coverage / 100.0)
    software_locale_genericness = _clamp_0_100((software_similarity * 0.6) + (locale_similarity * 0.4))

    commonness = (
        0.70 * attractor_risk
        + 0.20 * standardized_entropy
        + 0.10 * software_locale_genericness
    )

    flags: List[str] = []
    if attractor_risk >= 55:
        flags.append("high_commonness_profile")
    if standardized_entropy >= 82 and entropy_contribution >= 75:
        flags.append("entropy_standardized")
    if evidence_richness >= 75 and commonness >= 55:
        flags.append("rich_but_common")
    if software_locale_genericness >= 88:
        flags.append("generic_software_locale")

    if "high_commonness_profile" in flags and "entropy_standardized" in flags:
        commonness += 10.0
    if "rich_but_common" in flags:
        commonness += 5.0

    commonness = _clamp_0_100(commonness)
    distinctiveness = 100.0 - commonness
    return commonness, distinctiveness, flags


def _compute_insufficiency_risk_and_flags(
    evidence_richness: float,
    comparable_field_count: int,
    family_coverages: Dict[str, float],
) -> Tuple[float, List[str]]:
    """
    Compute 0-1 insufficiency/sparsity risk from missing coverage and low richness.
    """
    rendering_cov = _clamp_01(family_coverages.get(FAMILY_RENDERING, 0.0))
    structural_cov = _clamp_01(family_coverages.get(FAMILY_STRUCTURAL, 0.0))
    software_cov = _clamp_01(family_coverages.get(FAMILY_SOFTWARE, 0.0))
    locale_cov = _clamp_01(family_coverages.get(FAMILY_LOCALE, 0.0))

    richness_shortfall = _clamp_01((74.0 - evidence_richness) / 40.0)
    comparable_shortfall = _clamp_01((14.0 - float(comparable_field_count)) / 9.0)
    structural_absence = _clamp_01((0.55 - structural_cov) / 0.55)
    rendering_absence = _clamp_01((0.40 - rendering_cov) / 0.40)
    software_absence = _clamp_01((0.50 - software_cov) / 0.50)
    key_family_absence = (
        0.45 * structural_absence
        + 0.40 * rendering_absence
        + 0.15 * software_absence
    )
    weak_context = _clamp_01((0.45 - locale_cov) / 0.45)

    insufficiency_risk = (
        0.45 * richness_shortfall
        + 0.25 * comparable_shortfall
        + 0.20 * key_family_absence
        + 0.10 * weak_context
    )

    flags: List[str] = []
    if evidence_richness < 65:
        flags.append("insufficient_evidence")
    if comparable_field_count < 14:
        flags.append("low_comparable_fields")
    if structural_cov < 0.55 or rendering_cov < 0.45 or software_cov < 0.45:
        flags.append("missing_key_families")
    if rendering_cov < 0.20:
        flags.append("entropy_family_absent")
    if structural_cov < 0.30:
        flags.append("structural_family_absent")
    if software_cov < 0.35:
        flags.append("thin_software_family")
    if (
        evidence_richness < 62
        and comparable_field_count < 13
        and (rendering_cov < 0.25 or software_cov < 0.40)
    ):
        flags.append("sparse_observation")
    if (
        evidence_richness < 58
        and comparable_field_count < 12
        and (rendering_cov < 0.25 or structural_cov < 0.35)
    ):
        flags.append("too_partial_for_identity")
    if (
        evidence_richness < 45
        and comparable_field_count < 9
        and (rendering_cov < 0.18 or structural_cov < 0.25)
    ):
        flags.append("too_incomplete_for_identity")

    if "low_comparable_fields" in flags:
        insufficiency_risk += 0.12
    if "missing_key_families" in flags:
        insufficiency_risk += 0.10
    if "entropy_family_absent" in flags:
        insufficiency_risk += 0.15
    if "structural_family_absent" in flags:
        insufficiency_risk += 0.12
    if "thin_software_family" in flags:
        insufficiency_risk += 0.08
    if "sparse_observation" in flags:
        insufficiency_risk += 0.12
    if "too_partial_for_identity" in flags:
        insufficiency_risk += 0.18
    if "too_incomplete_for_identity" in flags:
        insufficiency_risk += 0.20

    return _clamp_01(insufficiency_risk), flags


def _compute_collision_risk(
    commonness_score: float,
    distinctiveness_score: float,
    evidence_richness: float,
    policy_flags: List[str],
) -> float:
    """
    Compute 0-1 collision risk used by trust adjustment and collision caps.

    Design goals:
    - commonness starts biting around 50 and becomes strong by ~75
    - risk rises mostly in clearly collision-prone combinations
    - policy flags can push risk into cap territory
    """
    # Steeper/nonlinear commonness ramp: 0 below 50, near 1 by 75.
    commonness_linear = _clamp_01((commonness_score - 50.0) / 25.0)
    commonness_factor = commonness_linear ** 2

    # Low distinctiveness only starts to matter meaningfully below ~50.
    low_distinctiveness_linear = _clamp_01((50.0 - distinctiveness_score) / 25.0)
    low_distinctiveness = low_distinctiveness_linear ** 2

    # Rich evidence should amplify risk only once richness is clearly high.
    richness_factor = _clamp_01((evidence_richness - 70.0) / 20.0)

    collision_risk = (
        0.45 * commonness_factor
        + 0.35 * low_distinctiveness
        + 0.20 * richness_factor
    )

    if "high_commonness_profile" in policy_flags:
        collision_risk += 0.15
    if "entropy_standardized" in policy_flags:
        collision_risk += 0.20
    if "rich_but_common" in policy_flags:
        collision_risk += 0.15

    return _clamp_01(collision_risk)


def _apply_trust_adjustment_to_profiles(
    raw_profile_scores: Dict[str, float],
    collision_risk: float,
    insufficiency_risk: float,
) -> Dict[str, float]:
    """
    Convert raw profile similarity into trust-adjusted identity confidence.
    """
    adjusted_scores: Dict[str, float] = {}
    collision = _clamp_01(collision_risk)
    insufficiency = _clamp_01(insufficiency_risk)

    # Collision remains penalty-like.
    profile_collision_penalty_strength = {
        "same_instance": 0.30,
        "same_environment": 0.36,
        "same_device": 0.44,
        "same_entity": 0.58,
    }

    # Insufficiency is moderation-like: pull confidence toward a profile midpoint.
    profile_uncertainty_pull_strength = {
        "same_instance": 0.60,
        "same_environment": 0.72,
        "same_device": 0.84,
        "same_entity": 0.95,
    }
    profile_uncertainty_midpoint = {
        "same_instance": 58.0,
        "same_environment": 56.0,
        "same_device": 54.0,
        "same_entity": 52.0,
    }

    # Strong insufficiency should constrain decisiveness around the midpoint band.
    profile_uncertainty_min_half_band = {
        "same_instance": 12.0,
        "same_environment": 10.0,
        "same_device": 9.0,
        "same_entity": 8.0,
    }
    profile_uncertainty_max_half_band = {
        "same_instance": 46.0,
        "same_environment": 42.0,
        "same_device": 38.0,
        "same_entity": 34.0,
    }

    profile_collision_threshold = {
        "same_instance": 0.90,
        "same_environment": 0.82,
        "same_device": 0.74,
        "same_entity": 0.65,
    }
    profile_collision_cap = {
        "same_instance": 84.0,
        "same_environment": 78.0,
        "same_device": 72.0,
        "same_entity": 64.0,
    }
    profile_hard_collision_cap = {
        "same_instance": 78.0,
        "same_environment": 72.0,
        "same_device": 66.0,
        "same_entity": 58.0,
    }

    for profile_name, raw_score in raw_profile_scores.items():
        collision_strength = profile_collision_penalty_strength.get(profile_name, 0.42)
        collision_effect = collision ** 1.10
        collision_penalty_fraction = _clamp_01(min(0.88, collision_strength * collision_effect))
        adjusted = raw_score * (1.0 - collision_penalty_fraction)

        collision_threshold = profile_collision_threshold.get(profile_name, 0.75)
        if collision >= collision_threshold:
            adjusted = min(adjusted, profile_collision_cap.get(profile_name, 72.0))
        if collision >= 0.90:
            adjusted = min(adjusted, profile_hard_collision_cap.get(profile_name, 66.0))

        # Moderation path: pull score toward midpoint as insufficiency rises.
        insufficiency_effect = insufficiency ** 1.15
        midpoint = profile_uncertainty_midpoint.get(profile_name, 54.0)
        pull_strength = profile_uncertainty_pull_strength.get(profile_name, 0.84) * insufficiency_effect
        pull_strength = _clamp_01(pull_strength)
        adjusted = adjusted + (midpoint - adjusted) * pull_strength

        # As insufficiency increases, compress outputs into a narrower uncertainty band.
        min_half_band = profile_uncertainty_min_half_band.get(profile_name, 9.0)
        max_half_band = profile_uncertainty_max_half_band.get(profile_name, 38.0)
        half_band = min_half_band + (max_half_band - min_half_band) * (1.0 - insufficiency_effect)
        lower = midpoint - half_band
        upper = midpoint + half_band
        adjusted = max(lower, min(upper, adjusted))

        adjusted_scores[profile_name] = _clamp_0_100(adjusted)

    return adjusted_scores


def _evaluate_uncertainty_policy(
    final_score: float,
    insufficiency_risk_score: float,
    decision_threshold: float,
    uncertainty_band: float,
) -> Tuple[bool, str, str, float, List[str]]:
    """
    Determine whether the score should be treated as ordinary, low-confidence,
    uncertain-zone, or abstain-worthy.
    """
    insuff = _clamp_0_100(insufficiency_risk_score)
    distance = abs(final_score - decision_threshold)
    near = distance <= uncertainty_band
    near_wide = distance <= (uncertainty_band * 1.5)

    flags: List[str] = []
    if insuff >= 60.0:
        flags.append("low_confidence_by_insufficiency")
    if near and insuff >= 60.0:
        flags.append("near_threshold_under_insufficiency")

    if insuff >= 92.0:
        flags.append("abstain_recommended")
        return True, "abstain", "abstain", distance, flags
    if insuff >= 75.0 and near_wide:
        flags.append("review_recommended")
        return True, "uncertain_zone", "review", distance, flags
    if insuff >= 60.0 and near:
        flags.append("challenge_recommended")
        return True, "uncertain_zone", "challenge", distance, flags
    if insuff >= 75.0:
        flags.append("review_recommended")
        return False, "low_confidence", "review", distance, flags
    if insuff >= 60.0:
        return False, "low_confidence", "low_confidence", distance, flags
    return False, "ordinary", "normal", distance, flags


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

    # Raw profile scores (before trust/commonness adjustment)
    raw_profile_scores: Dict[str, float] = {}
    for profile_name, weights in PROFILE_WEIGHTS.items():
        pairs: List[Tuple[float, float]] = []
        for family in FAMILY_NAMES:
            family_weight = weights.get(family, 0.0)
            if family_weight > 0:
                pairs.append((family_effective_scores[family], family_weight))
        richness_weight = weights.get("richness", 0.0)
        if richness_weight > 0:
            pairs.append((evidence_richness, richness_weight))

        raw_profile_scores[profile_name] = _weighted_mean(pairs)

    commonness_score, distinctiveness_score, commonness_flags = _compute_commonness_and_flags(
        attractor_risk=attractor_risk,
        evidence_richness=evidence_richness,
        entropy_contribution=entropy_contribution,
        family_similarities=family_similarities,
        family_coverages=family_coverages,
    )
    insufficiency_risk, insufficiency_flags = _compute_insufficiency_risk_and_flags(
        evidence_richness=evidence_richness,
        comparable_field_count=comparable_fields,
        family_coverages=family_coverages,
    )
    policy_flags: List[str] = []
    for flag in [*commonness_flags, *insufficiency_flags]:
        if flag not in policy_flags:
            policy_flags.append(flag)

    collision_risk = _compute_collision_risk(
        commonness_score=commonness_score,
        distinctiveness_score=distinctiveness_score,
        evidence_richness=evidence_richness,
        policy_flags=commonness_flags,
    )
    profile_scores = _apply_trust_adjustment_to_profiles(
        raw_profile_scores=raw_profile_scores,
        collision_risk=collision_risk,
        insufficiency_risk=insufficiency_risk,
    )

    if primary_profile not in profile_scores:
        primary_profile = "same_device"
    overall = profile_scores[primary_profile]
    raw_primary = raw_profile_scores.get(primary_profile, overall)
    trust_shift = overall - raw_primary
    trust_adjustment = abs(trust_shift)
    uncertainty_zone, confidence_label, policy_action, threshold_distance, uncertainty_flags = (
        _evaluate_uncertainty_policy(
            final_score=overall,
            insufficiency_risk_score=insufficiency_risk * 100.0,
            decision_threshold=decision_threshold,
            uncertainty_band=uncertainty_band,
        )
    )
    for flag in uncertainty_flags:
        if flag not in policy_flags:
            policy_flags.append(flag)

    # Sort matches by contribution (highest first)
    matches.sort(key=lambda m: m.contribution, reverse=True)
    top_matches = matches[:top_n]

    # Sort disagreements by penalty (highest first)
    disagreements.sort(key=lambda d: d.penalty, reverse=True)
    top_disagreements = disagreements[:top_n]

    return ScoreBreakdown(
        device_similarity=device_similarity,
        raw_similarity_score=raw_primary,
        commonness_score=commonness_score,
        distinctiveness_score=distinctiveness_score,
        collision_risk=collision_risk * 100.0,
        insufficiency_risk=insufficiency_risk * 100.0,
        trust_adjustment=trust_adjustment,
        trust_shift=trust_shift,
        uncertainty_zone=uncertainty_zone,
        confidence_label=confidence_label,
        policy_action=policy_action,
        decision_threshold=decision_threshold,
        threshold_distance=threshold_distance,
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
        raw_profile_scores=raw_profile_scores,
        policy_flags=policy_flags,
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

from typing import Any, Dict, List

from data_generator import LabeledFingerprint, generate_dataset, mutate, create_base_fingerprint
from metrics import ScoredPair, calculate_metrics, calculate_true_eer

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
    raw_profile_scores = breakdown.raw_profile_scores
    return {
        "legacyScore": float(calculate_confidence(left.data, right.data)),
        "breakdownScore": float(profile_scores.get("same_device", breakdown.overall_confidence)),
        "raw_breakdownScore": float(raw_profile_scores.get("same_device", breakdown.raw_similarity_score)),
        "raw_overall": float(breakdown.raw_similarity_score),
        "trust_adjustment": float(breakdown.trust_adjustment),
        "trust_shift": float(breakdown.trust_shift),
        "collision_risk": float(breakdown.collision_risk),
        "insufficiency_risk": float(breakdown.insufficiency_risk),
        "uncertainty_zone": bool(breakdown.uncertainty_zone),
        "confidence_label": str(breakdown.confidence_label),
        "policy_action": str(breakdown.policy_action),
        "commonness": float(breakdown.commonness_score),
        "distinctiveness": float(breakdown.distinctiveness_score),
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
        "raw_same_device": calculate_metrics(_as_metric_inputs(pairs, "raw_breakdownScore")),
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
                "raw_device_f1": metrics_by_score["raw_same_device"][index].f1,
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
                "raw_device_gap": metrics_by_score["raw_same_device"][index].far_frr_gap,
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
                "raw_device_mean": _average([float(p["raw_breakdownScore"]) for p in bucket]),
                "same_instance_mean": _average([float(p["same_instance"]) for p in bucket]),
                "same_environment_mean": _average([float(p["same_environment"]) for p in bucket]),
                "same_device_mean": _average([float(p["same_device"]) for p in bucket]),
                "same_entity_mean": _average([float(p["same_entity"]) for p in bucket]),
                "commonness_mean": _average([float(p["commonness"]) for p in bucket]),
                "distinctiveness_mean": _average([float(p["distinctiveness"]) for p in bucket]),
                "collision_risk_mean": _average([float(p["collision_risk"]) for p in bucket]),
                "insufficiency_risk_mean": _average([float(p["insufficiency_risk"]) for p in bucket]),
                "trust_adjustment_mean": _average([float(p["trust_adjustment"]) for p in bucket]),
                "trust_shift_mean": _average([float(p["trust_shift"]) for p in bucket]),
                "uncertainty_zone_pct": _average(
                    [100.0 if bool(p["uncertainty_zone"]) else 0.0 for p in bucket]
                ),
                "low_confidence_pct": _average(
                    [100.0 if str(p["confidence_label"]) != "ordinary" else 0.0 for p in bucket]
                ),
                "richness_mean": _average([float(p["evidenceRichness"]) for p in bucket]),
                "attractor_risk_mean": _average([float(p["attractorRisk"]) for p in bucket]),
            }
        )

    cohort_rows.append(
        {
            "cohort": "separation(same-diff)",
            "pairs": "-",
            "legacy_mean": cohort_rows[0]["legacy_mean"] - cohort_rows[1]["legacy_mean"],
            "raw_device_mean": cohort_rows[0]["raw_device_mean"] - cohort_rows[1]["raw_device_mean"],
            "same_instance_mean": cohort_rows[0]["same_instance_mean"] - cohort_rows[1]["same_instance_mean"],
            "same_environment_mean": cohort_rows[0]["same_environment_mean"] - cohort_rows[1]["same_environment_mean"],
            "same_device_mean": cohort_rows[0]["same_device_mean"] - cohort_rows[1]["same_device_mean"],
            "same_entity_mean": cohort_rows[0]["same_entity_mean"] - cohort_rows[1]["same_entity_mean"],
            "commonness_mean": cohort_rows[0]["commonness_mean"] - cohort_rows[1]["commonness_mean"],
            "distinctiveness_mean": cohort_rows[0]["distinctiveness_mean"] - cohort_rows[1]["distinctiveness_mean"],
            "collision_risk_mean": cohort_rows[0]["collision_risk_mean"] - cohort_rows[1]["collision_risk_mean"],
            "insufficiency_risk_mean": cohort_rows[0]["insufficiency_risk_mean"] - cohort_rows[1]["insufficiency_risk_mean"],
            "trust_adjustment_mean": cohort_rows[0]["trust_adjustment_mean"] - cohort_rows[1]["trust_adjustment_mean"],
            "trust_shift_mean": cohort_rows[0]["trust_shift_mean"] - cohort_rows[1]["trust_shift_mean"],
            "uncertainty_zone_pct": cohort_rows[0]["uncertainty_zone_pct"] - cohort_rows[1]["uncertainty_zone_pct"],
            "low_confidence_pct": cohort_rows[0]["low_confidence_pct"] - cohort_rows[1]["low_confidence_pct"],
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
    for name in ["legacy", "raw_same_device", "same_instance", "same_environment", "same_device", "same_entity"]:
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
