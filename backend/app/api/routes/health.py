from typing import Any

import httpx
from fastapi import APIRouter

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import check_database_connection

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


def _ollama_model_exists(payload: dict[str, Any], model_name: str) -> bool:
    for model in payload.get("models", []):
        if not isinstance(model, dict):
            continue

        names = {model.get("name"), model.get("model")}
        if model_name in names:
            return True

    return False


async def check_ollama_model(settings: Settings) -> tuple[str, str]:
    try:
        timeout = httpx.Timeout(settings.ollama_timeout_seconds)
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=timeout) as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return "error", settings.ollama_model

    try:
        payload = response.json()
    except ValueError as exc:
        logger.warning("Ollama health check returned invalid JSON: %s", exc)
        return "error", settings.ollama_model

    if not _ollama_model_exists(payload, settings.ollama_model):
        return "ok", "not_found"

    return "ok", settings.ollama_model


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
        response["message"] = settings.ollama_connection_error_message
    elif model_status == "not_found":
        response["message"] = settings.ollama_model_not_found_message

    return {
        **response,
    }
