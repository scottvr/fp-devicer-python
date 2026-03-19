from __future__ import annotations

from dataclasses import dataclass
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
    for field, generic_values in generic_markers.items():
        if fp.get(field) in generic_values:
            risk_score += 10.0

    fonts = fp.get("fonts", [])
    if isinstance(fonts, list) and len(fonts) < 8:
        risk_score += 15.0

    return _clamp_0_100(risk_score)


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

        for field in sorted(all_fields):
            value1 = flat1.get(field)
            value2 = flat2.get(field)

            weight = self._get_profile_weight(field)
            family = _get_field_family(field)
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

            similarity = self._compare_profile_field(field, value1, value2)
            family_weighted_similarity[family] += similarity * weight

            if field in STRUCTURAL_FIELDS:
                structural_pairs.append((similarity, weight))
            if field in ENTROPY_FIELDS:
                entropy_pairs.append((similarity, weight))
            if similarity >= 90:
                matching_fields += 1

        family_scores: Dict[str, FamilyScore] = {}
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
            family_scores[family] = FamilyScore(
                similarity=round(_clamp_0_100(similarity), 3),
                coverage=round(_clamp_0_100(coverage * 100.0), 3),
                effective=round(_clamp_0_100(effective), 3),
                comparable_weight=round(family_comparable, 6),
                total_weight=round(family_total, 6),
            )
            family_effective_scores[family] = effective

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

        profile_scores: Dict[str, float] = {}
        for profile, weights in PROFILE_FAMILY_WEIGHTS.items():
            pairs: List[Tuple[float, float]] = []
            for family in FAMILY_NAMES:
                family_weight = weights.get(family, 0.0)
                if family_weight > 0:
                    pairs.append((family_effective_scores[family], family_weight))
            richness_weight = weights.get("richness", 0.0)
            if richness_weight > 0:
                pairs.append((evidence_richness, richness_weight))
            raw_score = _weighted_mean(pairs)
            profile_scores[profile] = round(
                _apply_gentle_attractor_penalty(raw_score, attractor_risk, evidence_richness),
                3,
            )

        overall_confidence = profile_scores[primary_profile]
        return ConfidenceBreakdown(
            primary_profile=primary_profile,
            overall_confidence=round(overall_confidence, 3),
            profile_scores=profile_scores,
            family_scores=family_scores,
            evidence_richness=round(evidence_richness, 3),
            field_agreement=round(field_agreement, 3),
            structural_stability=round(structural_stability, 3),
            entropy_contribution=round(entropy_contribution, 3),
            attractor_risk=round(attractor_risk, 3),
            device_similarity=round(device_similarity, 3),
            total_fields_compared=comparable_fields,
            one_side_missing_fields=one_side_missing_fields,
            both_side_missing_fields=both_side_missing_fields,
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
) -> ConfidenceBreakdown:
    return create_confidence_calculator().calculate_confidence_breakdown(
        data1,
        data2,
        primary_profile=primary_profile,
    )
