from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import GlossaryCandidate, GlossarySet, GlossaryTerm


class GlossaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._ensure_sqlite_glossary_columns()

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
        source_lang: str = "ja",
        target_lang: str = "ko",
        glossary_set_id: int | None = None,
        term_type: str = "common",
        description: str | None = None,
        aliases: list[str] | None = None,
        priority: int = 0,
        is_required: bool = True,
        is_case_sensitive: bool = False,
        is_active: bool = True,
        commit: bool = True,
    ) -> GlossaryTerm:
        term = GlossaryTerm(
            glossary_set_id=glossary_set_id,
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            target_term=target_term,
            term_type=term_type,
            description=description,
            aliases=self._dump_aliases(aliases or []),
            priority=priority,
            is_required=int(is_required),
            is_case_sensitive=int(is_case_sensitive),
            is_active=int(is_active),
        )
        self.db.add(term)
        if commit:
            self.db.commit()
            self.db.refresh(term)
        else:
            self.db.flush()
        return term

    def get_term(self, term_id: int) -> GlossaryTerm | None:
        return self.db.get(GlossaryTerm, term_id)

    def find_terms_by_source(
        self,
        *,
        source_lang: str,
        target_lang: str,
        source_term: str,
    ) -> list[GlossaryTerm]:
        statement = select(GlossaryTerm).where(
            GlossaryTerm.source_lang == source_lang,
            GlossaryTerm.target_lang == target_lang,
            GlossaryTerm.source_term == source_term,
        )
        return list(self.db.scalars(statement))

    def update_term(
        self,
        term_id: int,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
        source_term: str | None = None,
        target_term: str | None = None,
        term_type: str | None = None,
        description: str | None = None,
        aliases: list[str] | None = None,
        priority: int | None = None,
        is_required: bool | None = None,
        is_active: bool | None = None,
        commit: bool = True,
    ) -> GlossaryTerm | None:
        term = self.get_term(term_id)
        if term is None:
            return None

        if source_lang is not None:
            term.source_lang = source_lang
        if target_lang is not None:
            term.target_lang = target_lang
        if source_term is not None:
            term.source_term = source_term
        if target_term is not None:
            term.target_term = target_term
        if term_type is not None:
            term.term_type = term_type
        if description is not None:
            term.description = description
        if aliases is not None:
            term.aliases = self._dump_aliases(aliases)
        if priority is not None:
            term.priority = priority
        if is_required is not None:
            term.is_required = int(is_required)
        if is_active is not None:
            term.is_active = int(is_active)

        if commit:
            self.db.commit()
            self.db.refresh(term)
        else:
            self.db.flush()
        return term

    def deactivate_term(self, term_id: int) -> GlossaryTerm | None:
        return self.update_term(term_id, is_active=False)

    def list_terms(
        self,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
        active_only: bool = False,
    ) -> list[GlossaryTerm]:
        statement = select(GlossaryTerm)
        if active_only:
            statement = statement.where(GlossaryTerm.is_active == 1)
        if source_lang is not None:
            statement = statement.where(GlossaryTerm.source_lang == source_lang)
        if target_lang is not None:
            statement = statement.where(GlossaryTerm.target_lang == target_lang)
        statement = statement.order_by(
            GlossaryTerm.is_required.desc(),
            GlossaryTerm.priority.desc(),
            GlossaryTerm.source_term,
            GlossaryTerm.id,
        )
        return list(self.db.scalars(statement))

    def list_active_terms(
        self,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
    ) -> list[GlossaryTerm]:
        return self.list_terms(
            source_lang=source_lang,
            target_lang=target_lang,
            active_only=True,
        )

    def create_candidate(
        self,
        *,
        source_lang: str,
        target_lang: str,
        source_term: str,
        suggested_target_term: str,
        source_text: str,
        model_translation: str,
        user_corrected_translation: str,
        status: str = "pending",
        commit: bool = True,
    ) -> GlossaryCandidate:
        candidate = GlossaryCandidate(
            source_lang=source_lang,
            target_lang=target_lang,
            source_term=source_term,
            suggested_target_term=suggested_target_term,
            source_text=source_text,
            model_translation=model_translation,
            user_corrected_translation=user_corrected_translation,
            status=status,
        )
        self.db.add(candidate)
        if commit:
            self.db.commit()
            self.db.refresh(candidate)
        else:
            self.db.flush()
        return candidate

    def get_candidate(self, candidate_id: int) -> GlossaryCandidate | None:
        return self.db.get(GlossaryCandidate, candidate_id)

    def list_candidates(self, *, status: str | None = None) -> list[GlossaryCandidate]:
        statement = select(GlossaryCandidate)
        if status is not None:
            statement = statement.where(GlossaryCandidate.status == status)
        statement = statement.order_by(
            GlossaryCandidate.created_at.desc(),
            GlossaryCandidate.id.desc(),
        )
        return list(self.db.scalars(statement))

    def update_candidate_status(
        self,
        candidate_id: int,
        *,
        status: str,
        commit: bool = True,
    ) -> GlossaryCandidate | None:
        candidate = self.get_candidate(candidate_id)
        if candidate is None:
            return None
        candidate.status = status
        if commit:
            self.db.commit()
            self.db.refresh(candidate)
        else:
            self.db.flush()
        return candidate

    def _dump_aliases(self, aliases: list[str]) -> str:
        cleaned = [alias for alias in aliases if alias]
        return json.dumps(cleaned, ensure_ascii=False)

    def _ensure_sqlite_glossary_columns(self) -> None:
        bind = self.db.get_bind()
        if bind.dialect.name != "sqlite":
            return

        self.db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS glossary_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT NOT NULL DEFAULT 'ja',
                    target_lang TEXT NOT NULL DEFAULT 'ko',
                    source_term TEXT NOT NULL,
                    suggested_target_term TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    model_translation TEXT NOT NULL,
                    user_corrected_translation TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'approved', 'rejected')),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        self.db.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_glossary_candidates_status "
                "ON glossary_candidates(status)"
            )
        )
        self.db.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS trg_glossary_candidates_updated_at
                AFTER UPDATE ON glossary_candidates
                FOR EACH ROW
                BEGIN
                    UPDATE glossary_candidates
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = OLD.id;
                END
                """
            )
        )

        rows = self.db.execute(text("PRAGMA table_info(glossary_terms)")).mappings().all()
        if not rows:
            self.db.commit()
            return

        existing_columns = {str(row["name"]) for row in rows}
        migrations = {
            "source_lang": "ALTER TABLE glossary_terms ADD COLUMN source_lang TEXT NOT NULL DEFAULT 'ja'",
            "target_lang": "ALTER TABLE glossary_terms ADD COLUMN target_lang TEXT NOT NULL DEFAULT 'ko'",
            "aliases": "ALTER TABLE glossary_terms ADD COLUMN aliases TEXT",
            "priority": "ALTER TABLE glossary_terms ADD COLUMN priority INTEGER NOT NULL DEFAULT 0",
            "is_required": "ALTER TABLE glossary_terms ADD COLUMN is_required INTEGER NOT NULL DEFAULT 1",
        }
        changed = False
        for column_name, statement in migrations.items():
            if column_name in existing_columns:
                continue
            self.db.execute(text(statement))
            changed = True
        if changed:
            self.db.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_glossary_terms_lang "
                    "ON glossary_terms(source_lang, target_lang)"
                )
            )
        self.db.commit()


def parse_aliases(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]
