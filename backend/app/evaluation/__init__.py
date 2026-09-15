"""Evaluation module for benchmarking accuracy, recall, false-positive rate, and latency."""

from app.evaluation.harness import (
    BenchmarkSample,
    BENCHMARK_DATASET,
    EvaluationMetricResult,
    run_benchmark_evaluation,
)

__all__ = [
    "BenchmarkSample",
    "BENCHMARK_DATASET",
    "EvaluationMetricResult",
    "run_benchmark_evaluation",
]
