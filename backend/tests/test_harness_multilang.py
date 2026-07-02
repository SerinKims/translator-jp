from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import EvalRun
from app.db.repositories.evaluation_repository import EvaluationRepository
from app.services.evaluator import EvaluationService, TranslationAttempt

DATASETS = [
    ("harness/datasets/smoke_ja_ko.jsonl", "translate_ja_ko_v1"),
    ("harness/datasets/smoke_zh_ko.jsonl", "translate_zh_ko_v1"),
    ("harness/datasets/smoke_en_ko.jsonl", "translate_en_ko_v1"),
]


def test_smoke_datasets_have_at_least_ten_cases() -> None:
    service = EvaluationService(translator=ReferenceTranslator({}))

    for dataset_path, _ in DATASETS:
        cases = service.load_dataset(dataset_path)

        assert len(cases) >= 10
        assert all(case["target_lang"] == "ko" for case in cases)


def test_selects_language_specific_prompts() -> None:
    service = EvaluationService(translator=ReferenceTranslator({}))

    for dataset_path, expected_prompt_version in DATASETS:
        case = service.load_dataset(dataset_path)[0]

        assert service.select_prompt_version_for_case(case) == expected_prompt_version


def test_generates_report_and_latest_json(tmp_path: Path) -> None:
    async def run_test() -> None:
        dataset_path = "harness/datasets/smoke_en_ko.jsonl"
        seed_service = EvaluationService(translator=ReferenceTranslator({}))
        cases = seed_service.load_dataset(dataset_path)
        translator = ReferenceTranslator({case["source"]: case["reference"] for case in cases})
        service = EvaluationService(translator=translator)

        report = await service.run_evaluation(
            dataset_path=dataset_path,
            model="qwen3:14b",
            output_path=tmp_path / "report.json",
            latest_path=tmp_path / "latest.json",
        )

        saved_report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
        latest_report = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))

        assert set(report) == {"run", "summary", "cases", "regression"}
        assert saved_report["summary"]["total_cases"] == len(cases)
        assert latest_report["run"]["model_name"] == "qwen3:14b"
        assert report["summary"]["metrics"]["no_source_left_score"] == 1.0
        assert translator.prompt_versions == ["translate_en_ko_v1"] * len(cases)

    asyncio.run(run_test())


def test_saves_eval_run_and_results(db_session: Session, tmp_path: Path) -> None:
    async def run_test() -> None:
        dataset_path = "harness/datasets/smoke_ja_ko.jsonl"
        seed_service = EvaluationService(translator=ReferenceTranslator({}))
        cases = seed_service.load_dataset(dataset_path)
        translator = ReferenceTranslator({case["source"]: case["reference"] for case in cases})
        service = EvaluationService(db_session, translator=translator)

        await service.run_evaluation(
            dataset_path=dataset_path,
            model="qwen3:14b",
            output_path=tmp_path / "report.json",
            latest_path=tmp_path / "latest.json",
            save_db=True,
        )

        run = db_session.query(EvalRun).one()
        results = EvaluationRepository(db_session).list_results(eval_run_id=run.id)

        assert run.model_name == "qwen3:14b"
        assert run.prompt_version == "translate_ja_ko_v1"
        assert run.total_cases == len(cases)
        assert run.passed_cases == len(cases)
        assert run.no_japanese_left_score == 1.0
        assert len(results) == len(cases)
        assert all(result.passed == 1 for result in results)

    asyncio.run(run_test())


class ReferenceTranslator:
    def __init__(self, translations_by_source: dict[str, str]) -> None:
        self.translations_by_source = translations_by_source
        self.prompt_versions: list[str] = []

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
        self.prompt_versions.append(prompt_version)
        return TranslationAttempt(
            text=self.translations_by_source.get(source, ""),
            elapsed_ms=7,
        )
