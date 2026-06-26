from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.repositories.glossary_repository import GlossaryRepository
from app.db.session import get_db
from app.schemas.glossary import (
    GlossaryTermCreate,
    GlossaryTermResponse,
    glossary_term_to_response,
)


router = APIRouter(tags=["glossary"])


def get_glossary_repository(
    db: Annotated[Session, Depends(get_db)],
) -> GlossaryRepository:
    return GlossaryRepository(db)


@router.get("/glossary", response_model=list[GlossaryTermResponse])
def list_glossary_terms(
    repository: Annotated[GlossaryRepository, Depends(get_glossary_repository)],
) -> list[GlossaryTermResponse]:
    terms = repository.list_terms()
    return [glossary_term_to_response(term) for term in terms]


@router.post("/glossary", response_model=GlossaryTermResponse, status_code=201)
def create_glossary_term(
    request: GlossaryTermCreate,
    repository: Annotated[GlossaryRepository, Depends(get_glossary_repository)],
) -> GlossaryTermResponse:
    term = repository.create_term(
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        source_term=request.source_term,
        target_term=request.target_term,
        term_type=request.term_type,
        description=request.description,
        aliases=request.aliases,
        priority=request.priority,
        is_required=request.is_required,
        is_active=request.is_active,
    )
    return glossary_term_to_response(term)
