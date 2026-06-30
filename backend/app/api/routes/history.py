from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes.translate import get_translation_service
from app.llm.translator import TranslationService, TranslationServiceError
from app.schemas.translation import PageTranslateRequest, TranslationResponse

router = APIRouter(prefix="/translations", tags=["translations"])


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
        )
    except TranslationServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
