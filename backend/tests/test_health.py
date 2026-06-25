import asyncio
import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.api.routes import health
from app.core.config import get_settings
from app.db import session
from app.main import app


def test_health_returns_200(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_check_ollama_model(settings):
        return "ok", settings.ollama_model_name

    monkeypatch.setattr(health, "check_database_connection", lambda: True)
    monkeypatch.setattr(health, "check_ollama_model", fake_check_ollama_model)

    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "ollama": "ok",
        "database": "ok",
        "model": "gemma4:26b-a4b-it-q4_K_M",
    }


def test_health_reports_ollama_error(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()

    async def fake_check_ollama_model(_settings):
        return "error", settings.ollama_model_name

    monkeypatch.setattr(health, "check_database_connection", lambda: True)
    monkeypatch.setattr(health, "check_ollama_model", fake_check_ollama_model)

    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["ollama"] == "error"
    assert response.json()["message"] == settings.ollama_runtime_error_message


def test_health_reports_missing_model(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()

    async def fake_check_ollama_model(_settings):
        return "ok", "not_found"

    monkeypatch.setattr(health, "check_database_connection", lambda: True)
    monkeypatch.setattr(health, "check_ollama_model", fake_check_ollama_model)

    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["model"] == "not_found"
    assert response.json()["message"] == settings.ollama_model_not_found_message


def test_check_ollama_model_reports_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class ModelNotFoundError(RuntimeError):
        status_code = 404
        error = "model not found"

    settings = get_settings()
    monkeypatch.setattr(health, "is_ollama_installed", lambda: True)

    def fake_show_ollama_model(_model: str) -> None:
        raise ModelNotFoundError()

    monkeypatch.setattr(health, "show_ollama_model", fake_show_ollama_model)

    result = asyncio.run(health.check_ollama_model(settings))

    assert result == ("ok", "not_found")


def test_database_connection_check() -> None:
    assert session.check_database_connection()
