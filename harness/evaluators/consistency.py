from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from harness.evaluators.rule_checks import (
    DIALOGUE_CHECK,
    EMPTY_TRANSLATION_CHECK,
    GLOSSARY_CHECK,
    OVER_SUMMARY_CHECK,
    PARAGRAPH_CHECK,
    PROPER_NOUN_CHECK,
    SOURCE_RESIDUAL_CHECK,
)


METRIC_BY_CHECK = {
    SOURCE_RESIDUAL_CHECK: "no_source_left_score",
    PARAGRAPH_CHECK: "paragraph_match_score",
    GLOSSARY_CHECK: "glossary_preserve_score",
    DIALOGUE_CHECK: "dialogue_style_score",
    EMPTY_TRANSLATION_CHECK: "no_empty_translation_score",
    OVER_SUMMARY_CHECK: "no_over_summary_score",
    PROPER_NOUN_CHECK: "proper_noun_preserve_score",
}


def summarize_results(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(case_results)
    passed_cases = sum(1 for result in case_results if result.get("passed") is True)
    failed_cases = total_cases - passed_cases
    elapsed_values = [
        int(result.get("elapsed_ms", 0) or 0)
        for result in case_results
        if result.get("elapsed_ms") is not None
    ]
    metrics = {
        metric_name: _average(
            _check_score(result, check_name)
            for result in case_results
            if check_name in result["checks"]
        )
        for check_name, metric_name in METRIC_BY_CHECK.items()
    }

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "pass_rate": round(passed_cases / total_cases, 4) if total_cases else 0.0,
        "avg_elapsed_ms": round(_average(elapsed_values)) if elapsed_values else 0,
        "metrics": {key: round(value, 4) for key, value in metrics.items()},
    }


def build_report(
    *,
    run: dict[str, Any],
    cases: list[dict[str, Any]],
    regression: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "run": {
            **run,
            "created_at": run.get("created_at") or datetime.now(UTC).isoformat(),
        },
        "summary": summarize_results(cases),
        "cases": cases,
        "regression": regression or {"baseline": None, "degraded": False, "failures": []},
    }


def _check_score(result: dict[str, Any], check_name: str) -> float:
    check = result["checks"][check_name]
    return float(check.get("score", 0.0))


def _average(values: Any) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)
