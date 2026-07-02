from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Base, EvalResult, EvalRun


class EvaluationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._ensure_tables()

    def create_run(
        self,
        *,
        run_name: str | None,
        model_name: str,
        prompt_version: str,
        dataset_name: str,
        total_cases: int,
        passed_cases: int,
        failed_cases: int,
        avg_elapsed_ms: int | None,
        no_source_left_score: float | None,
        paragraph_match_score: float | None,
        glossary_preserve_score: float | None,
        dialogue_style_score: float | None,
        no_empty_translation_score: float | None,
        report_json: str | None,
        commit: bool = True,
    ) -> EvalRun:
        run = EvalRun(
            run_name=run_name,
            model_name=model_name,
            prompt_version=prompt_version,
            dataset_name=dataset_name,
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            avg_elapsed_ms=avg_elapsed_ms,
            no_japanese_left_score=no_source_left_score,
            paragraph_match_score=paragraph_match_score,
            glossary_preserve_score=glossary_preserve_score,
            dialogue_style_score=dialogue_style_score,
            no_empty_translation_score=no_empty_translation_score,
            report_json=report_json,
        )
        self.db.add(run)
        if commit:
            self.db.commit()
            self.db.refresh(run)
        else:
            self.db.flush()
        return run

    def create_result(
        self,
        *,
        eval_run_id: int,
        case_id: str,
        source_text: str,
        expected_translation: str | None,
        actual_translation: str | None,
        passed: bool,
        score: float | None,
        fail_reason: str | None,
        elapsed_ms: int | None,
        commit: bool = True,
    ) -> EvalResult:
        result = EvalResult(
            eval_run_id=eval_run_id,
            case_id=case_id,
            source_text=source_text,
            expected_translation=expected_translation,
            actual_translation=actual_translation,
            passed=int(passed),
            score=score,
            fail_reason=fail_reason,
            elapsed_ms=elapsed_ms,
        )
        self.db.add(result)
        if commit:
            self.db.commit()
            self.db.refresh(result)
        else:
            self.db.flush()
        return result

    def save_report(self, report: dict[str, Any], *, run_name: str | None = None) -> EvalRun:
        summary = report.get("summary", {})
        metrics = summary.get("metrics", {})
        run_payload = report.get("run", {})
        report_json = json.dumps(report, ensure_ascii=False, sort_keys=True)
        run = self.create_run(
            run_name=run_name or run_payload.get("run_name"),
            model_name=str(run_payload.get("model_name", "")),
            prompt_version=str(run_payload.get("prompt_version", "")),
            dataset_name=str(run_payload.get("dataset_name", "")),
            total_cases=int(summary.get("total_cases", 0) or 0),
            passed_cases=int(summary.get("passed_cases", 0) or 0),
            failed_cases=int(summary.get("failed_cases", 0) or 0),
            avg_elapsed_ms=int(summary.get("avg_elapsed_ms", 0) or 0),
            no_source_left_score=_optional_float(metrics.get("no_source_left_score")),
            paragraph_match_score=_optional_float(metrics.get("paragraph_match_score")),
            glossary_preserve_score=_optional_float(metrics.get("glossary_preserve_score")),
            dialogue_style_score=_optional_float(metrics.get("dialogue_style_score")),
            no_empty_translation_score=_optional_float(metrics.get("no_empty_translation_score")),
            report_json=report_json,
            commit=False,
        )

        for case_result in report.get("cases", []):
            self.create_result(
                eval_run_id=run.id,
                case_id=str(case_result.get("id", "")),
                source_text=str(case_result.get("source", "")),
                expected_translation=case_result.get("reference"),
                actual_translation=case_result.get("actual"),
                passed=bool(case_result.get("passed")),
                score=_optional_float(case_result.get("score")),
                fail_reason=_fail_reason(case_result),
                elapsed_ms=int(case_result.get("elapsed_ms", 0) or 0),
                commit=False,
            )

        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: int) -> EvalRun | None:
        return self.db.get(EvalRun, run_id)

    def list_results(self, *, eval_run_id: int) -> list[EvalResult]:
        statement = (
            select(EvalResult).where(EvalResult.eval_run_id == eval_run_id).order_by(EvalResult.id)
        )
        return list(self.db.scalars(statement))

    def _ensure_tables(self) -> None:
        bind = self.db.get_bind()
        Base.metadata.create_all(bind, tables=[EvalRun.__table__, EvalResult.__table__])


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _fail_reason(case_result: dict[str, Any]) -> str | None:
    failed_checks = [
        f"{name}: {check.get('message', '')}"
        for name, check in case_result.get("checks", {}).items()
        if check.get("passed") is False
    ]
    return "; ".join(failed_checks) if failed_checks else None
