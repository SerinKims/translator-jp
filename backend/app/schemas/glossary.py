from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import GlossaryTerm
from app.db.repositories.glossary_repository import parse_aliases


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
