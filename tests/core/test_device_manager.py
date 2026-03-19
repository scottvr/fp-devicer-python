import pytest
import asyncio

from devicer import DeviceManager, create_in_memory_adapter
from devicer.libs.default_observability import DefaultMetrics
from tests.fixtures.fingerprints import (
    fp_different,
    fp_identical,
    fp_similar,
    fp_very_different,
    fp_very_similar,
)


@pytest.mark.asyncio
async def test_creates_new_device_when_no_match_exists():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)
    result = await manager.identify(fp_identical, user_id="user_abc")
    assert result.device_id.startswith("dev_")
    assert result.is_new_device is True
    assert result.confidence == 0
    assert result.linked_user_id == "user_abc"


@pytest.mark.asyncio
async def test_match_flow_and_confidence_ordering():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    first = await manager.identify(fp_identical)
    second = await manager.identify(fp_very_similar)
    third = await manager.identify(fp_similar)
    fourth = await manager.identify(fp_different)
    fifth = await manager.identify(fp_very_different)

    assert second.device_id == first.device_id
    assert third.device_id == first.device_id
    assert second.confidence >= third.confidence >= fourth.confidence
    assert fifth.confidence < 60


@pytest.mark.asyncio
async def test_snapshot_persisted_each_identify_and_user_linked():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    result = await manager.identify(fp_identical, user_id="user_link_test")
    await manager.identify(fp_very_similar, user_id="user_link_test")

    history = await adapter.get_history(result.device_id)
    assert len(history) == 2
    assert all(item.user_id == "user_link_test" for item in history)


@pytest.mark.asyncio
async def test_dedup_cache_behavior():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=5000)

    first = await manager.identify(fp_identical)
    all_before = await adapter.get_all_fingerprints()
    second = await manager.identify(fp_identical)
    all_after = await adapter.get_all_fingerprints()

    assert second.device_id == first.device_id
    assert len(all_after) == len(all_before)

    manager.clear_dedup_cache()
    await manager.identify(fp_identical)
    all_post_clear = await adapter.get_all_fingerprints()
    assert len(all_post_clear) == len(all_after) + 1


@pytest.mark.asyncio
async def test_identify_many_batch_behavior():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    results = await manager.identify_many([fp_identical, fp_very_similar, fp_very_different], user_id="batch_user", ip="127.0.0.1")
    assert len(results) == 3
    assert results[0].is_new_device is True
    assert results[1].device_id == results[0].device_id

    empty = await manager.identify_many([])
    assert empty == []


@pytest.mark.asyncio
async def test_metrics_summary_and_custom_metrics():
    adapter = create_in_memory_adapter()
    metrics = DefaultMetrics()
    manager = DeviceManager(adapter, dedup_window_ms=0, metrics=metrics)

    await manager.identify(fp_identical)
    await manager.identify(fp_very_similar)

    summary = manager.get_metrics_summary()
    assert summary["counters"]["identify_total"] == 2


@pytest.mark.asyncio
async def test_match_confidence_persisted_in_result_and_snapshot():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    first = await manager.identify(fp_identical)
    second = await manager.identify(fp_very_similar)

    assert first.match_confidence == 0
    assert second.match_confidence == second.confidence

    history = await adapter.get_history(second.device_id)
    latest = history[0]
    assert latest.match_confidence == second.confidence


@pytest.mark.asyncio
async def test_new_device_snapshot_has_zero_match_confidence():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    result = await manager.identify(fp_identical)
    history = await adapter.get_history(result.device_id)
    assert history[0].match_confidence == 0


@pytest.mark.asyncio
async def test_dedup_cache_expires_after_window():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=50)

    await manager.identify(fp_identical)
    count_before = len(await adapter.get_all_fingerprints())
    await asyncio.sleep(0.07)
    await manager.identify(fp_identical)
    count_after = len(await adapter.get_all_fingerprints())
    assert count_after == count_before + 1


@pytest.mark.asyncio
async def test_dedup_disabled_always_writes():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    await manager.identify(fp_identical)
    await manager.identify(fp_identical)
    await manager.identify(fp_identical)

    all_entries = await adapter.get_all_fingerprints()
    assert len(all_entries) == 3


@pytest.mark.asyncio
async def test_identify_many_applies_context_to_all_entries():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    results = await manager.identify_many([fp_identical, fp_very_similar], user_id="batch_user", ip="127.0.0.1")
    assert results[0].linked_user_id == "batch_user"
    assert results[1].linked_user_id == "batch_user"

    history = await adapter.get_history(results[0].device_id)
    assert len(history) == 2
    assert all(item.user_id == "batch_user" for item in history)
    assert all(item.ip == "127.0.0.1" for item in history)


@pytest.mark.asyncio
async def test_identify_many_respects_dedup_with_repeated_inputs():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=5000)

    results = await manager.identify_many([fp_identical, fp_identical, fp_identical])
    assert len(results) == 3
    assert results[1].device_id == results[0].device_id
    assert results[2].device_id == results[0].device_id

    all_entries = await adapter.get_all_fingerprints()
    assert len(all_entries) == 1


@pytest.mark.asyncio
async def test_multiple_candidates_returns_highest_confidence_match():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0, match_threshold=50)

    first = await manager.identify(fp_identical)
    await manager.identify(fp_very_different)

    match = await manager.identify(fp_very_similar)
    assert match.device_id == first.device_id


@pytest.mark.asyncio
async def test_adaptive_weighting_with_stable_history_keeps_high_confidence():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    for _ in range(4):
        await manager.identify(fp_identical)

    result = await manager.identify(fp_very_similar)
    assert result.is_new_device is False
    assert result.confidence > 70


@pytest.mark.asyncio
async def test_identify_supports_profile_scoring_mode():
    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0, confidence_profile="same_instance")

    first = await manager.identify(fp_identical)
    second = await manager.identify(fp_very_similar)

    assert second.device_id == first.device_id
    assert 0 <= second.confidence <= 100


def test_get_metrics_summary_returns_none_without_get_summary():
    class MinimalMetrics:
        def increment_counter(self, name, value=1):
            return None

        def record_histogram(self, name, value):
            return None

        def record_gauge(self, name, value):
            return None

        def record_identify(self, duration_ms, confidence, is_new_device, candidates_count, matched):
            return None

    adapter = create_in_memory_adapter()
    manager = DeviceManager(adapter, dedup_window_ms=0, metrics=MinimalMetrics())
    assert manager.get_metrics_summary() is None
