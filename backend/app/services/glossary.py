from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.db.repositories.glossary_repository import GlossaryRepository, parse_aliases


MAX_GLOSSARY_TERMS_PER_CHUNK = 30
MAX_GLOSSARY_CONTEXT_CHARS = 1500
GLOSSARY_CONTEXT_HEADER = "[용어집 - 반드시 지킬 것]"


@dataclass(frozen=True)
class SelectedGlossaryTerm:
    source_term: str
    target_term: str
    term_type: str
    description: str | None
    aliases: tuple[str, ...] = ()
    priority: int = 0
    is_required: bool = True
    is_active: bool = True
    source_lang: str = "ja"
    target_lang: str = "ko"
    is_case_sensitive: bool = False


@dataclass(frozen=True)
class GlossaryViolation:
    source_term: str
    target_term: str
    matched_source: str
    is_required: bool


class GlossaryService:
    def __init__(self, db: Session) -> None:
        self.repository = GlossaryRepository(db)

    def select_terms_for_text(
        self,
        source_text: str,
        *,
        source_lang: str,
        target_lang: str,
    ) -> list[SelectedGlossaryTerm]:
        terms = self.repository.list_active_terms(
            source_lang=source_lang,
            target_lang=target_lang,
        )
        return select_glossary_terms_for_text(
            source_text,
            terms,
            source_lang=source_lang,
            target_lang=target_lang,
        )


def select_glossary_terms_for_text(
    source_text: str,
    glossary_terms: Iterable[Any],
    *,
    source_lang: str | None = None,
    target_lang: str | None = None,
    max_terms: int = MAX_GLOSSARY_TERMS_PER_CHUNK,
) -> list[SelectedGlossaryTerm]:
    selected: list[SelectedGlossaryTerm] = []
    seen: set[tuple[str, str, str, str]] = set()
    for term in glossary_terms:
        selected_term = _to_selected_term(term)
        if not selected_term.is_active:
            continue
        if source_lang is not None and selected_term.source_lang != source_lang:
            continue
        if target_lang is not None and selected_term.target_lang != target_lang:
            continue
        if not selected_term.source_term:
            continue
        if not _find_matched_expression(source_text, selected_term):
            continue

        dedupe_key = (
            selected_term.source_lang,
            selected_term.target_lang,
            selected_term.source_term,
            selected_term.target_term,
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        selected.append(selected_term)

    selected.sort(key=_selection_sort_key)
    return selected[:max_terms]


def build_glossary_context(
    selected_terms: Iterable[Any],
    *,
    max_chars: int = MAX_GLOSSARY_CONTEXT_CHARS,
) -> str:
    lines = [GLOSSARY_CONTEXT_HEADER]
    for term_like in selected_terms:
        term = _to_selected_term(term_like)
        line = f"{term.source_term}={term.target_term}"
        candidate = "\n".join([*lines, line])
        if len(candidate) > max_chars:
            break
        lines.append(line)

    return "\n".join(lines) if len(lines) > 1 else ""


def make_selected_glossary_hash(selected_terms: Iterable[Any]) -> str:
    normalized = [_term_to_cache_dict(_to_selected_term(term)) for term in selected_terms]
    normalized.sort(
        key=lambda item: (
            item["is_required"] is not True,
            -item["priority"],
            -len(item["source_term"]),
            item["source_term"],
            item["target_term"],
        )
    )
    return _sha256_json(normalized)


def make_selected_glossary_hash_for_text(
    source_text: str,
    glossary_terms: Iterable[Any],
    *,
    source_lang: str | None = None,
    target_lang: str | None = None,
) -> str:
    selected_terms = select_glossary_terms_for_text(
        source_text,
        glossary_terms,
        source_lang=source_lang,
        target_lang=target_lang,
    )
    return make_selected_glossary_hash(selected_terms)


def check_glossary_violations(
    *,
    source_text: str,
    translated_text: str,
    selected_terms: Iterable[Any],
    required_only: bool = True,
) -> list[GlossaryViolation]:
    violations: list[GlossaryViolation] = []
    for term_like in selected_terms:
        term = _to_selected_term(term_like)
        if required_only and not term.is_required:
            continue
        matched_source = _find_matched_expression(source_text, term)
        if matched_source is None:
            continue
        if term.target_term not in translated_text:
            violations.append(
                GlossaryViolation(
                    source_term=term.source_term,
                    target_term=term.target_term,
                    matched_source=matched_source,
                    is_required=term.is_required,
                )
            )
    return violations


def _selection_sort_key(term: SelectedGlossaryTerm) -> tuple[bool, int, int, str]:
    return (
        not term.is_required,
        -term.priority,
        -len(term.source_term),
        term.source_term,
    )


def _find_matched_expression(source_text: str, term: SelectedGlossaryTerm) -> str | None:
    haystack = source_text if term.is_case_sensitive else source_text.lower()
    for expression in (term.source_term, *term.aliases):
        if not expression:
            continue
        needle = expression if term.is_case_sensitive else expression.lower()
        if needle in haystack:
            return expression
    return None


def _to_selected_term(term: Any) -> SelectedGlossaryTerm:
    if isinstance(term, SelectedGlossaryTerm):
        return term
    return SelectedGlossaryTerm(
        source_term=str(_get_term_value(term, "source_term", "") or ""),
        target_term=str(_get_term_value(term, "target_term", "") or ""),
        term_type=str(_get_term_value(term, "term_type", "common") or "common"),
        description=_get_optional_str(term, "description"),
        aliases=tuple(parse_aliases(_get_term_value(term, "aliases", []))),
        priority=int(_get_term_value(term, "priority", 0) or 0),
        is_required=bool(_get_term_value(term, "is_required", True)),
        is_active=bool(_get_term_value(term, "is_active", True)),
        source_lang=str(_get_term_value(term, "source_lang", "ja") or "ja"),
        target_lang=str(_get_term_value(term, "target_lang", "ko") or "ko"),
        is_case_sensitive=bool(_get_term_value(term, "is_case_sensitive", False)),
    )


def _get_term_value(term: Any, name: str, default: Any) -> Any:
    if isinstance(term, dict):
        return term.get(name, default)
    return getattr(term, name, default)


def _get_optional_str(term: Any, name: str) -> str | None:
    value = _get_term_value(term, name, None)
    if value is None:
        return None
    return str(value)


def _term_to_cache_dict(term: SelectedGlossaryTerm) -> dict[str, Any]:
    return {
        "source_lang": term.source_lang,
        "target_lang": term.target_lang,
        "source_term": term.source_term,
        "target_term": term.target_term,
        "term_type": term.term_type,
        "description": term.description,
        "aliases": list(term.aliases),
        "priority": term.priority,
        "is_required": term.is_required,
    }


def _sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_hex(raw)


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
