"""
Lightweight T-Career load scenario runner.

This script intentionally uses only Python's standard library so it can run in CI,
staging jump boxes, or developer machines without installing Locust/k6.

Example:
    python tools/load_tests/tcareer_load.py --base-url http://localhost:8000 --profile smoke
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Profile:
    users: int
    duration_seconds: int
    request_interval_seconds: float


PROFILES = {
    "smoke": Profile(users=2, duration_seconds=30, request_interval_seconds=1.0),
    "pilot": Profile(users=15, duration_seconds=180, request_interval_seconds=0.75),
    "expected-production": Profile(users=75, duration_seconds=300, request_interval_seconds=0.5),
    "stress": Profile(users=150, duration_seconds=600, request_interval_seconds=0.25),
}

SCENARIOS = {
    "auth": ["/api/v1/health/live/", "/api/v1/health/ready/"],
    "student-dashboard": ["/api/v1/jobs/student/dashboard/"],
    "recruiter-dashboard": ["/api/v1/health/ops/"],
    "organization-dashboard": ["/api/v1/organizations/"],
    "job-browsing": ["/api/v1/jobs/"],
    "candidate-search": ["/api/v1/jobs/organizations/{organization_id}/candidates/search/"],
    "application-pipeline": ["/api/v1/jobs/organizations/{organization_id}/applications/"],
    "notification-history": ["/api/v1/notifications/"],
    "ai-history": ["/api/v1/ai/history/"],
    "ai-chat": ["/api/v1/ai/"],
    "rag-retrieval": ["/api/v1/ai/knowledge/index-status/"],
    "enterprise-reports": ["/api/v1/organizations/{organization_id}/enterprise/reports/"],
    "email-queue": ["/api/v1/health/ops/"],
}


def percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, round((pct / 100) * (len(sorted_values) - 1)))
    return sorted_values[index]


def request_once(base_url: str, path: str, token: str = "") -> dict:
    url = base_url.rstrip("/") + path
    started = time.perf_counter()
    request = urllib.request.Request(url, method="GET")
    request.add_header("Accept", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read(256)
            status = response.status
            size = int(response.headers.get("Content-Length") or 0)
    except urllib.error.HTTPError as exc:
        status = exc.code
        size = 0
    except Exception:
        status = 0
        size = 0
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {"status": status, "latency_ms": elapsed_ms, "size": size, "path": path}


def expand_paths(paths: Iterable[str], organization_id: str) -> list[str]:
    return [path.format(organization_id=organization_id or "00000000-0000-0000-0000-000000000000") for path in paths]


def run_profile(base_url: str, profile: Profile, paths: list[str], token: str) -> dict:
    started_at = time.perf_counter()
    deadline = time.time() + profile.duration_seconds
    results = []
    futures = []
    with ThreadPoolExecutor(max_workers=profile.users) as executor:
        while time.time() < deadline:
            for path in paths:
                futures.append(executor.submit(request_once, base_url, path, token))
            time.sleep(profile.request_interval_seconds)
        for future in as_completed(futures):
            results.append(future.result())

    elapsed_seconds = max(time.perf_counter() - started_at, 0.001)
    latencies = [item["latency_ms"] for item in results if item["status"]]
    errors = [item for item in results if not (200 <= item["status"] < 400)]
    successful = len(results) - len(errors)
    return {
        "request_count": len(results),
        "successful_requests": successful,
        "failed_requests": len(errors),
        "error_count": len(errors),
        "error_rate": round(len(errors) / len(results), 4) if results else 0,
        "requests_per_second": round(len(results) / elapsed_seconds, 2),
        "p50_ms": round(statistics.median(latencies), 2) if latencies else 0,
        "p95_ms": round(percentile(latencies, 95), 2),
        "p99_ms": round(percentile(latencies, 99), 2),
        "average_response_size_bytes": round(sum(item["size"] for item in results) / len(results), 2) if results else 0,
        "status_counts": {str(status): len([item for item in results if item["status"] == status]) for status in sorted({item["status"] for item in results})},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--profile", choices=PROFILES.keys(), default="smoke")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), action="append")
    parser.add_argument("--token", default="")
    parser.add_argument("--organization-id", default="")
    args = parser.parse_args()

    selected = args.scenario or list(SCENARIOS.keys())
    paths = []
    for scenario in selected:
        paths.extend(expand_paths(SCENARIOS[scenario], args.organization_id))
    result = run_profile(args.base_url, PROFILES[args.profile], paths, args.token)
    result.update({"profile": args.profile, "scenarios": selected, "base_url": args.base_url})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
