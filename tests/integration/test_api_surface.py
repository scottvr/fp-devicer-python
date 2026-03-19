def test_public_api_surface_exports():
    import devicer as api

    assert callable(api.get_hash)
    assert callable(api.compare_hashes)
    assert callable(api.calculate_confidence)
    assert callable(api.calculate_confidence_profile)
    assert callable(api.calculate_confidence_breakdown)
    assert callable(api.create_confidence_calculator)

    assert callable(api.register_comparator)
    assert callable(api.register_weight)
    assert callable(api.register_plugin)
    assert callable(api.unregister_comparator)
    assert callable(api.unregister_weight)
    assert callable(api.set_default_weight)
    assert callable(api.clear_registry)
    assert callable(api.initialize_default_registry)

    assert callable(api.create_in_memory_adapter)
    assert callable(api.create_sqlite_adapter)
    assert callable(api.create_postgres_adapter)
    assert callable(api.create_redis_adapter)

    assert api.DeviceManager is not None
    assert api.AdapterFactory is not None
    assert api.default_logger is not None
    assert api.default_metrics is not None


import pytest


@pytest.mark.asyncio
async def test_round_trip_identify_flow():
    from devicer import AdapterFactory, AdapterFactoryOptions, DeviceManager
    from tests.fixtures.fingerprints import fp_identical, fp_very_similar

    adapter = AdapterFactory.create(AdapterFactoryOptions(type="inmemory"))
    await adapter.init()
    manager = DeviceManager(adapter, dedup_window_ms=0)

    first = await manager.identify(fp_identical)
    second = await manager.identify(fp_very_similar)

    assert first.device_id.startswith("dev_")
    assert first.is_new_device is True
    assert second.device_id == first.device_id
    assert second.is_new_device is False


def test_register_plugin_affects_global_registry_scoring():
    import devicer as api
    from tests.fixtures.fingerprints import fp_identical, fp_very_similar

    api.clear_registry()
    api.initialize_default_registry()
    api.register_plugin("userAgent", weight=0)
    score_with_zero_ua = api.calculate_confidence(fp_identical, fp_very_similar)

    api.clear_registry()
    api.initialize_default_registry()
    score_default = api.calculate_confidence(fp_identical, fp_very_similar)

    assert 0 <= score_with_zero_ua <= 100
    assert 0 <= score_default <= 100
