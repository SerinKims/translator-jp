from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.db.repositories.evaluation_repository import EvaluationRepository
from app.llm.ollama_client import OllamaClient
from app.llm.prompts import PromptLoader

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.evaluators.consistency import build_report  # noqa: E402
from harness.evaluators.regression import compare_reports, load_report  # noqa: E402
from harness.evaluators.rule_checks import evaluate_case  # noqa: E402

DEFAULT_REPORT_DIR = PROJECT_ROOT / "harness" / "reports"
LATEST_REPORT_PATH = DEFAULT_REPORT_DIR / "latest.json"


@dataclass(frozen=True)
class TranslationAttempt:
    text: str
    elapsed_ms: int


class HarnessTranslator(Protocol):
    async def translate(
        self,
        *,
        source: str,
        source_lang: str,
        target_lang: str,
        model: str,
        prompt_version: str,
        prompt_text: str,
        glossary: list[dict[str, Any]],
    ) -> TranslationAttempt | str: ...


class OllamaHarnessTranslator:
    def __init__(self, *, timeout_seconds: float | None = None) -> None:
        self.timeout_seconds = timeout_seconds

    async def translate(
        self,
        *,
        source: str,
        source_lang: str,
        target_lang: str,
        model: str,
        prompt_version: str,
        prompt_text: str,
        glossary: list[dict[str, Any]],
    ) -> TranslationAttempt:
        client = OllamaClient(model=model, timeout_seconds=self.timeout_seconds)
        messages = [
            {"role": "system", "content": prompt_text},
            {
                "role": "user",
                "content": _build_user_prompt(
                    source=source,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    glossary=glossary,
                ),
            },
        ]
        result = await client.chat(messages, think=False, options=None)
        return TranslationAttempt(text=result.content, elapsed_ms=result.elapsed_ms)


class EvaluationService:
    def __init__(
        self,
        db: Session | None = None,
        *,
        prompt_loader: PromptLoader | None = None,
        translator: HarnessTranslator | None = None,
    ) -> None:
        self.db = db
        self.prompt_loader = prompt_loader or PromptLoader()
        self.translator = translator or OllamaHarnessTranslator()

    def load_dataset(self, dataset_path: str | Path) -> list[dict[str, Any]]:
        path = self.resolve_path(dataset_path)
        cases: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
            self._validate_case(case, path=path, line_number=line_number)
            cases.append(case)
        if not cases:
            raise ValueError(f"Dataset is empty: {path}")
        return cases

    def select_prompt_version_for_case(self, case: dict[str, Any]) -> str:
        return self.prompt_loader.select_prompt_version(
            source_lang=str(case["source_lang"]),
            target_lang=str(case["target_lang"]),
        )

    async def run_evaluation(
        self,
        *,
        dataset_path: str | Path,
        model: str,
        output_path: str | Path | None = None,
        baseline_path: str | Path | None = None,
        latest_path: str | Path = LATEST_REPORT_PATH,
        save_db: bool = False,
    ) -> dict[str, Any]:
        dataset_file = self.resolve_path(dataset_path)
        cases = self.load_dataset(dataset_file)
        started_at = datetime.now(UTC)
        case_results: list[dict[str, Any]] = []
        prompt_versions: list[str] = []

        for case in cases:
            source_lang = str(case["source_lang"])
            target_lang = str(case["target_lang"])
            prompt_version = self.select_prompt_version_for_case(case)
            prompt_versions.append(prompt_version)
            prompt_text = self.prompt_loader.load(
                prompt_version,
                source_lang=source_lang,
                target_lang=target_lang,
            )
            attempt = await self.translator.translate(
                source=str(case["source"]),
                source_lang=source_lang,
                target_lang=target_lang,
                model=model,
                prompt_version=prompt_version,
                prompt_text=prompt_text,
                glossary=_normalize_glossary(case.get("glossary", [])),
            )
            normalized_attempt = _normalize_attempt(attempt)
            case_result = evaluate_case(
                {**case, "elapsed_ms": normalized_attempt.elapsed_ms},
                normalized_attempt.text,
                prompt_version=prompt_version,
            )
            case_results.append(case_result)

        resolved_output_path = self._default_output_path(dataset_file, model, output_path)
        run = {
            "model_name": model,
            "prompt_version": _single_or_mixed(prompt_versions),
            "dataset_name": dataset_file.name,
            "dataset_path": str(dataset_file),
            "report_path": str(resolved_output_path),
            "started_at": started_at.isoformat(),
            "ended_at": datetime.now(UTC).isoformat(),
        }
        draft_report = build_report(run=run, cases=case_results)
        baseline_report = load_report(self.resolve_path(baseline_path)) if baseline_path else None
        regression = compare_reports(
            current_report=draft_report,
            baseline_report=baseline_report,
        )
        report = build_report(run=run, cases=case_results, regression=regression)

        self.write_report(report, resolved_output_path)
        self.write_report(report, self.resolve_output_path(latest_path))

        if save_db:
            if self.db is None:
                raise ValueError("A database session is required when save_db=True.")
            EvaluationRepository(self.db).save_report(report)

        return report

    def write_report(self, report: dict[str, Any], output_path: str | Path) -> Path:
        path = self.resolve_output_path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        cwd_candidate = Path.cwd() / candidate
        if cwd_candidate.exists():
            return cwd_candidate
        return PROJECT_ROOT / candidate

    def resolve_output_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return PROJECT_ROOT / candidate

    def _default_output_path(
        self,
        dataset_path: Path,
        model: str,
        output_path: str | Path | None,
    ) -> Path:
        if output_path is not None:
            return self.resolve_output_path(output_path)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        model_slug = "".join(char if char.isalnum() else "_" for char in model).strip("_")
        return DEFAULT_REPORT_DIR / f"{dataset_path.stem}_{model_slug}_{timestamp}.json"

    def _validate_case(self, case: Any, *, path: Path, line_number: int) -> None:
        if not isinstance(case, dict):
            raise ValueError(f"Dataset row must be an object: {path}:{line_number}")
        required_fields = ("id", "source_lang", "target_lang", "source", "reference")
        missing = [field for field in required_fields if field not in case]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Dataset row is missing {joined}: {path}:{line_number}")


def _build_user_prompt(
    *,
    source: str,
    source_lang: str,
    target_lang: str,
    glossary: list[dict[str, Any]],
) -> str:
    lines = [
        f"source_lang: {source_lang}",
        f"target_lang: {target_lang}",
        "glossary:",
    ]
    for term in glossary:
        source_term = term.get("source_term")
        target_term = term.get("target_term")
        if source_term and target_term:
            lines.append(f"{source_term}={target_term}")
    lines.extend(["source_text:", source])
    return "\n".join(lines)


def _normalize_attempt(attempt: TranslationAttempt | str) -> TranslationAttempt:
    if isinstance(attempt, TranslationAttempt):
        return attempt
    return TranslationAttempt(text=str(attempt), elapsed_ms=0)


def _normalize_glossary(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _single_or_mixed(values: list[str]) -> str:
    unique = sorted(set(values))
    if len(unique) == 1:
        return unique[0]
    return "mixed"


def elapsed_ms(started_at: float) -> int:
    return max(0, round((time.perf_counter() - started_at) * 1000))
