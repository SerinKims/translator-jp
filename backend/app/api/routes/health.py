from fastapi import APIRouter

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import check_database_connection
from app.llm.litert_lm_client import is_litert_lm_available

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


def is_litert_lm_installed() -> bool:
    return is_litert_lm_available()


async def check_litert_lm_model(settings: Settings) -> tuple[str, str]:
    if not is_litert_lm_installed():
        logger.warning("LiteRT-LM package is not installed")
        return "error", settings.litert_lm_model_name

    if not settings.litert_lm_model_path.is_file():
        return "ok", "not_found"

    return "ok", settings.litert_lm_model_name


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    database_status = "ok" if check_database_connection() else "error"
    litert_lm_status, model_status = await check_litert_lm_model(settings)

    response = {
        "status": "ok",
        "litert_lm": litert_lm_status,
        "database": database_status,
        "model": model_status,
    }

    if litert_lm_status == "error":
        response["message"] = settings.litert_lm_runtime_error_message
    elif model_status == "not_found":
        response["message"] = settings.litert_lm_model_not_found_message

    return {
        **response,
    }
