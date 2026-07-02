from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare_reports(
    *,
    current_report: dict[str, Any],
    baseline_report: dict[str, Any] | None,
    tolerance: float = 0.0,
) -> dict[str, Any]:
    if baseline_report is None:
        return {"baseline": None, "degraded": False, "failures": [], "metric_deltas": {}}

    current_metrics = current_report.get("summary", {}).get("metrics", {})
    baseline_metrics = baseline_report.get("summary", {}).get("metrics", {})
    metric_deltas: dict[str, float] = {}
    failures: list[dict[str, Any]] = []

    for metric_name, current_value in current_metrics.items():
        if metric_name not in baseline_metrics:
            continue
        baseline_value = float(baseline_metrics[metric_name])
        delta = round(float(current_value) - baseline_value, 4)
        metric_deltas[metric_name] = delta
        if delta < -abs(tolerance):
            failures.append(
                {
                    "metric": metric_name,
                    "baseline": baseline_value,
                    "current": float(current_value),
                    "delta": delta,
                }
            )

    return {
        "baseline": baseline_report.get("run", {}).get("report_path")
        or baseline_report.get("run", {}).get("dataset_name"),
        "degraded": bool(failures),
        "failures": failures,
        "metric_deltas": metric_deltas,
    }
