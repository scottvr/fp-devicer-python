from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from ..libs.confidence import calculate_confidence
from .data_generator import LabeledFingerprint, generate_dataset
from .metrics import BenchmarkResult, ScoredPair, calculate_metrics, calculate_true_eer


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


def _generate_pairs(groups: Dict[str, List[LabeledFingerprint]]) -> List[ScoredPair]:
    devices = list(groups.keys())
    sorted_by_size = sorted(devices, key=lambda x: len(groups[x]), reverse=True)
    attractor_pool_size = max(1, int(len(sorted_by_size) * 0.1 + 0.9999))
    scored_pairs: List[ScoredPair] = []

    for i in range(2500):
        dev = devices[i % len(devices)]
        samples = groups[dev]
        if len(samples) < 2:
            continue

        idx1 = i % len(samples)
        idx2 = (idx1 + 1 + i) % len(samples)
        a = samples[idx1]
        b = samples[idx2]
        scored_pairs.append(
            {
                "score": float(calculate_confidence(a.data, b.data)),
                "sameDevice": True,
                "isAttractor": a.is_attractor or b.is_attractor,
            }
        )

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
            cross_b = attractor_sample if attractor_dev != dev else groups[dev2][i % len(groups[dev2])]

            scored_pairs.append(
                {
                    "score": float(calculate_confidence(cross_a.data, cross_b.data)),
                    "sameDevice": False,
                    "isAttractor": cross_a.is_attractor or cross_b.is_attractor,
                }
            )

        scored_pairs.append(
            {
                "score": float(calculate_confidence(c.data, d.data)),
                "sameDevice": False,
                "isAttractor": c.is_attractor or d.is_attractor,
            }
        )

    return scored_pairs


def run_accuracy_benchmark(
    dataset_size: int = 2000,
    sessions_per_device: int = 5,
    dbscan_eps: float = 0.05,
    dbscan_min_pts: int = 3,
) -> Dict[str, Any]:
    dataset = generate_dataset(dataset_size, sessions_per_device)

    groups: Dict[str, List[LabeledFingerprint]] = {}
    for item in dataset:
        groups.setdefault(item.device_label, []).append(item)

    scored_pairs = _generate_pairs(groups)

    results = calculate_metrics(scored_pairs)
    best = max(results, key=lambda item: item.f1)
    true_eer = calculate_true_eer(results)

    output = "\n".join(
        [
            f"--- Accuracy Metrics ({datetime.now(UTC).isoformat()}) ---",
            _format_table([asdict(item) for item in results]),
            (
                f"Best threshold (F1): {best.threshold} | "
                f"F1: {best.f1:.3f} | FAR/FRR gap: {best.far_frr_gap:.3f}"
            ),
            (
                f"True EER: {true_eer.eer:.3f} at threshold≈{true_eer.threshold:.2f} "
                f"(FAR={true_eer.far:.3f}, FRR={true_eer.frr:.3f}, method={true_eer.method})"
            ),
        ]
    )

    out_path = Path(__file__).with_name("accuracy.bench.out")
    out_path.write_text(output, encoding="utf-8")

    return {
        "results": results,
        "best": best,
        "output": output,
    }


def main() -> None:
    payload = run_accuracy_benchmark()
    print(payload["output"])


if __name__ == "__main__":
    main()
