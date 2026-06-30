from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.glossary import (
    GlossaryCandidateApproveRequest,
    GlossaryCandidateResponse,
    GlossaryImportResponse,
    GlossaryTermCreate,
    GlossaryTermResponse,
    GlossaryTermUpdate,
    glossary_candidate_to_response,
    glossary_import_to_response,
    glossary_term_to_response,
)
from app.services.glossary import GlossaryService, GlossaryServiceError


router = APIRouter(tags=["glossary"])


def get_glossary_service(
    db: Annotated[Session, Depends(get_db)],
) -> GlossaryService:
    return GlossaryService(db)


@router.get("/glossary", response_model=list[GlossaryTermResponse])
def list_glossary_terms(
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
) -> list[GlossaryTermResponse]:
    terms = service.list_terms()
    return [glossary_term_to_response(term) for term in terms]


@router.post("/glossary", response_model=GlossaryTermResponse, status_code=201)
def create_glossary_term(
    request: GlossaryTermCreate,
    response: Response,
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
) -> GlossaryTermResponse:
    try:
        result = service.create_term(**request.model_dump())
    except GlossaryServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    if not result.created:
        response.status_code = 200
    return glossary_term_to_response(result.term)


@router.patch("/glossary/{term_id}", response_model=GlossaryTermResponse)
def update_glossary_term(
    term_id: int,
    request: GlossaryTermUpdate,
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
) -> GlossaryTermResponse:
    try:
        term = service.update_term(term_id, **request.model_dump(exclude_unset=True))
    except GlossaryServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return glossary_term_to_response(term)


@router.delete("/glossary/{term_id}", response_model=GlossaryTermResponse)
def delete_glossary_term(
    term_id: int,
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
) -> GlossaryTermResponse:
    try:
        term = service.deactivate_term(term_id)
    except GlossaryServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return glossary_term_to_response(term)


@router.post("/glossary/import", response_model=GlossaryImportResponse)
async def import_glossary_terms(
    request: Request,
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
) -> GlossaryImportResponse:
    try:
        text = await _read_import_text(request)
        result = service.import_csv_text(text)
    except GlossaryServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return glossary_import_to_response(result)


@router.get("/glossary/candidates", response_model=list[GlossaryCandidateResponse])
def list_glossary_candidates(
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
    status: str | None = None,
) -> list[GlossaryCandidateResponse]:
    candidates = service.list_candidates(status=status)
    return [glossary_candidate_to_response(candidate) for candidate in candidates]


@router.post(
    "/glossary/candidates/{candidate_id}/approve",
    response_model=GlossaryCandidateResponse,
)
def approve_glossary_candidate(
    candidate_id: int,
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
    request: GlossaryCandidateApproveRequest | None = None,
) -> GlossaryCandidateResponse:
    try:
        payload = request.model_dump() if request is not None else {}
        candidate = service.approve_candidate(candidate_id, **payload)
    except GlossaryServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return glossary_candidate_to_response(candidate)


@router.post(
    "/glossary/candidates/{candidate_id}/reject",
    response_model=GlossaryCandidateResponse,
)
def reject_glossary_candidate(
    candidate_id: int,
    service: Annotated[GlossaryService, Depends(get_glossary_service)],
) -> GlossaryCandidateResponse:
    try:
        candidate = service.reject_candidate(candidate_id)
    except GlossaryServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return glossary_candidate_to_response(candidate)


async def _read_import_text(request: Request) -> str:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
            raise GlossaryServiceError("JSON 본문에는 text 문자열이 필요합니다.", status_code=400)
        return payload["text"]
    return (await request.body()).decode("utf-8")
