from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .hashing import canonicalized_stringify, compare_hashes, get_hash
from .registry import get_global_registry
from ..types import Comparator, ComparisonOptions, FPDataSet


DEFAULT_WEIGHTS: Dict[str, float] = {
    "userAgent": 10,
    "platform": 20,
    "timezone": 10,
    "language": 15,
    "languages": 20,
    "cookieEnabled": 5,
    "doNotTrack": 5,
    "hardwareConcurrency": 5,
    "deviceMemory": 5,
    "product": 5,
    "productSub": 5,
    "vendor": 5,
    "vendorSub": 5,
    "appName": 5,
    "appVersion": 5,
    "appCodeName": 5,
    "appMinorVersion": 5,
    "buildID": 5,
    "plugins": 15,
    "mimeTypes": 15,
    "screen": 10,
    "fonts": 15,
    "canvas": 30,
    "webgl": 25,
    "audio": 25,
    "highEntropyValues": 20,
}

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

PROFILE_FIELD_WEIGHTS: Dict[str, float] = {
    "canvas": 0.10,
    "webgl": 0.0875,
    "audio": 0.0625,
    "screen.width": 0.10,
    "screen.height": 0.10,
    "screen.colorDepth": 0.04,
    "screen.pixelDepth": 0.03,
    "hardwareConcurrency": 0.06,
    "deviceMemory": 0.05,
    "fonts": 0.06,
    "plugins": 0.03,
    "mimeTypes": 0.02,
    "platform": 0.04,
    "userAgent": 0.03,
    "appVersion": 0.02,
    "highEntropyValues": 0.04,
    "timezone": 0.03,
    "language": 0.02,
    "languages": 0.02,
    "_default": 0.005,
}

PROFILE_FAMILY_WEIGHTS: Dict[str, Dict[str, float]] = {
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

FAMILY_COVERAGE_INFLUENCE = 0.30
DEFAULT_DECISION_THRESHOLD = 65.0
DEFAULT_UNCERTAINTY_BAND = 8.0

STRUCTURAL_FIELDS = {
    "screen.width",
    "screen.height",
    "screen.colorDepth",
    "screen.pixelDepth",
    "hardwareConcurrency",
    "deviceMemory",
    "platform",
    "timezone",
}

ENTROPY_FIELDS = {"canvas", "webgl", "audio"}

ATTRACTOR_PATTERNS = [
    {"platform": "Win32", "userAgent": "Chrome"},
    {"platform": "MacIntel", "userAgent": "Safari"},
    {"platform": "iPhone", "deviceMemory": 8},
    {"platform": "Linux armv8l", "userAgent": "Chrome"},
]

PROFILE_NAMES = set(PROFILE_FAMILY_WEIGHTS.keys())


def _default_comparator(a: Any, b: Any, _path: Optional[str] = None) -> float:
    return 1.0 if a == b else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _clamp_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _weighted_mean(pairs: List[Tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        return 0.0
    return sum(value * weight for value, weight in pairs) / total_weight


def _coverage_damped_similarity(similarity: float, coverage: float) -> float:
    alpha = _clamp01(FAMILY_COVERAGE_INFLUENCE)
    return similarity * ((1.0 - alpha) + alpha * coverage)


def _apply_gentle_attractor_penalty(score: float, attractor_risk: float, evidence_richness: float) -> float:
    risk = _clamp_0_100(attractor_risk) / 100.0
    richness = _clamp_0_100(evidence_richness) / 100.0
    penalty_points = 8.0 * risk * (1.0 - richness)
    return max(0.0, score - penalty_points)


def _calculate_jaccard_similarity(set_a: Set[Any], set_b: Set[Any]) -> float:
    if not set_a and not set_b:
        return 100.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return (intersection / union * 100.0) if union > 0 else 0.0


def _to_hashable(value: Any) -> Any:
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


def _calculate_string_similarity(value_a: str, value_b: str) -> float:
    if value_a == value_b:
        return 100.0
    if not value_a or not value_b:
        return 0.0
    set_a = set(value_a.lower())
    set_b = set(value_b.lower())
    return _calculate_jaccard_similarity(set_a, set_b)


def _compare_generic_values(value_a: Any, value_b: Any) -> float:
    if value_a == value_b:
        return 100.0
    if value_a is None or value_b is None:
        return 0.0

    if isinstance(value_a, list) and isinstance(value_b, list):
        set_a = {_to_hashable(item) for item in value_a}
        set_b = {_to_hashable(item) for item in value_b}
        return _calculate_jaccard_similarity(set_a, set_b)

    if isinstance(value_a, dict) and isinstance(value_b, dict):
        keys_a = set(value_a.keys())
        keys_b = set(value_b.keys())
        common_keys = keys_a & keys_b
        if not common_keys:
            return 0.0
        matches = sum(1 for key in common_keys if value_a[key] == value_b[key])
        return (matches / len(common_keys)) * 100.0

    if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
        avg = (abs(value_a) + abs(value_b)) / 2
        if avg == 0:
            return 100.0
        diff_pct = abs(value_a - value_b) / avg * 100.0
        return max(0.0, 100.0 - diff_pct)

    if isinstance(value_a, str) and isinstance(value_b, str):
        return _calculate_string_similarity(value_a, value_b)

    return 0.0


def _get_field_family(field_name: str) -> str:
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


def _flatten_fingerprint(fp: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    flattened: Dict[str, Any] = {}
    for key, value in fp.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and key != "highEntropyValues":
            flattened.update(_flatten_fingerprint(value, full_key))
        else:
            flattened[full_key] = value
    return flattened


def _calculate_attractor_risk(fp: Dict[str, Any]) -> float:
    risk_score = 0.0
    for pattern in ATTRACTOR_PATTERNS:
        matches = all(
            str(fp.get(key, "")).find(str(val)) >= 0
            for key, val in pattern.items()
        )
        if matches:
            risk_score += 30.0

    generic_markers = {
        "platform": ["Win32", "MacIntel"],
        "deviceMemory": [8, 16],
        "hardwareConcurrency": [4, 8],
        "language": ["en-US"],
    }
    for field_name, generic_values in generic_markers.items():
        if fp.get(field_name) in generic_values:
            risk_score += 10.0

    fonts = fp.get("fonts", [])
    if isinstance(fonts, list) and len(fonts) < 8:
        risk_score += 15.0

    return _clamp_0_100(risk_score)


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
    rendering_cov = _clamp01(family_coverages.get(FAMILY_RENDERING, 0.0))
    structural_cov = _clamp01(family_coverages.get(FAMILY_STRUCTURAL, 0.0))
    software_cov = _clamp01(family_coverages.get(FAMILY_SOFTWARE, 0.0))
    locale_cov = _clamp01(family_coverages.get(FAMILY_LOCALE, 0.0))

    richness_shortfall = _clamp01((74.0 - evidence_richness) / 40.0)
    comparable_shortfall = _clamp01((14.0 - float(comparable_field_count)) / 9.0)
    structural_absence = _clamp01((0.55 - structural_cov) / 0.55)
    rendering_absence = _clamp01((0.40 - rendering_cov) / 0.40)
    software_absence = _clamp01((0.50 - software_cov) / 0.50)
    key_family_absence = (
        0.45 * structural_absence
        + 0.40 * rendering_absence
        + 0.15 * software_absence
    )
    weak_context = _clamp01((0.45 - locale_cov) / 0.45)

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

    return _clamp01(insufficiency_risk), flags


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
    commonness_linear = _clamp01((commonness_score - 50.0) / 25.0)
    commonness_factor = commonness_linear ** 2

    low_distinctiveness_linear = _clamp01((50.0 - distinctiveness_score) / 25.0)
    low_distinctiveness = low_distinctiveness_linear ** 2

    richness_factor = _clamp01((evidence_richness - 70.0) / 20.0)

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

    return _clamp01(collision_risk)


def _apply_trust_adjustment_to_profiles(
    raw_profile_scores: Dict[str, float],
    collision_risk: float,
    insufficiency_risk: float,
) -> Dict[str, float]:
    """
    Convert raw profile similarity into trust-adjusted identity confidence.
    """
    adjusted_scores: Dict[str, float] = {}
    collision = _clamp01(collision_risk)
    insufficiency = _clamp01(insufficiency_risk)

    profile_collision_penalty_strength = {
        "same_instance": 0.30,
        "same_environment": 0.36,
        "same_device": 0.44,
        "same_entity": 0.58,
    }

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
        collision_penalty_fraction = _clamp01(min(0.88, collision_strength * collision_effect))
        adjusted = raw_score * (1.0 - collision_penalty_fraction)

        collision_threshold = profile_collision_threshold.get(profile_name, 0.75)
        if collision >= collision_threshold:
            adjusted = min(adjusted, profile_collision_cap.get(profile_name, 72.0))
        if collision >= 0.90:
            adjusted = min(adjusted, profile_hard_collision_cap.get(profile_name, 66.0))

        insufficiency_effect = insufficiency ** 1.15
        midpoint = profile_uncertainty_midpoint.get(profile_name, 54.0)
        pull_strength = profile_uncertainty_pull_strength.get(profile_name, 0.84) * insufficiency_effect
        pull_strength = _clamp01(pull_strength)
        adjusted = adjusted + (midpoint - adjusted) * pull_strength

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
    threshold = _clamp_0_100(decision_threshold)
    band = max(0.0, uncertainty_band)
    distance = abs(final_score - threshold)
    near = distance <= band
    near_wide = distance <= (band * 1.5)

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


@dataclass(frozen=True)
class FamilyScore:
    similarity: float
    coverage: float
    effective: float
    comparable_weight: float
    total_weight: float


@dataclass(frozen=True)
class ConfidenceBreakdown:
    primary_profile: str
    overall_confidence: float
    profile_scores: Dict[str, float]
    family_scores: Dict[str, FamilyScore]
    evidence_richness: float
    field_agreement: float
    structural_stability: float
    entropy_contribution: float
    attractor_risk: float
    device_similarity: float
    total_fields_compared: int
    one_side_missing_fields: int
    both_side_missing_fields: int
    raw_similarity_score: float = 0.0
    commonness_score: float = 0.0
    distinctiveness_score: float = 100.0
    collision_risk: float = 0.0
    insufficiency_risk: float = 0.0
    trust_adjustment: float = 0.0
    trust_shift: float = 0.0
    uncertainty_zone: bool = False
    confidence_label: str = "ordinary"
    policy_action: str = "normal"
    decision_threshold: float = DEFAULT_DECISION_THRESHOLD
    threshold_distance: float = 0.0
    raw_profile_scores: Dict[str, float] = field(default_factory=dict)
    policy_flags: List[str] = field(default_factory=list)
    family_similarities: Dict[str, float] = field(default_factory=dict)
    family_coverages: Dict[str, float] = field(default_factory=dict)
    family_effective_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConfidenceCalculator:
    options: ComparisonOptions

    def __post_init__(self) -> None:
        local_weights = dict(self.options.weights or {})
        local_comparators = self.options.comparators or {}
        self.local_weights = local_weights
        if self.options.use_global_registry:
            global_registry = get_global_registry()
            self.weights = {**global_registry.weights, **DEFAULT_WEIGHTS, **local_weights}
            self.comparators = {**global_registry.comparators, **local_comparators}
            self.default_weight = self.options.default_weight or global_registry.default_weight
        else:
            self.weights = {**DEFAULT_WEIGHTS, **local_weights}
            self.comparators = dict(local_comparators)
            self.default_weight = self.options.default_weight

    def _get_weight(self, path: str) -> float:
        return float(self.weights.get(path, self.default_weight))

    def _get_profile_weight(self, path: str) -> float:
        if path in self.local_weights:
            return float(self.local_weights[path])
        return float(PROFILE_FIELD_WEIGHTS.get(path, PROFILE_FIELD_WEIGHTS["_default"]))

    def _get_comparator(self, path: str) -> Comparator:
        return self.comparators.get(path, _default_comparator)

    def _compare_recursive(self, value1: Any, value2: Any, path: str = "", depth: int = 0) -> Tuple[float, float]:
        if depth > self.options.max_depth:
            return 0.0, 0.0
        if value1 is None or value2 is None:
            return 0.0, 0.0

        if not isinstance(value1, (dict, list)) or not isinstance(value2, (dict, list)):
            comparator = self._get_comparator(path)
            similarity = max(0.0, min(1.0, float(comparator(value1, value2, path))))
            weight = self._get_weight(path)
            return weight, weight * similarity

        if isinstance(value1, list) and isinstance(value2, list):
            total = 0.0
            matched = 0.0
            for index in range(min(len(value1), len(value2))):
                child_path = f"{path}[{index}]"
                child_total, child_matched = self._compare_recursive(value1[index], value2[index], child_path, depth + 1)
                total += child_total
                matched += child_matched
            return total, matched

        if isinstance(value1, dict) and isinstance(value2, dict):
            total = 0.0
            matched = 0.0
            keys = set(value1.keys()).union(set(value2.keys()))
            for key in keys:
                child_path = f"{path}.{key}" if path else str(key)
                child_total, child_matched = self._compare_recursive(value1.get(key), value2.get(key), child_path, depth + 1)
                total += child_total
                matched += child_matched
            return total, matched

        return 0.0, 0.0

    def _compare_profile_field(self, path: str, value1: Any, value2: Any) -> float:
        comparator = self.comparators.get(path)
        if comparator is not None:
            try:
                return _clamp_0_100(float(comparator(value1, value2, path)) * 100.0)
            except Exception:
                pass
        return _compare_generic_values(value1, value2)

    def calculate_confidence_breakdown(
        self,
        data1: FPDataSet,
        data2: FPDataSet,
        primary_profile: str = "same_device",
        decision_threshold: float = DEFAULT_DECISION_THRESHOLD,
        uncertainty_band: float = DEFAULT_UNCERTAINTY_BAND,
    ) -> ConfidenceBreakdown:
        if primary_profile not in PROFILE_NAMES:
            primary_profile = "same_device"

        flat1 = _flatten_fingerprint(data1)
        flat2 = _flatten_fingerprint(data2)

        weighted_fields = set(PROFILE_FIELD_WEIGHTS.keys()) - {"_default"}
        all_fields = set(flat1.keys()) | set(flat2.keys()) | weighted_fields

        comparable_fields = 0
        matching_fields = 0
        one_side_missing_fields = 0
        both_side_missing_fields = 0

        structural_pairs: List[Tuple[float, float]] = []
        entropy_pairs: List[Tuple[float, float]] = []

        total_weight = 0.0
        comparable_weight = 0.0
        family_total_weight = {name: 0.0 for name in FAMILY_NAMES}
        family_comparable_weight = {name: 0.0 for name in FAMILY_NAMES}
        family_weighted_similarity = {name: 0.0 for name in FAMILY_NAMES}

        for field_name in sorted(all_fields):
            value1 = flat1.get(field_name)
            value2 = flat2.get(field_name)

            weight = self._get_profile_weight(field_name)
            family = _get_field_family(field_name)
            total_weight += weight
            family_total_weight[family] += weight

            if value1 is None and value2 is None:
                both_side_missing_fields += 1
                continue
            if value1 is None or value2 is None:
                one_side_missing_fields += 1
                continue

            comparable_fields += 1
            comparable_weight += weight
            family_comparable_weight[family] += weight

            similarity = self._compare_profile_field(field_name, value1, value2)
            family_weighted_similarity[family] += similarity * weight

            if field_name in STRUCTURAL_FIELDS:
                structural_pairs.append((similarity, weight))
            if field_name in ENTROPY_FIELDS:
                entropy_pairs.append((similarity, weight))
            if similarity >= 90:
                matching_fields += 1

        family_scores: Dict[str, FamilyScore] = {}
        family_similarities: Dict[str, float] = {}
        family_coverages: Dict[str, float] = {}
        family_effective_scores: Dict[str, float] = {}
        for family in FAMILY_NAMES:
            family_total = family_total_weight[family]
            family_comparable = family_comparable_weight[family]
            similarity = (
                family_weighted_similarity[family] / family_comparable
                if family_comparable > 0
                else 0.0
            )
            coverage = (family_comparable / family_total) if family_total > 0 else 0.0
            effective = _coverage_damped_similarity(similarity, coverage)

            family_similarities[family] = _clamp_0_100(similarity)
            family_coverages[family] = _clamp01(coverage)
            family_effective_scores[family] = _clamp_0_100(effective)

            family_scores[family] = FamilyScore(
                similarity=round(_clamp_0_100(similarity), 3),
                coverage=round(_clamp_0_100(coverage * 100.0), 3),
                effective=round(_clamp_0_100(effective), 3),
                comparable_weight=round(family_comparable, 6),
                total_weight=round(family_total, 6),
            )

        evidence_richness = (comparable_weight / total_weight * 100.0) if total_weight > 0 else 0.0
        field_agreement = (matching_fields / comparable_fields * 100.0) if comparable_fields > 0 else 0.0
        structural_stability = _weighted_mean(structural_pairs)
        entropy_contribution = _weighted_mean(entropy_pairs)

        device_similarity = _weighted_mean(
            [
                (family_effective_scores[FAMILY_RENDERING], 0.30),
                (family_effective_scores[FAMILY_STRUCTURAL], 0.45),
                (family_effective_scores[FAMILY_SOFTWARE], 0.20),
                (family_effective_scores[FAMILY_LOCALE], 0.05),
            ]
        )

        attractor_risk = (_calculate_attractor_risk(data1) + _calculate_attractor_risk(data2)) / 2.0

        raw_profile_scores: Dict[str, float] = {}
        for profile_name, weights in PROFILE_FAMILY_WEIGHTS.items():
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

        return ConfidenceBreakdown(
            primary_profile=primary_profile,
            overall_confidence=round(_clamp_0_100(overall), 3),
            profile_scores={name: round(_clamp_0_100(score), 3) for name, score in profile_scores.items()},
            family_scores=family_scores,
            evidence_richness=round(_clamp_0_100(evidence_richness), 3),
            field_agreement=round(_clamp_0_100(field_agreement), 3),
            structural_stability=round(_clamp_0_100(structural_stability), 3),
            entropy_contribution=round(_clamp_0_100(entropy_contribution), 3),
            attractor_risk=round(_clamp_0_100(attractor_risk), 3),
            device_similarity=round(_clamp_0_100(device_similarity), 3),
            total_fields_compared=comparable_fields,
            one_side_missing_fields=one_side_missing_fields,
            both_side_missing_fields=both_side_missing_fields,
            raw_similarity_score=round(_clamp_0_100(raw_primary), 3),
            commonness_score=round(_clamp_0_100(commonness_score), 3),
            distinctiveness_score=round(_clamp_0_100(distinctiveness_score), 3),
            collision_risk=round(_clamp_0_100(collision_risk * 100.0), 3),
            insufficiency_risk=round(_clamp_0_100(insufficiency_risk * 100.0), 3),
            trust_adjustment=round(_clamp_0_100(trust_adjustment), 3),
            trust_shift=round(trust_shift, 3),
            uncertainty_zone=uncertainty_zone,
            confidence_label=confidence_label,
            policy_action=policy_action,
            decision_threshold=round(_clamp_0_100(decision_threshold), 3),
            threshold_distance=round(max(0.0, threshold_distance), 3),
            raw_profile_scores={
                name: round(_clamp_0_100(score), 3)
                for name, score in raw_profile_scores.items()
            },
            policy_flags=policy_flags,
            family_similarities={
                name: round(_clamp_0_100(score), 3)
                for name, score in family_similarities.items()
            },
            family_coverages={
                name: round(_clamp01(score), 6)
                for name, score in family_coverages.items()
            },
            family_effective_scores={
                name: round(_clamp_0_100(score), 3)
                for name, score in family_effective_scores.items()
            },
        )

    def calculate_profile_confidence(
        self,
        data1: FPDataSet,
        data2: FPDataSet,
        profile: str = "same_device",
    ) -> int:
        breakdown = self.calculate_confidence_breakdown(data1, data2, primary_profile=profile)
        return int(round(_clamp_0_100(breakdown.overall_confidence)))

    def calculate_confidence(self, data1: FPDataSet, data2: FPDataSet, profile: Optional[str] = None) -> int:
        if profile is not None:
            return self.calculate_profile_confidence(data1, data2, profile=profile)

        total_weight, matched_weight = self._compare_recursive(data1, data2)
        structural_score = matched_weight / total_weight if total_weight > 0 else 0.0

        tlsh_score = 1.0
        tlsh_weight = max(0.0, min(1.0, self.options.tlsh_weight))
        if tlsh_weight > 0:
            tlsh_max_distance = 300
            hash1 = get_hash(canonicalized_stringify(data1))
            hash2 = get_hash(canonicalized_stringify(data2))
            difference = compare_hashes(hash1, hash2)
            tlsh_score = max(0.0, (tlsh_max_distance - difference) / tlsh_max_distance)

        final_score = structural_score * (1.0 - tlsh_weight) + tlsh_score * tlsh_weight
        return round(max(0.0, min(100.0, final_score * 100.0)))


def create_confidence_calculator(user_options: Optional[ComparisonOptions] = None) -> ConfidenceCalculator:
    return ConfidenceCalculator(options=user_options or ComparisonOptions())


def calculate_confidence(data1: FPDataSet, data2: FPDataSet, profile: Optional[str] = None) -> int:
    return create_confidence_calculator().calculate_confidence(data1, data2, profile=profile)


def calculate_confidence_profile(data1: FPDataSet, data2: FPDataSet, profile: str = "same_device") -> int:
    return create_confidence_calculator().calculate_profile_confidence(data1, data2, profile=profile)


def calculate_confidence_breakdown(
    data1: FPDataSet,
    data2: FPDataSet,
    primary_profile: str = "same_device",
    decision_threshold: float = DEFAULT_DECISION_THRESHOLD,
    uncertainty_band: float = DEFAULT_UNCERTAINTY_BAND,
) -> ConfidenceBreakdown:
    return create_confidence_calculator().calculate_confidence_breakdown(
        data1,
        data2,
        primary_profile=primary_profile,
        decision_threshold=decision_threshold,
        uncertainty_band=uncertainty_band,
    )
