from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.llm.translator import TranslationService, TranslationServiceError
from app.schemas.translation import TranslationRequest, TranslationResponse


router = APIRouter(tags=["translate"])


def get_translation_service(db: Annotated[Session, Depends(get_db)]) -> TranslationService:
    return TranslationService(db)


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    service: Annotated[TranslationService, Depends(get_translation_service)],
) -> TranslationResponse:
    try:
        return await service.translate_text(request)
    except TranslationServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
