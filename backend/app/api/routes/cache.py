from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.cache import TranslationCacheService

router = APIRouter(prefix="/cache", tags=["cache"])


def get_translation_cache_service(
    db: Annotated[Session, Depends(get_db)],
) -> TranslationCacheService:
    return TranslationCacheService(db)


@router.delete("/translations", status_code=status.HTTP_204_NO_CONTENT)
async def clear_translation_cache(
    service: Annotated[
        TranslationCacheService,
        Depends(get_translation_cache_service),
    ],
) -> None:
    service.clear_all()
