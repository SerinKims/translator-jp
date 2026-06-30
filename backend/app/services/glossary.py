from __future__ import annotations

import hashlib
import json
import csv
from dataclasses import dataclass
from io import StringIO
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.db.repositories.glossary_repository import GlossaryRepository, parse_aliases


MAX_GLOSSARY_TERMS_PER_CHUNK = 30
MAX_GLOSSARY_CONTEXT_CHARS = 1500
GLOSSARY_CONTEXT_HEADER = "[용어집 - 반드시 지킬 것]"
TERM_NOT_FOUND_MESSAGE = "용어를 찾을 수 없습니다."
CANDIDATE_NOT_FOUND_MESSAGE = "후보 용어를 찾을 수 없습니다."
DUPLICATE_TERM_MESSAGE = "이미 같은 용어가 등록되어 있습니다."
CONFLICT_TERM_MESSAGE = "같은 원어에 다른 번역어가 이미 등록되어 있습니다."
CANDIDATE_NOT_PENDING_MESSAGE = "대기 중인 후보 용어만 처리할 수 있습니다."
EMPTY_CSV_MESSAGE = "CSV 내용이 비어 있습니다."


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


@dataclass(frozen=True)
class GlossaryCreateResult:
    term: Any
    created: bool


@dataclass(frozen=True)
class GlossaryImportConflict:
    row: int
    source_lang: str
    target_lang: str
    source_term: str
    target_term: str
    message: str


@dataclass(frozen=True)
class GlossaryImportResult:
    imported: int
    skipped_duplicates: int
    conflicts: list[GlossaryImportConflict]


class GlossaryServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GlossaryDuplicateError(GlossaryServiceError):
    def __init__(self, message: str = DUPLICATE_TERM_MESSAGE) -> None:
        super().__init__(message, status_code=409)


class GlossaryConflictError(GlossaryServiceError):
    def __init__(self, message: str = CONFLICT_TERM_MESSAGE) -> None:
        super().__init__(message, status_code=409)


class GlossaryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = GlossaryRepository(db)

    def list_terms(
        self,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
        active_only: bool = False,
    ) -> list[Any]:
        return self.repository.list_terms(
            source_lang=source_lang,
            target_lang=target_lang,
            active_only=active_only,
        )

    def create_term(
        self,
        *,
        source_lang: str,
        target_lang: str,
        source_term: str,
        target_term: str,
        term_type: str = "common",
        description: str | None = None,
        aliases: list[str] | None = None,
        priority: int = 0,
        is_required: bool = True,
        is_active: bool = True,
    ) -> GlossaryCreateResult:
        existing = self._find_duplicate_or_conflict(
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            target_term=target_term,
        )
        if existing is not None:
            return GlossaryCreateResult(term=existing, created=False)

        term = self.repository.create_term(
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            target_term=target_term,
            term_type=term_type,
            description=description,
            aliases=aliases or [],
            priority=priority,
            is_required=is_required,
            is_active=is_active,
        )
        return GlossaryCreateResult(term=term, created=True)

    def update_term(self, term_id: int, **changes: Any) -> Any:
        term = self.repository.get_term(term_id)
        if term is None:
            raise GlossaryServiceError(TERM_NOT_FOUND_MESSAGE, status_code=404)

        source_lang = changes.get("source_lang", term.source_lang)
        target_lang = changes.get("target_lang", term.target_lang)
        source_term = changes.get("source_term", term.source_term)
        target_term = changes.get("target_term", term.target_term)
        self._find_duplicate_or_conflict(
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            target_term=target_term,
            ignore_term_id=term_id,
        )

        updated = self.repository.update_term(term_id, **changes)
        if updated is None:
            raise GlossaryServiceError(TERM_NOT_FOUND_MESSAGE, status_code=404)
        return updated

    def deactivate_term(self, term_id: int) -> Any:
        term = self.repository.deactivate_term(term_id)
        if term is None:
            raise GlossaryServiceError(TERM_NOT_FOUND_MESSAGE, status_code=404)
        return term

    def import_csv_text(self, text: str) -> GlossaryImportResult:
        if not text.strip():
            raise GlossaryServiceError(EMPTY_CSV_MESSAGE, status_code=400)

        imported = 0
        skipped_duplicates = 0
        conflicts: list[GlossaryImportConflict] = []
        reader = csv.DictReader(StringIO(text))
        for row_number, row in enumerate(reader, start=2):
            payload = _csv_row_to_payload(row)
            try:
                result = self.create_term(**payload)
            except GlossaryConflictError as exc:
                conflicts.append(
                    GlossaryImportConflict(
                        row=row_number,
                        source_lang=payload["source_lang"],
                        target_lang=payload["target_lang"],
                        source_term=payload["source_term"],
                        target_term=payload["target_term"],
                        message=exc.message,
                    )
                )
                continue
            if result.created:
                imported += 1
            else:
                skipped_duplicates += 1

        return GlossaryImportResult(
            imported=imported,
            skipped_duplicates=skipped_duplicates,
            conflicts=conflicts,
        )

    def list_candidates(self, *, status: str | None = None) -> list[Any]:
        return self.repository.list_candidates(status=status)

    def create_candidate_from_feedback(
        self,
        *,
        source_lang: str = "ja",
        target_lang: str = "ko",
        source_term: str,
        suggested_target_term: str,
        source_text: str,
        model_translation: str,
        user_corrected_translation: str,
    ) -> Any | None:
        if model_translation == user_corrected_translation:
            return None
        return self.repository.create_candidate(
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            suggested_target_term=suggested_target_term,
            source_text=source_text,
            model_translation=model_translation,
            user_corrected_translation=user_corrected_translation,
        )

    def approve_candidate(
        self,
        candidate_id: int,
        *,
        term_type: str = "common",
        description: str | None = None,
        aliases: list[str] | None = None,
        priority: int = 0,
        is_required: bool = True,
    ) -> Any:
        candidate = self.repository.get_candidate(candidate_id)
        if candidate is None:
            raise GlossaryServiceError(CANDIDATE_NOT_FOUND_MESSAGE, status_code=404)
        if candidate.status != "pending":
            raise GlossaryServiceError(CANDIDATE_NOT_PENDING_MESSAGE, status_code=400)

        self._find_duplicate_or_conflict(
            source_lang=candidate.source_lang,
            target_lang=candidate.target_lang,
            source_term=candidate.source_term,
            target_term=candidate.suggested_target_term,
            raise_duplicate=True,
        )
        try:
            self.repository.create_term(
                source_lang=candidate.source_lang,
                target_lang=candidate.target_lang,
                source_term=candidate.source_term,
                target_term=candidate.suggested_target_term,
                term_type=term_type,
                description=description,
                aliases=aliases or [],
                priority=priority,
                is_required=is_required,
                is_active=True,
                commit=False,
            )
            self.repository.update_candidate_status(
                candidate_id,
                status="approved",
                commit=False,
            )
            self.db.commit()
            self.db.refresh(candidate)
        except Exception:
            self.db.rollback()
            raise
        return candidate

    def reject_candidate(self, candidate_id: int) -> Any:
        candidate = self.repository.update_candidate_status(candidate_id, status="rejected")
        if candidate is None:
            raise GlossaryServiceError(CANDIDATE_NOT_FOUND_MESSAGE, status_code=404)
        return candidate

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

    def _find_duplicate_or_conflict(
        self,
        *,
        source_lang: str,
        target_lang: str,
        source_term: str,
        target_term: str,
        ignore_term_id: int | None = None,
        raise_duplicate: bool = False,
    ) -> Any | None:
        matches = self.repository.find_terms_by_source(
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
        )
        for term in matches:
            if ignore_term_id is not None and term.id == ignore_term_id:
                continue
            if term.target_term == target_term:
                if raise_duplicate:
                    raise GlossaryDuplicateError()
                return term
            raise GlossaryConflictError()
        return None


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
        if not term.is_active:
            continue
        line = f"{term.source_term}={term.target_term}"
        candidate = "\n".join([*lines, line])
        if len(candidate) > max_chars:
            break
        lines.append(line)

    return "\n".join(lines) if len(lines) > 1 else ""


def make_selected_glossary_hash(selected_terms: Iterable[Any]) -> str:
    normalized = [
        _term_to_cache_dict(term)
        for term in (_to_selected_term(term) for term in selected_terms)
        if term.is_active
    ]
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


def _csv_row_to_payload(row: dict[str, str | None]) -> dict[str, Any]:
    return {
        "source_lang": _clean_csv_value(row.get("source_lang")) or "ja",
        "target_lang": _clean_csv_value(row.get("target_lang")) or "ko",
        "source_term": _required_csv_value(row, "source_term"),
        "target_term": _required_csv_value(row, "target_term"),
        "term_type": _clean_csv_value(row.get("term_type")) or "common",
        "priority": _parse_int(_clean_csv_value(row.get("priority")), default=0),
        "is_required": _parse_bool(_clean_csv_value(row.get("is_required")), default=True),
        "description": _clean_csv_value(row.get("description")),
        "aliases": _parse_alias_csv(_clean_csv_value(row.get("aliases"))),
    }


def _required_csv_value(row: dict[str, str | None], field_name: str) -> str:
    value = _clean_csv_value(row.get(field_name))
    if not value:
        raise GlossaryServiceError(f"CSV의 {field_name} 값이 비어 있습니다.", status_code=400)
    return value


def _clean_csv_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_int(value: str | None, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise GlossaryServiceError("CSV의 priority 값은 정수여야 합니다.", status_code=400) from exc


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise GlossaryServiceError(
        "CSV의 is_required 값은 true 또는 false여야 합니다.",
        status_code=400,
    )


def _parse_alias_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [alias.strip() for alias in value.split("|") if alias.strip()]
