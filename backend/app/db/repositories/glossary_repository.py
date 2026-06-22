from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GlossarySet, GlossaryTerm


class GlossaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_set(
        self,
        *,
        name: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> GlossarySet:
        glossary_set = GlossarySet(
            name=name,
            description=description,
            is_active=int(is_active),
        )
        self.db.add(glossary_set)
        self.db.commit()
        self.db.refresh(glossary_set)
        return glossary_set

    def create_term(
        self,
        *,
        source_term: str,
        target_term: str,
        glossary_set_id: int | None = None,
        term_type: str = "common",
        description: str | None = None,
        is_case_sensitive: bool = False,
        is_active: bool = True,
    ) -> GlossaryTerm:
        term = GlossaryTerm(
            glossary_set_id=glossary_set_id,
            source_term=source_term,
            target_term=target_term,
            term_type=term_type,
            description=description,
            is_case_sensitive=int(is_case_sensitive),
            is_active=int(is_active),
        )
        self.db.add(term)
        self.db.commit()
        self.db.refresh(term)
        return term

    def list_active_terms(self) -> list[GlossaryTerm]:
        statement = (
            select(GlossaryTerm)
            .where(GlossaryTerm.is_active == 1)
            .order_by(GlossaryTerm.source_term)
        )
        return list(self.db.scalars(statement))
