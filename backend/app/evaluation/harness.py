"""Evaluation benchmark dataset and accuracy/latency benchmarking harness."""

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.graph.review_graph import run_review
from app.schemas.review import ReviewResult

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkSample:
    """A code snippet with known ground-truth defects for evaluation."""
    sample_id: str
    name: str
    language: str
    code: str
    expected_bugs: List[str]  # Keywords expected in detected issue descriptions
    expected_vulnerabilities: List[str]
    expected_min_severity: str = "medium"


BENCHMARK_DATASET: List[BenchmarkSample] = [
    # 1. Python SQL Injection
    BenchmarkSample(
        sample_id="py-sqli-01",
        name="Python SQL Injection",
        language="python",
        code="""def get_user_records(db, user_input):
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    return db.execute(query)
""",
        expected_bugs=[],
        expected_vulnerabilities=["sql", "injection"],
        expected_min_severity="high",
    ),
    # 2. Python Division by Zero
    BenchmarkSample(
        sample_id="py-div-zero",
        name="Python Division by Zero Defect",
        language="python",
        code="""def compute_average(total, count):
    return total / count
""",
        expected_bugs=["division by zero", "zero"],
        expected_vulnerabilities=[],
        expected_min_severity="medium",
    ),
    # 3. Python Mutable Default Argument
    BenchmarkSample(
        sample_id="py-mutable-default",
        name="Python Mutable Default Argument",
        language="python",
        code="""def append_to_list(val, target_list=[]):
    target_list.append(val)
    return target_list
""",
        expected_bugs=["mutable default", "target_list"],
        expected_vulnerabilities=[],
        expected_min_severity="medium",
    ),
    # 4. JavaScript Hardcoded API Secret
    BenchmarkSample(
        sample_id="js-hardcoded-token",
        name="JavaScript Hardcoded API Token",
        language="javascript",
        code="""const API_SECRET_KEY = "sk-live-99882233aabbcc";
async function fetchAccount() {
    return fetch("https://api.example.com", { headers: { Authorization: API_SECRET_KEY } });
}
""",
        expected_bugs=[],
        expected_vulnerabilities=["secret", "token", "hardcoded"],
        expected_min_severity="high",
    ),
    # 5. TypeScript Unhandled Promise / Async Rejection
    BenchmarkSample(
        sample_id="ts-unhandled-promise",
        name="TypeScript Unhandled Async Error",
        language="typescript",
        code="""async function loadData(url: string): Promise<any> {
    const res = await fetch(url);
    return res.json();
}
""",
        expected_bugs=["error handling", "try", "catch"],
        expected_vulnerabilities=[],
        expected_min_severity="low",
    ),
    # 6. Java Resource Leak
    BenchmarkSample(
        sample_id="java-unclosed-stream",
        name="Java Unclosed FileInputStream Resource Leak",
        language="java",
        code="""public class FileReader {
    public void readFile(String path) throws Exception {
        FileInputStream fis = new FileInputStream(path);
        int data = fis.read();
    }
}
""",
        expected_bugs=["resource leak", "close", "stream"],
        expected_vulnerabilities=[],
        expected_min_severity="medium",
    ),
    # 7. Go Goroutine Resource / Channel Leak
    BenchmarkSample(
        sample_id="go-goroutine-leak",
        name="Go Nil Channel Read Deadlock",
        language="go",
        code="""package main
func readFromNilChan() int {
    var ch chan int
    return <-ch
}
""",
        expected_bugs=["nil channel", "deadlock", "block"],
        expected_vulnerabilities=[],
        expected_min_severity="high",
    ),
]


@dataclass
class EvaluationMetricResult:
    """Aggregated evaluation metrics across benchmark runs."""
    total_samples: int
    total_expected_defects: int
    defects_caught: int
    recall: float
    total_reported_issues: int
    estimated_false_positives: int
    false_positive_rate: float
    avg_latency_ms: float
    sample_details: List[Dict[str, Any]] = field(default_factory=list)


async def run_benchmark_evaluation(depth: str = "deep") -> EvaluationMetricResult:
    """Run full review pipeline against all benchmark samples and compute recall, false-positive rate, and latency."""
    total_expected = 0
    total_caught = 0
    total_reported = 0
    total_latency_ms = 0.0
    details = []

    for sample in BENCHMARK_DATASET:
        t0 = time.perf_counter()
        state = {
            "raw_code": sample.code,
            "code": sample.code,
            "language": sample.language,
            "depth": depth,
        }
        review: ReviewResult = await run_review(state, persist=False)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        total_latency_ms += latency_ms

        all_expected = sample.expected_bugs + sample.expected_vulnerabilities
        total_expected += len(all_expected)

        caught_count = 0
        reported_descriptions = [i.description.lower() for i in review.issues]
        total_reported += len(review.issues)

        for expected in all_expected:
            if any(expected.lower() in desc for desc in reported_descriptions):
                caught_count += 1

        total_caught += caught_count
        details.append({
            "sample_id": sample.sample_id,
            "name": sample.name,
            "expected": len(all_expected),
            "caught": caught_count,
            "reported_issues": len(review.issues),
            "latency_ms": round(latency_ms, 2),
        })

    recall = total_caught / total_expected if total_expected > 0 else 1.0
    avg_latency = total_latency_ms / len(BENCHMARK_DATASET) if BENCHMARK_DATASET else 0.0
    fp_estimate = max(0, total_reported - total_caught)
    fp_rate = fp_estimate / total_reported if total_reported > 0 else 0.0

    return EvaluationMetricResult(
        total_samples=len(BENCHMARK_DATASET),
        total_expected_defects=total_expected,
        defects_caught=total_caught,
        recall=round(recall, 3),
        total_reported_issues=total_reported,
        estimated_false_positives=fp_estimate,
        false_positive_rate=round(fp_rate, 3),
        avg_latency_ms=round(avg_latency, 2),
        sample_details=details,
    )
