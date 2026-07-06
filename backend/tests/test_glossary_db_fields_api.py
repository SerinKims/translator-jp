from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app


def test_glossary_api_persists_db_backed_fields(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)

    try:
        client = TestClient(app)
        created = client.post(
            "/api/glossary",
            json={
                "source_lang": "en",
                "target_lang": "ko",
                "source_term": "Demon King",
                "target_term": "마왕",
                "term_type": "title",
                "description": "fantasy title",
                "aliases": ["demon lord", "dark king"],
                "priority": 95,
                "is_required": False,
                "is_case_sensitive": True,
                "is_active": True,
            },
        )
        term_id = created.json()["id"]
        patched = client.patch(
            f"/api/glossary/{term_id}",
            json={
                "source_lang": "ja",
                "source_term": "魔王",
                "aliases": ["魔王様"],
                "is_required": True,
                "is_case_sensitive": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    created_payload = created.json()
    assert created_payload["glossary_set_id"] is None
    assert created_payload["source_lang"] == "en"
    assert created_payload["term_type"] == "title"
    assert created_payload["description"] == "fantasy title"
    assert created_payload["aliases"] == ["demon lord", "dark king"]
    assert created_payload["priority"] == 95
    assert created_payload["is_required"] is False
    assert created_payload["is_case_sensitive"] is True

    assert patched.status_code == 200
    patched_payload = patched.json()
    assert patched_payload["source_lang"] == "ja"
    assert patched_payload["source_term"] == "魔王"
    assert patched_payload["aliases"] == ["魔王様"]
    assert patched_payload["is_required"] is True
    assert patched_payload["is_case_sensitive"] is False


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
