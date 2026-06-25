import asyncio

from fastapi import APIRouter

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import check_database_connection
from app.llm.ollama_client import is_ollama_available, show_ollama_model

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


def is_ollama_installed() -> bool:
    return is_ollama_available()


async def check_ollama_model(settings: Settings) -> tuple[str, str]:
    if not is_ollama_installed():
        logger.warning("Ollama package is not installed")
        return "error", settings.ollama_model_name

    try:
        await asyncio.wait_for(
            asyncio.to_thread(show_ollama_model, settings.ollama_model_name),
            timeout=settings.ollama_health_timeout_seconds,
        )
    except TimeoutError:
        logger.warning("Ollama model check timed out")
        return "error", settings.ollama_model_name
    except Exception as exc:
        message = getattr(exc, "error", None) or str(exc)
        status_code = getattr(exc, "status_code", None)
        if status_code == 404 or "not found" in message.lower():
            return "ok", "not_found"

        logger.warning("Ollama model check failed: %s", message)
        return "error", settings.ollama_model_name

    return "ok", settings.ollama_model_name


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    database_status = "ok" if check_database_connection() else "error"
    ollama_status, model_status = await check_ollama_model(settings)

    response = {
        "status": "ok",
        "ollama": ollama_status,
        "database": database_status,
        "model": model_status,
    }

    if ollama_status == "error":
        response["message"] = settings.ollama_runtime_error_message
    elif model_status == "not_found":
        response["message"] = settings.ollama_model_not_found_message

    return {
        **response,
    }
