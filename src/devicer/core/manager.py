from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from ..libs.confidence import DEFAULT_WEIGHTS, calculate_confidence, create_confidence_calculator
from ..libs.default_observability import default_logger, default_metrics
from ..libs.hashing import canonicalized_stringify, get_hash
from ..libs.registry import get_global_registry
from ..types import ComparisonOptions, DeviceMatch, FPDataSet, Metrics, StoredFingerprint, StorageAdapter


@dataclass
class IdentifyResult:
    device_id: str
    confidence: float
    is_new_device: bool
    match_confidence: float
    linked_user_id: Optional[str] = None


class DeviceManager:
    def __init__(
        self,
        adapter: StorageAdapter,
        match_threshold: float = 50,
        candidate_min_score: float = 30,
        stability_window_size: int = 5,
        dedup_window_ms: int = 5000,
        confidence_profile: Optional[str] = None,
        logger=default_logger,
        metrics: Metrics = default_metrics,
    ) -> None:
        self.adapter = adapter
        self.match_threshold = match_threshold
        self.candidate_min_score = candidate_min_score
        self.stability_window_size = stability_window_size
        self.dedup_window_ms = dedup_window_ms
        self.confidence_profile = confidence_profile
        self.logger = logger
        self.metrics = metrics
        self._dedup_cache: Dict[str, Tuple[IdentifyResult, float]] = {}

    def _compute_field_stabilities(self, snapshots: List[StoredFingerprint]) -> Dict[str, float]:
        if len(snapshots) < 2:
            return {}
        registry = get_global_registry()
        stabilities: Dict[str, float] = {}
        for field in DEFAULT_WEIGHTS.keys():
            comparator = registry.comparators.get(field, lambda a, b, _p=None: 1.0 if a == b else 0.0)
            total = 0.0
            count = 0
            for index in range(len(snapshots) - 1):
                value1 = snapshots[index].fingerprint.get(field)
                value2 = snapshots[index + 1].fingerprint.get(field)
                if value1 is not None and value2 is not None:
                    total += max(0.0, min(1.0, float(comparator(value1, value2, field))))
                    count += 1
            stabilities[field] = (total / count) if count else 1.0
        return stabilities

    async def identify(self, incoming: FPDataSet, user_id: Optional[str] = None, ip: Optional[str] = None) -> IdentifyResult:
        start = perf_counter()

        cache_key = None
        if self.dedup_window_ms > 0:
            cache_key = get_hash(canonicalized_stringify(incoming))
            cached = self._dedup_cache.get(cache_key)
            if cached and cached[1] > perf_counter() * 1000:
                self.logger.debug("Dedup cache hit", {"cacheKey": cache_key})
                return cached[0]

        candidates = await self.adapter.find_candidates(incoming, self.candidate_min_score, limit=100)
        best_match: Optional[DeviceMatch] = None

        for candidate in candidates:
            history = await self.adapter.get_history(candidate.device_id, self.stability_window_size)
            if not history:
                continue
            history = sorted(history, key=lambda entry: entry.timestamp, reverse=True)

            scorer = calculate_confidence
            if len(history) >= 2:
                stabilities = self._compute_field_stabilities(history)
                adapted_weights = {
                    field: base_weight * stabilities.get(field, 1.0)
                    for field, base_weight in DEFAULT_WEIGHTS.items()
                }
                scorer = create_confidence_calculator(user_options=ComparisonOptions(weights=adapted_weights)).calculate_confidence

            score = scorer(incoming, history[0].fingerprint, self.confidence_profile)
            if best_match is None or score > best_match.confidence:
                best_match = DeviceMatch(
                    device_id=candidate.device_id,
                    confidence=score,
                    last_seen=history[0].timestamp,
                )

        is_matched = best_match is not None and best_match.confidence > self.match_threshold
        device_id = best_match.device_id if is_matched and best_match else f"dev_{uuid4()}"
        is_new_device = not is_matched
        final_confidence = best_match.confidence if best_match else 0.0

        snapshot = StoredFingerprint(
            id=str(uuid4()),
            device_id=device_id,
            user_id=user_id,
            timestamp=datetime.now(UTC),
            fingerprint=incoming,
            ip=ip,
            match_confidence=final_confidence,
        )
        await self.adapter.save(snapshot)
        if user_id:
            await self.adapter.link_to_user(device_id, user_id)

        duration_ms = (perf_counter() - start) * 1000
        self.metrics.record_identify(duration_ms, final_confidence, is_new_device, len(candidates), is_matched)
        self.logger.info(
            "Device identification completed",
            {
                "deviceId": device_id,
                "confidence": final_confidence,
                "isNewDevice": is_new_device,
                "candidates": len(candidates),
            },
        )

        result = IdentifyResult(
            device_id=device_id,
            confidence=final_confidence,
            is_new_device=is_new_device,
            match_confidence=final_confidence,
            linked_user_id=user_id,
        )

        if cache_key and self.dedup_window_ms > 0:
            expires_at = perf_counter() * 1000 + self.dedup_window_ms
            self._dedup_cache[cache_key] = (result, expires_at)

        return result

    async def identify_many(self, incoming_list: List[FPDataSet], user_id: Optional[str] = None, ip: Optional[str] = None) -> List[IdentifyResult]:
        results: List[IdentifyResult] = []
        for incoming in incoming_list:
            results.append(await self.identify(incoming, user_id=user_id, ip=ip))
        return results

    def clear_dedup_cache(self) -> None:
        self._dedup_cache.clear()

    def get_metrics_summary(self):
        if hasattr(self.metrics, "get_summary"):
            return self.metrics.get_summary()
        return None
