from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, TypedDict


class ScoredPair(TypedDict):
    score: float
    sameDevice: bool
    isAttractor: bool


@dataclass(frozen=True)
class BenchmarkResult:
    threshold: int
    precision: float
    recall: float
    f1: float
    far: float
    frr: float
    far_frr_gap: float
    attr: float


def calculate_metrics(
    scored_pairs: Sequence[ScoredPair], thresholds: Sequence[int] | None = None
) -> List[BenchmarkResult]:
    threshold_values = list(thresholds) if thresholds is not None else [i * 5 for i in range(21)]
    results: List[BenchmarkResult] = []

    for threshold in threshold_values:
        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for pair in scored_pairs:
            predicted_same = pair["score"] >= threshold
            if pair["sameDevice"] and predicted_same:
                tp += 1
            elif (not pair["sameDevice"]) and predicted_same:
                fp += 1
            elif (not pair["sameDevice"]) and (not predicted_same):
                tn += 1
            else:
                fn += 1

        precision = (tp / (tp + fp)) if (tp + fp) else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) else 0.0
        far = (fp / (fp + tn)) if (fp + tn) else 0.0
        frr = (fn / (tp + fn)) if (tp + fn) else 0.0
        far_frr_gap = abs(far - frr)

        attractor_impostors = [p for p in scored_pairs if (not p["sameDevice"]) and p["isAttractor"] is True]
        if attractor_impostors:
            attr_above = [p for p in attractor_impostors if p["score"] >= threshold]
            attr = len(attr_above) / len(attractor_impostors)
        else:
            attr = 0.0

        denominator = precision + recall
        f1 = (2 * precision * recall / denominator) if denominator else 0.0

        results.append(
            BenchmarkResult(
                threshold=int(threshold),
                precision=precision,
                recall=recall,
                f1=f1,
                far=far,
                frr=frr,
                far_frr_gap=far_frr_gap,
                attr=attr,
            )
        )

    return results


@dataclass(frozen=True)
class EqualErrorRateResult:
    threshold: float
    eer: float
    far: float
    frr: float
    method: str


def calculate_true_eer(results: Sequence[BenchmarkResult]) -> EqualErrorRateResult:
    """
    Compute true Equal Error Rate (EER) from FAR/FRR threshold sweep results.

    If FAR and FRR cross between sampled thresholds, linearly interpolate the
    crossing point. If no crossing exists in sampled points, use the nearest
    threshold by |FAR - FRR| and report average(FAR, FRR) there.
    """
    if not results:
        return EqualErrorRateResult(
            threshold=0.0,
            eer=0.0,
            far=0.0,
            frr=0.0,
            method="empty",
        )

    ordered = sorted(results, key=lambda item: item.threshold)
    previous = ordered[0]
    previous_delta = previous.far - previous.frr

    if previous_delta == 0:
        return EqualErrorRateResult(
            threshold=float(previous.threshold),
            eer=previous.far,
            far=previous.far,
            frr=previous.frr,
            method="exact_threshold",
        )

    for current in ordered[1:]:
        current_delta = current.far - current.frr

        if current_delta == 0:
            return EqualErrorRateResult(
                threshold=float(current.threshold),
                eer=current.far,
                far=current.far,
                frr=current.frr,
                method="exact_threshold",
            )

        if previous_delta * current_delta < 0:
            interpolation = previous_delta / (previous_delta - current_delta)
            threshold = previous.threshold + interpolation * (current.threshold - previous.threshold)
            far = previous.far + interpolation * (current.far - previous.far)
            frr = previous.frr + interpolation * (current.frr - previous.frr)
            eer = (far + frr) / 2.0
            return EqualErrorRateResult(
                threshold=float(threshold),
                eer=eer,
                far=far,
                frr=frr,
                method="interpolated_crossing",
            )

        previous = current
        previous_delta = current_delta

    nearest = min(ordered, key=lambda item: abs(item.far - item.frr))
    eer = (nearest.far + nearest.frr) / 2.0
    return EqualErrorRateResult(
        threshold=float(nearest.threshold),
        eer=eer,
        far=nearest.far,
        frr=nearest.frr,
        method="nearest_threshold",
    )
