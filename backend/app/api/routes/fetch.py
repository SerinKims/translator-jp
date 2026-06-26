from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fetch import (
    PixivFetchRequest,
    PixivFetchResponse,
    PixivTranslateRequest,
    PixivTranslateResponse,
)
from app.services.fetch_service import FetchService, FetchServiceError


router = APIRouter(prefix="/fetch", tags=["fetch"])


def get_fetch_service(db: Annotated[Session, Depends(get_db)]) -> FetchService:
    return FetchService(db)


@router.post("/pixiv", response_model=PixivFetchResponse)
async def fetch_pixiv(
    request: PixivFetchRequest,
    service: Annotated[FetchService, Depends(get_fetch_service)],
) -> PixivFetchResponse:
    try:
        return await service.fetch_pixiv(
            url=request.url,
            translate_after_fetch=request.translate_after_fetch,
            think=request.think,
            options=request.options,
        )
    except FetchServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/pixiv/translate", response_model=PixivTranslateResponse)
async def fetch_and_translate_pixiv(
    request: PixivTranslateRequest,
    service: Annotated[FetchService, Depends(get_fetch_service)],
) -> PixivTranslateResponse:
    try:
        return await service.fetch_and_translate_pixiv(
            url=request.url,
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
        )
    except FetchServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
