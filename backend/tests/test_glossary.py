from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.glossary_repository import GlossaryRepository
from app.services.glossary import (
    MAX_GLOSSARY_CONTEXT_CHARS,
    MAX_GLOSSARY_TERMS_PER_CHUNK,
    GlossaryConflictError,
    GlossaryDuplicateError,
    GlossaryService,
    build_glossary_context,
    check_glossary_violations,
    make_selected_glossary_hash,
    select_glossary_terms_for_text,
)


def test_create_and_list_glossary_term(db_session: Session) -> None:
    repository = GlossaryRepository(db_session)

    created = repository.create_term(
        source_lang="ja",
        target_lang="ko",
        source_term="王都",
        target_term="왕도",
        term_type="place",
        description="판타지 문맥에서는 수도보다 왕도가 자연스러움",
        aliases=["王城", "王国の都"],
        priority=80,
        is_required=True,
    )
    terms = repository.list_terms()

    assert created.id == 1
    assert len(terms) == 1
    assert terms[0].source_lang == "ja"
    assert terms[0].target_lang == "ko"
    assert terms[0].source_term == "王都"
    assert terms[0].target_term == "왕도"
    assert terms[0].priority == 80
    assert terms[0].is_required == 1


def test_service_adds_single_glossary_term(db_session: Session) -> None:
    service = GlossaryService(db_session)

    result = service.create_term(
        source_lang="ja",
        target_lang="ko",
        source_term="王都",
        target_term="왕도",
        term_type="place",
        priority=80,
    )

    assert result.created is True
    assert result.term.source_term == "王都"
    assert result.term.target_term == "왕도"


def test_service_prevents_duplicate_terms(db_session: Session) -> None:
    service = GlossaryService(db_session)
    first = service.create_term(
        source_term="王都",
        target_term="왕도",
        source_lang="ja",
        target_lang="ko",
    )

    second = service.create_term(
        source_term="王都",
        target_term="왕도",
        source_lang="ja",
        target_lang="ko",
    )

    assert first.created is True
    assert second.created is False
    assert second.term.id == first.term.id
    assert len(service.list_terms()) == 1


def test_service_detects_conflicting_terms(db_session: Session) -> None:
    service = GlossaryService(db_session)
    service.create_term(source_term="王都", target_term="왕도", source_lang="ja", target_lang="ko")

    try:
        service.create_term(
            source_term="王都",
            target_term="수도",
            source_lang="ja",
            target_lang="ko",
        )
    except GlossaryConflictError as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("conflict was not detected")


def test_service_updates_glossary_term(db_session: Session) -> None:
    service = GlossaryService(db_session)
    created = service.create_term(
        source_term="魔王",
        target_term="마왕",
        source_lang="ja",
        target_lang="ko",
    )

    updated = service.update_term(
        created.term.id,
        target_term="마왕님",
        priority=95,
        aliases=["魔王様"],
    )

    assert updated.target_term == "마왕님"
    assert updated.priority == 95
    assert "魔王様" in updated.aliases


def test_service_deactivates_glossary_term(db_session: Session) -> None:
    service = GlossaryService(db_session)
    created = service.create_term(
        source_term="姫様",
        target_term="공주님",
        source_lang="ja",
        target_lang="ko",
    )

    deactivated = service.deactivate_term(created.term.id)

    assert deactivated.is_active == 0
    assert service.list_terms(active_only=True) == []


def test_csv_import_applies_duplicate_and_conflict_policy(db_session: Session) -> None:
    service = GlossaryService(db_session)
    csv_text = """source_lang,target_lang,source_term,target_term,term_type,priority,is_required,description,aliases
ja,ko,王都,왕도,place,80,true,판타지 문맥에서는 수도보다 왕도가 자연스러움,王城|王国の都
ja,ko,王都,왕도,place,80,true,duplicate,王城
ja,ko,王都,수도,place,80,true,conflict,
ja,ko,魔王,마왕,title,90,true,판타지 기본 용어,
"""

    result = service.import_csv_text(csv_text)

    assert result.imported == 2
    assert result.skipped_duplicates == 1
    assert len(result.conflicts) == 1
    assert result.conflicts[0].source_term == "王都"
    assert len(service.list_terms()) == 2


def test_create_candidate_from_feedback(db_session: Session) -> None:
    service = GlossaryService(db_session)

    candidate = service.create_candidate_from_feedback(
        source_lang="ja",
        target_lang="ko",
        source_term="王都",
        suggested_target_term="왕도",
        source_text="王都の空を見上げた。",
        model_translation="수도의 하늘을 올려다보았다.",
        user_corrected_translation="왕도의 하늘을 올려다보았다.",
    )

    assert candidate is not None
    assert candidate.status == "pending"
    assert candidate.source_term == "王都"


def test_approve_candidate_creates_term_and_updates_status(db_session: Session) -> None:
    service = GlossaryService(db_session)
    candidate = service.create_candidate_from_feedback(
        source_term="王都",
        suggested_target_term="왕도",
        source_text="王都の空を見上げた。",
        model_translation="수도의 하늘을 올려다보았다.",
        user_corrected_translation="왕도의 하늘을 올려다보았다.",
    )
    assert candidate is not None

    approved = service.approve_candidate(candidate.id, term_type="place", priority=80)

    assert approved.status == "approved"
    terms = service.list_terms()
    assert len(terms) == 1
    assert terms[0].source_term == "王都"
    assert terms[0].target_term == "왕도"


def test_reject_candidate_updates_status_without_creating_term(db_session: Session) -> None:
    service = GlossaryService(db_session)
    candidate = service.create_candidate_from_feedback(
        source_term="王都",
        suggested_target_term="왕도",
        source_text="王都の空を見上げた。",
        model_translation="수도의 하늘을 올려다보았다.",
        user_corrected_translation="왕도의 하늘을 올려다보았다.",
    )
    assert candidate is not None

    rejected = service.reject_candidate(candidate.id)

    assert rejected.status == "rejected"
    assert service.list_terms() == []


def test_approve_candidate_duplicate_or_conflict_keeps_candidate_pending(
    db_session: Session,
) -> None:
    service = GlossaryService(db_session)
    service.create_term(source_term="王都", target_term="왕도", source_lang="ja", target_lang="ko")
    duplicate = service.create_candidate_from_feedback(
        source_term="王都",
        suggested_target_term="왕도",
        source_text="王都の空を見上げた。",
        model_translation="수도의 하늘을 올려다보았다.",
        user_corrected_translation="왕도의 하늘을 올려다보았다.",
    )
    conflict = service.create_candidate_from_feedback(
        source_term="王都",
        suggested_target_term="수도",
        source_text="王都の空を見上げた。",
        model_translation="수도의 하늘을 올려다보았다.",
        user_corrected_translation="왕도의 하늘을 올려다보았다.",
    )
    assert duplicate is not None
    assert conflict is not None

    for candidate, expected_error in (
        (duplicate, GlossaryDuplicateError),
        (conflict, GlossaryConflictError),
    ):
        try:
            service.approve_candidate(candidate.id)
        except expected_error:
            pass
        else:
            raise AssertionError("approve policy error was not raised")
        assert service.repository.get_candidate(candidate.id).status == "pending"


def test_selects_source_term_in_source_text() -> None:
    selected = select_glossary_terms_for_text(
        "王都の門が開いた。",
        [{"source_term": "王都", "target_term": "왕도"}],
    )

    assert [term.source_term for term in selected] == ["王都"]


def test_selects_alias_in_source_text() -> None:
    selected = select_glossary_terms_for_text(
        "王城の門が開いた。",
        [{"source_term": "王都", "target_term": "왕도", "aliases": ["王城"]}],
    )

    assert [term.source_term for term in selected] == ["王都"]


def test_filters_source_lang_target_lang_and_inactive_terms() -> None:
    terms = [
        {"source_lang": "en", "target_lang": "ko", "source_term": "王都", "target_term": "왕도"},
        {
            "source_lang": "ja",
            "target_lang": "en",
            "source_term": "王都",
            "target_term": "royal capital",
        },
        {
            "source_lang": "ja",
            "target_lang": "ko",
            "source_term": "王都",
            "target_term": "왕도",
            "is_active": False,
        },
        {"source_lang": "ja", "target_lang": "ko", "source_term": "魔王", "target_term": "마왕"},
    ]

    selected = select_glossary_terms_for_text(
        "王都で魔王が笑った。",
        terms,
        source_lang="ja",
        target_lang="ko",
    )

    assert [term.source_term for term in selected] == ["魔王"]


def test_selected_terms_are_sorted_by_policy() -> None:
    terms = [
        {"source_term": "王", "target_term": "왕", "priority": 100, "is_required": False},
        {"source_term": "王都", "target_term": "왕도", "priority": 80, "is_required": True},
        {"source_term": "姫様", "target_term": "공주님", "priority": 90, "is_required": True},
        {"source_term": "魔王", "target_term": "마왕", "priority": 90, "is_required": True},
    ]

    selected = select_glossary_terms_for_text("王都で魔王と姫様と王が会った。", terms)

    assert [term.source_term for term in selected] == ["姫様", "魔王", "王都", "王"]


def test_builds_glossary_prompt_context() -> None:
    selected = select_glossary_terms_for_text(
        "魔王は王都で姫様に会った。",
        [
            {"source_term": "魔王", "target_term": "마왕", "priority": 100},
            {"source_term": "王都", "target_term": "왕도", "priority": 80},
            {"source_term": "姫様", "target_term": "공주님", "priority": 70},
        ],
    )

    assert build_glossary_context(selected) == (
        "[용어집 - 반드시 지킬 것]\n魔王=마왕\n王都=왕도\n姫様=공주님"
    )


def test_max_terms_per_chunk_limit() -> None:
    terms = [
        {"source_term": f"用語{i:02d}", "target_term": f"용어{i:02d}"}
        for i in range(MAX_GLOSSARY_TERMS_PER_CHUNK + 5)
    ]
    source_text = " ".join(term["source_term"] for term in terms)

    selected = select_glossary_terms_for_text(source_text, terms)

    assert len(selected) == MAX_GLOSSARY_TERMS_PER_CHUNK


def test_max_context_chars_limit() -> None:
    selected = [
        {"source_term": f"長い用語{i:02d}", "target_term": "아주긴번역어" * 20} for i in range(100)
    ]

    context = build_glossary_context(selected)

    assert len(context) <= MAX_GLOSSARY_CONTEXT_CHARS


def test_selected_glossary_hash_uses_only_selected_terms() -> None:
    selected = select_glossary_terms_for_text(
        "魔王が笑った。",
        [
            {"source_term": "魔王", "target_term": "마왕"},
            {"source_term": "王都", "target_term": "왕도"},
        ],
    )
    selected_again = select_glossary_terms_for_text(
        "魔王が笑った。",
        [
            {"source_term": "魔王", "target_term": "마왕"},
            {"source_term": "勇者", "target_term": "용사"},
        ],
    )

    assert make_selected_glossary_hash(selected) == make_selected_glossary_hash(selected_again)


def test_glossary_violation_check() -> None:
    selected = select_glossary_terms_for_text(
        "王城の門が開いた。",
        [{"source_term": "王都", "target_term": "왕도", "aliases": ["王城"], "is_required": True}],
    )

    violations = check_glossary_violations(
        source_text="王城の門が開いた。",
        translated_text="수도의 문이 열렸다.",
        selected_terms=selected,
    )

    assert len(violations) == 1
    assert violations[0].source_term == "王都"
    assert violations[0].target_term == "왕도"
    assert violations[0].matched_source == "王城"


def test_inactive_terms_are_excluded_from_prompt_context() -> None:
    selected = select_glossary_terms_for_text(
        "王都で魔王が会った。",
        [
            {"source_term": "王都", "target_term": "왕도", "is_active": False},
            {"source_term": "魔王", "target_term": "마왕", "is_active": True},
        ],
    )

    context = build_glossary_context(selected)

    assert "王都=왕도" not in context
    assert "魔王=마왕" in context


def test_inactive_terms_are_excluded_from_glossary_hash() -> None:
    active_only_hash = make_selected_glossary_hash(
        [{"source_term": "魔王", "target_term": "마왕", "is_active": True}]
    )
    with_inactive_hash = make_selected_glossary_hash(
        [
            {"source_term": "魔王", "target_term": "마왕", "is_active": True},
            {"source_term": "王都", "target_term": "왕도", "is_active": False},
        ]
    )

    assert with_inactive_hash == active_only_hash
