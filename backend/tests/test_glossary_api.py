from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app


def test_glossary_api_create_and_list(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)

    try:
        client = TestClient(app)
        created = client.post(
            "/api/glossary",
            json={
                "source_lang": "ja",
                "target_lang": "ko",
                "source_term": "王都",
                "target_term": "왕도",
                "term_type": "place",
                "description": "판타지 문맥에서는 수도보다 왕도가 자연스러움",
                "aliases": ["王城", "王国の都"],
                "priority": 80,
                "is_required": True,
            },
        )
        listed = client.get("/api/glossary")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    payload = created.json()
    assert payload["id"] == 1
    assert payload["source_lang"] == "ja"
    assert payload["target_lang"] == "ko"
    assert payload["source_term"] == "王都"
    assert payload["target_term"] == "왕도"
    assert payload["aliases"] == ["王城", "王国の都"]
    assert payload["priority"] == 80
    assert payload["is_required"] is True
    assert payload["is_active"] is True

    assert listed.status_code == 200
    assert listed.json()[0]["source_term"] == "王都"


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
