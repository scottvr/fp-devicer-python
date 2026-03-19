from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .data_generator import (
	create_attractor_fingerprint,
	create_base_fingerprint,
	generate_audio_blob,
	generate_canvas_blob,
	generate_dataset,
	generate_webgl_blob,
	mutate,
)
from .metrics import BenchmarkResult, calculate_metrics

if TYPE_CHECKING:
	from .accuracy_bench import run_accuracy_benchmark
	from .performance_bench import run_performance_benchmark

__all__ = [
	"BenchmarkResult",
	"create_attractor_fingerprint",
	"create_base_fingerprint",
	"calculate_metrics",
	"generate_audio_blob",
	"generate_canvas_blob",
	"generate_dataset",
	"generate_webgl_blob",
	"mutate",
	"run_accuracy_benchmark",
	"run_performance_benchmark",
]


def __getattr__(name: str) -> Any:
	if name == "run_accuracy_benchmark":
		from .accuracy_bench import run_accuracy_benchmark

		return run_accuracy_benchmark
	if name == "run_performance_benchmark":
		from .performance_bench import run_performance_benchmark

		return run_performance_benchmark
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
