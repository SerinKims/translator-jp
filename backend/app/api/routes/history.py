from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.routes.translate import get_translation_service
from app.db.session import get_db
from app.llm.translator import TranslationService, TranslationServiceError
from app.schemas.translation import (
    PageTranslateRequest,
    TranslationDetailResponse,
    TranslationHistoryItem,
    TranslationResponse,
)
from app.services.history import HistoryService, HistoryServiceError

router = APIRouter(prefix="/translations", tags=["translations"])


def get_history_service(db: Annotated[Session, Depends(get_db)]) -> HistoryService:
    return HistoryService(db)


@router.get("", response_model=list[TranslationHistoryItem])
async def list_translations(
    service: Annotated[HistoryService, Depends(get_history_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TranslationHistoryItem]:
    return service.list_translations(limit=limit, offset=offset)


@router.get("/{job_id}", response_model=TranslationDetailResponse)
async def get_translation_detail(
    job_id: int,
    service: Annotated[HistoryService, Depends(get_history_service)],
) -> TranslationDetailResponse:
    try:
        return service.get_translation_detail(job_id)
    except HistoryServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{job_id}/chunks/{chunk_index}/retry", response_model=TranslationResponse)
async def retry_chunk(
    job_id: int,
    chunk_index: int,
    service: Annotated[TranslationService, Depends(get_translation_service)],
) -> TranslationResponse:
    try:
        return await service.retry_failed_chunk(job_id, chunk_index)
    except TranslationServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{job_id}/pages/{page_index}/translate", response_model=TranslationResponse)
async def translate_page(
    job_id: int,
    page_index: int,
    request: PageTranslateRequest,
    service: Annotated[TranslationService, Depends(get_translation_service)],
) -> TranslationResponse:
    try:
        return await service.translate_job(
            job_id,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            style=request.style,
            honorific_policy=request.honorific_policy,
            preserve_names=request.preserve_names,
            use_glossary=request.use_glossary,
            use_cache=request.use_cache,
            stream=request.stream,
            think=request.think,
            options=request.options,
            translate_scope="current_page",
            page_index=page_index,
            force=request.force,
        )
    except TranslationServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
