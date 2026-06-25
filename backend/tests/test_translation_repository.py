from datetime import datetime

from sqlalchemy.orm import Session

from app.db.repositories.translation_repository import TranslationRepository


def test_create_translation_job(db_session: Session) -> None:
    repository = TranslationRepository(db_session)

    job = repository.create_job(original_text="吾輩は猫である。")

    assert job.id is not None
    assert job.original_text == "吾輩は猫である。"
    assert job.source_site == "manual"
    assert job.model_name == "gemma4:26b-a4b-it-q4_K_M"
    assert job.prompt_version == "translate_ja_ko_v1"
    assert job.ollama_think == "false"
    assert job.ollama_options_json is None
    assert job.style == "webnovel"
    assert job.honorific_policy == "preserve"
    assert job.preserve_names == 1
    assert job.status == "pending"


def test_create_translation_job_with_pixiv_source_metadata(db_session: Session) -> None:
    repository = TranslationRepository(db_session)
    fetched_at = datetime(2026, 6, 22, 10, 0, 0)

    job = repository.create_job(
        source_site="pixiv",
        source_url="https://www.pixiv.net/novel/show.php?id=12345678",
        source_title="夜の物語",
        source_author="作者名",
        source_work_id="12345678",
        source_fetched_at=fetched_at,
        original_text="これはpixiv小説です。",
    )

    saved = repository.get_job(job.id)

    assert saved is not None
    assert saved.source_site == "pixiv"
    assert saved.source_url == "https://www.pixiv.net/novel/show.php?id=12345678"
    assert saved.source_title == "夜の物語"
    assert saved.source_author == "作者名"
    assert saved.source_work_id == "12345678"
    assert saved.source_fetched_at == fetched_at


def test_create_translation_job_with_ollama_options(db_session: Session) -> None:
    repository = TranslationRepository(db_session)

    job = repository.create_job(
        original_text="原文",
        ollama_think="low",
        ollama_options={"temperature": 0.2, "max_tokens": 2048},
    )

    assert job.ollama_think == '"low"'
    assert job.ollama_options_json == '{"max_tokens": 2048, "temperature": 0.2}'
