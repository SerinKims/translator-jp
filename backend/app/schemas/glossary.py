from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import GlossaryCandidate, GlossaryTerm
from app.db.repositories.glossary_repository import parse_aliases
from app.services.glossary import GlossaryImportResult


class GlossaryTermCreate(BaseModel):
    source_lang: str = "ja"
    target_lang: str = "ko"
    source_term: str
    target_term: str
    term_type: str = "common"
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    priority: int = 0
    is_required: bool = True
    is_active: bool = True

    @field_validator("source_lang", "target_lang", "source_term", "target_term", "term_type")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("aliases")
    @classmethod
    def clean_aliases(cls, value: list[str]) -> list[str]:
        return [alias.strip() for alias in value if alias.strip()]


class GlossaryTermUpdate(BaseModel):
    source_lang: str | None = None
    target_lang: str | None = None
    source_term: str | None = None
    target_term: str | None = None
    term_type: str | None = None
    description: str | None = None
    aliases: list[str] | None = None
    priority: int | None = None
    is_required: bool | None = None
    is_active: bool | None = None

    @field_validator("source_lang", "target_lang", "source_term", "target_term", "term_type")
    @classmethod
    def validate_optional_non_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("aliases")
    @classmethod
    def clean_optional_aliases(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [alias.strip() for alias in value if alias.strip()]


class GlossaryImportTextRequest(BaseModel):
    text: str


class GlossaryImportConflictResponse(BaseModel):
    row: int
    source_lang: str
    target_lang: str
    source_term: str
    target_term: str
    message: str


class GlossaryImportResponse(BaseModel):
    imported: int
    skipped_duplicates: int
    conflicts: list[GlossaryImportConflictResponse]


class GlossaryTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_lang: str
    target_lang: str
    source_term: str
    target_term: str
    term_type: str
    description: str | None
    aliases: list[str]
    priority: int
    is_required: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GlossaryCandidateApproveRequest(BaseModel):
    term_type: str = "common"
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    priority: int = 0
    is_required: bool = True

    @field_validator("term_type")
    @classmethod
    def validate_term_type(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("aliases")
    @classmethod
    def clean_approve_aliases(cls, value: list[str]) -> list[str]:
        return [alias.strip() for alias in value if alias.strip()]


class GlossaryCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_lang: str
    target_lang: str
    source_term: str
    suggested_target_term: str
    source_text: str
    model_translation: str
    user_corrected_translation: str
    status: str
    created_at: datetime
    updated_at: datetime


def glossary_term_to_response(term: GlossaryTerm) -> GlossaryTermResponse:
    return GlossaryTermResponse(
        id=term.id,
        source_lang=term.source_lang,
        target_lang=term.target_lang,
        source_term=term.source_term,
        target_term=term.target_term,
        term_type=term.term_type,
        description=term.description,
        aliases=parse_aliases(term.aliases),
        priority=term.priority,
        is_required=bool(term.is_required),
        is_active=bool(term.is_active),
        created_at=term.created_at,
        updated_at=term.updated_at,
    )


def glossary_import_to_response(result: GlossaryImportResult) -> GlossaryImportResponse:
    return GlossaryImportResponse(
        imported=result.imported,
        skipped_duplicates=result.skipped_duplicates,
        conflicts=[
            GlossaryImportConflictResponse(
                row=conflict.row,
                source_lang=conflict.source_lang,
                target_lang=conflict.target_lang,
                source_term=conflict.source_term,
                target_term=conflict.target_term,
                message=conflict.message,
            )
            for conflict in result.conflicts
        ],
    )


def glossary_candidate_to_response(
    candidate: GlossaryCandidate,
) -> GlossaryCandidateResponse:
    return GlossaryCandidateResponse(
        id=candidate.id,
        source_lang=candidate.source_lang,
        target_lang=candidate.target_lang,
        source_term=candidate.source_term,
        suggested_target_term=candidate.suggested_target_term,
        source_text=candidate.source_text,
        model_translation=candidate.model_translation,
        user_corrected_translation=candidate.user_corrected_translation,
        status=candidate.status,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )
