from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings

try:
    import ollama
except ModuleNotFoundError:
    ollama = None  # type: ignore[assignment]


OLLAMA_MODEL_NAME = "gemma4:26b-a4b-it-q4_K_M"
OLLAMA_IMPORT_ERROR_MESSAGE = (
    "ollama 패키지를 불러올 수 없습니다. backend requirements를 설치해주세요."
)
OLLAMA_TIMEOUT_MESSAGE = "번역 시간이 너무 오래 걸렸습니다. 입력 문장을 줄이거나 다시 시도해주세요."
OLLAMA_EMPTY_RESPONSE_MESSAGE = "모델이 빈 응답을 반환했습니다. 다시 시도해주세요."
OLLAMA_INVALID_OPTIONS_MESSAGE = "Ollama options는 dict 형식이어야 합니다."
OLLAMA_INVALID_THINK_MESSAGE = "Ollama think는 str 또는 bool 형식이어야 합니다."
OllamaThink = str | bool


def ollama_model_not_found_message(model: str) -> str:
    return f"Ollama 모델을 찾을 수 없습니다: {model}"


def is_ollama_available() -> bool:
    return ollama is not None


def show_ollama_model(model: str) -> Any:
    if ollama is None:
        raise OllamaClientError(
            OLLAMA_IMPORT_ERROR_MESSAGE,
            code="runtime_unavailable",
        )
    return ollama.show(model)


@dataclass(frozen=True)
class OllamaChatResult:
    content: str
    model: str
    elapsed_ms: int
    raw_response: dict[str, Any]

    @property
    def text(self) -> str:
        return self.content


class OllamaClientError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int | None = None,
        elapsed_ms: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.elapsed_ms = elapsed_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "elapsed_ms": self.elapsed_ms,
        }


class OllamaClient:
    def __init__(
        self,
        *,
        model: str | None = None,
        timeout_seconds: float | None = None,
        runtime: Any | None = None,
        options: dict[str, Any] | None = None,
        think: OllamaThink | None = False,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.ollama_model_name
        self.timeout_seconds = timeout_seconds or settings.ollama_timeout_seconds
        self.options = self._validate_options(options)
        self.think = self._validate_think(think)
        self._runtime = runtime

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        options: dict[str, Any] | None = None,
        think: OllamaThink | None = None,
    ) -> OllamaChatResult:
        started_at = time.perf_counter()
        if self._runtime is None and ollama is None:
            raise self._error(
                OLLAMA_IMPORT_ERROR_MESSAGE,
                code="runtime_unavailable",
                started_at=started_at,
            )

        try:
            resolved_options = self._validate_options(
                options if options is not None else self.options
            )
            resolved_think = self._validate_think(think if think is not None else self.think)
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._chat_blocking,
                    messages,
                    resolved_options,
                    resolved_think,
                ),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise self._error(
                OLLAMA_TIMEOUT_MESSAGE,
                code="timeout",
                started_at=started_at,
            ) from exc
        except OllamaClientError:
            raise
        except Exception as exc:
            raise self._normalize_runtime_error(exc, started_at=started_at) from exc

        content = self._extract_content(result.raw_response)
        if not content:
            raise OllamaClientError(
                OLLAMA_EMPTY_RESPONSE_MESSAGE,
                code="empty_response",
                elapsed_ms=self._elapsed_ms(started_at),
            )

        return OllamaChatResult(
            content=content,
            model=result.model,
            elapsed_ms=self._elapsed_ms(started_at),
            raw_response=result.raw_response,
        )

    def _chat_blocking(
        self,
        messages: list[dict[str, str]],
        options: dict[str, Any] | None,
        think: OllamaThink | None,
    ) -> OllamaChatResult:
        runtime = self._load_runtime()
        response = runtime.chat(
            model=self.model,
            messages=messages,
            think=think,
            options=options,
        )
        raw_response = self._normalize_response(response)
        return OllamaChatResult(
            content="",
            model=self._response_model(raw_response),
            elapsed_ms=0,
            raw_response=raw_response,
        )

    def _load_runtime(self) -> Any:
        runtime = self._runtime or ollama
        if runtime is None:
            raise OllamaClientError(
                OLLAMA_IMPORT_ERROR_MESSAGE,
                code="runtime_unavailable",
            )
        return runtime

    def _extract_content(self, payload: dict[str, Any]) -> str:
        message = payload.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"].strip()

        content = payload.get("content")
        if isinstance(content, str):
            return content.strip()

        text = payload.get("text")
        if isinstance(text, str):
            return text.strip()

        return ""

    def _normalize_response(self, response: Any) -> dict[str, Any]:
        if isinstance(response, dict):
            return response

        model_dump = getattr(response, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, dict):
                return dumped

        if isinstance(response, Mapping):
            return dict(response)

        try:
            return dict(response)
        except (TypeError, ValueError):
            return {"response": response}

    def _response_model(self, payload: dict[str, Any]) -> str:
        model = payload.get("model")
        return model if isinstance(model, str) and model else self.model

    def _validate_options(self, options: dict[str, Any] | None) -> dict[str, Any] | None:
        if options is not None and not isinstance(options, dict):
            raise OllamaClientError(OLLAMA_INVALID_OPTIONS_MESSAGE, code="invalid_options")
        return options

    def _validate_think(self, think: OllamaThink | None) -> OllamaThink | None:
        if think is not None and not isinstance(think, str | bool):
            raise OllamaClientError(OLLAMA_INVALID_THINK_MESSAGE, code="invalid_think")
        return think

    def _normalize_runtime_error(self, exc: Exception, *, started_at: float) -> OllamaClientError:
        status_code = getattr(exc, "status_code", None)
        message = getattr(exc, "error", None) or str(exc) or exc.__class__.__name__
        code = "ollama_error"
        if status_code == 404 or "not found" in message.lower():
            code = "model_not_found"
            message = ollama_model_not_found_message(self.model)

        return OllamaClientError(
            message,
            code=code,
            status_code=status_code,
            elapsed_ms=self._elapsed_ms(started_at),
        )

    def _error(self, message: str, *, code: str, started_at: float) -> OllamaClientError:
        return OllamaClientError(
            message,
            code=code,
            elapsed_ms=self._elapsed_ms(started_at),
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((time.perf_counter() - started_at) * 1000))
