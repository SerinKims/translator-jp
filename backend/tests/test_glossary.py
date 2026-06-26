from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.glossary_repository import GlossaryRepository
from app.services.glossary import (
    MAX_GLOSSARY_CONTEXT_CHARS,
    MAX_GLOSSARY_TERMS_PER_CHUNK,
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
