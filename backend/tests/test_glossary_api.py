from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.services.glossary import GlossaryService


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


def test_glossary_api_duplicate_and_conflict(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)

    try:
        client = TestClient(app)
        first = client.post(
            "/api/glossary",
            json={"source_term": "王都", "target_term": "왕도"},
        )
        duplicate = client.post(
            "/api/glossary",
            json={"source_term": "王都", "target_term": "왕도"},
        )
        conflict = client.post(
            "/api/glossary",
            json={"source_term": "王都", "target_term": "수도"},
        )
        listed = client.get("/api/glossary")
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 201
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == first.json()["id"]
    assert conflict.status_code == 409
    assert "다른 번역어" in conflict.json()["detail"]
    assert len(listed.json()) == 1


def test_glossary_api_patch_and_delete_soft_deactivate(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)

    try:
        client = TestClient(app)
        created = client.post(
            "/api/glossary",
            json={"source_term": "魔王", "target_term": "마왕"},
        )
        term_id = created.json()["id"]
        patched = client.patch(
            f"/api/glossary/{term_id}",
            json={"target_term": "마왕님", "priority": 90},
        )
        deleted = client.delete(f"/api/glossary/{term_id}")
    finally:
        app.dependency_overrides.clear()

    assert patched.status_code == 200
    assert patched.json()["target_term"] == "마왕님"
    assert patched.json()["priority"] == 90
    assert deleted.status_code == 200
    assert deleted.json()["is_active"] is False


def test_glossary_api_import_csv_text_body(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    csv_text = """source_lang,target_lang,source_term,target_term,term_type,priority,is_required,description,aliases
ja,ko,王都,왕도,place,80,true,판타지 문맥에서는 수도보다 왕도가 자연스러움,王城|王国の都
ja,ko,王都,왕도,place,80,true,duplicate,
ja,ko,王都,수도,place,80,true,conflict,
ja,ko,魔王,마왕,title,90,true,판타지 기본 용어,
"""

    try:
        client = TestClient(app)
        imported = client.post(
            "/api/glossary/import",
            content=csv_text.encode("utf-8"),
            headers={"content-type": "text/csv; charset=utf-8"},
        )
    finally:
        app.dependency_overrides.clear()

    assert imported.status_code == 200
    payload = imported.json()
    assert payload["imported"] == 2
    assert payload["skipped_duplicates"] == 1
    assert len(payload["conflicts"]) == 1


def test_glossary_api_import_json_text(db_session: Session) -> None:
    app.dependency_overrides[get_db] = _override_db(db_session)
    csv_text = "source_lang,target_lang,source_term,target_term\nja,ko,姫様,공주님\n"

    try:
        client = TestClient(app)
        imported = client.post("/api/glossary/import", json={"text": csv_text})
    finally:
        app.dependency_overrides.clear()

    assert imported.status_code == 200
    assert imported.json()["imported"] == 1


def test_glossary_candidate_api_approve_and_reject(db_session: Session) -> None:
    service = GlossaryService(db_session)
    approve_candidate = service.create_candidate_from_feedback(
        source_term="王都",
        suggested_target_term="왕도",
        source_text="王都の空を見上げた。",
        model_translation="수도의 하늘을 올려다보았다.",
        user_corrected_translation="왕도의 하늘을 올려다보았다.",
    )
    reject_candidate = service.create_candidate_from_feedback(
        source_term="姫様",
        suggested_target_term="공주님",
        source_text="姫様が笑った。",
        model_translation="아가씨가 웃었다.",
        user_corrected_translation="공주님이 웃었다.",
    )
    assert approve_candidate is not None
    assert reject_candidate is not None
    app.dependency_overrides[get_db] = _override_db(db_session)

    try:
        client = TestClient(app)
        listed = client.get("/api/glossary/candidates")
        approved = client.post(
            f"/api/glossary/candidates/{approve_candidate.id}/approve",
            json={"term_type": "place", "priority": 80},
        )
        rejected = client.post(f"/api/glossary/candidates/{reject_candidate.id}/reject")
    finally:
        app.dependency_overrides.clear()

    assert listed.status_code == 200
    assert len(listed.json()) == 2
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_glossary_candidate_api_approve_conflict_keeps_pending(db_session: Session) -> None:
    service = GlossaryService(db_session)
    service.create_term(source_term="王都", target_term="왕도", source_lang="ja", target_lang="ko")
    candidate = service.create_candidate_from_feedback(
        source_term="王都",
        suggested_target_term="수도",
        source_text="王都の空を見上げた。",
        model_translation="수도의 하늘을 올려다보았다.",
        user_corrected_translation="왕도의 하늘을 올려다보았다.",
    )
    assert candidate is not None
    app.dependency_overrides[get_db] = _override_db(db_session)

    try:
        client = TestClient(app)
        approved = client.post(f"/api/glossary/candidates/{candidate.id}/approve")
        listed = client.get("/api/glossary/candidates?status=pending")
    finally:
        app.dependency_overrides.clear()

    assert approved.status_code == 409
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == candidate.id
    assert listed.json()[0]["status"] == "pending"


def _override_db(db_session: Session):
    def _get_db() -> Generator[Session, None, None]:
        yield db_session

    return _get_db
