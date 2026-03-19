import pytest

from devicer.benchmarks.metrics import BenchmarkResult, calculate_metrics, calculate_true_eer


def test_calculate_metrics_basic_parity_math():
    scored_pairs = [
        {"score": 90, "sameDevice": True, "isAttractor": False},
        {"score": 60, "sameDevice": True, "isAttractor": True},
        {"score": 70, "sameDevice": False, "isAttractor": True},
        {"score": 10, "sameDevice": False, "isAttractor": False},
    ]

    results = calculate_metrics(scored_pairs, thresholds=[50])
    result = results[0]

    assert result.threshold == 50
    assert result.precision == 2 / 3
    assert result.recall == 1.0
    assert result.far == 0.5
    assert result.frr == 0.0
    assert result.far_frr_gap == 0.5
    assert result.attr == 1.0


def test_calculate_metrics_default_threshold_count():
    scored_pairs = [{"score": 10, "sameDevice": False, "isAttractor": False}]
    results = calculate_metrics(scored_pairs)
    assert len(results) == 21
    assert results[0].threshold == 0
    assert results[-1].threshold == 100


def test_calculate_true_eer_interpolates_crossing():
    rows = [
        BenchmarkResult(80, 0.0, 0.0, 0.0, far=0.4, frr=0.2, far_frr_gap=0.2, attr=0.0),
        BenchmarkResult(90, 0.0, 0.0, 0.0, far=0.2, frr=0.4, far_frr_gap=0.2, attr=0.0),
    ]

    eer = calculate_true_eer(rows)

    assert eer.method == "interpolated_crossing"
    assert eer.threshold == pytest.approx(85.0)
    assert eer.eer == pytest.approx(0.3)
    assert eer.far == pytest.approx(0.3)
    assert eer.frr == pytest.approx(0.3)


def test_calculate_true_eer_falls_back_to_nearest_threshold():
    rows = [
        BenchmarkResult(80, 0.0, 0.0, 0.0, far=0.5, frr=0.1, far_frr_gap=0.4, attr=0.0),
        BenchmarkResult(90, 0.0, 0.0, 0.0, far=0.2, frr=0.05, far_frr_gap=0.15, attr=0.0),
    ]

    eer = calculate_true_eer(rows)

    assert eer.method == "nearest_threshold"
    assert eer.threshold == 90.0
    assert eer.eer == 0.125
    assert eer.far == 0.2
    assert eer.frr == 0.05
