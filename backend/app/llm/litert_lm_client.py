from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings

try:
    import litert_lm
except ModuleNotFoundError:
    litert_lm = None  # type: ignore[assignment]


LITERT_LM_MODEL_NAME = "gemma4-e4b"
LITERT_LM_MODEL_PATH = r"C:\Users\USER\.litert-lm\models\gemma4-e4b\model.litertlm"

LITERT_LM_IMPORT_ERROR_MESSAGE = (
    "litert-lm-api 패키지를 불러올 수 없습니다. backend requirements를 설치해주세요."
)
LITERT_LM_TIMEOUT_MESSAGE = (
    "번역 시간이 너무 오래 걸렸습니다. 입력 문장을 줄이거나 다시 시도해주세요."
)
LITERT_LM_EMPTY_RESPONSE_MESSAGE = "모델이 빈 응답을 반환했습니다. 다시 시도해주세요."


def litert_lm_model_not_found_message(model_path: str | Path) -> str:
    return f"LiteRT-LM 모델 파일을 찾을 수 없습니다: {model_path}"


def is_litert_lm_available() -> bool:
    return litert_lm is not None


@dataclass(frozen=True)
class LiteRTLMChatResult:
    content: str
    model: str
    elapsed_ms: int
    raw_response: dict[str, Any]

    @property
    def text(self) -> str:
        return self.content


class LiteRTLMClientError(RuntimeError):
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


class LiteRTLMClient:
    def __init__(
        self,
        *,
        model: str | None = None,
        model_path: str | Path | None = None,
        timeout_seconds: float | None = None,
        runtime: Any | None = None,
        path_exists: Callable[[Path], bool] | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.litert_lm_model_name
        self.model_path = Path(model_path or settings.litert_lm_model_path)
        self.timeout_seconds = timeout_seconds or settings.litert_lm_timeout_seconds
        self._runtime = runtime
        self._path_exists = path_exists or Path.is_file

    async def chat(
        self,
        messages: list[dict[str, str]],
    ) -> LiteRTLMChatResult:
        started_at = time.perf_counter()
        if not self._path_exists(self.model_path):
            raise self._error(
                litert_lm_model_not_found_message(str(self.model_path)),
                code="model_not_found",
                started_at=started_at,
            )
        if self._runtime is None and litert_lm is None:
            raise self._error(
                LITERT_LM_IMPORT_ERROR_MESSAGE,
                code="runtime_unavailable",
                started_at=started_at,
            )

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._chat_blocking, messages),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise self._error(
                LITERT_LM_TIMEOUT_MESSAGE,
                code="timeout",
                started_at=started_at,
            ) from exc
        except LiteRTLMClientError:
            raise
        except Exception as exc:
            raise self._error(
                str(exc) or exc.__class__.__name__,
                code="litert_lm_error",
                started_at=started_at,
            ) from exc

        content = self._extract_content(result.raw_response)
        if not content:
            raise LiteRTLMClientError(
                LITERT_LM_EMPTY_RESPONSE_MESSAGE,
                code="empty_response",
                elapsed_ms=self._elapsed_ms(started_at),
            )

        return LiteRTLMChatResult(
            content=content,
            model=result.model,
            elapsed_ms=self._elapsed_ms(started_at),
            raw_response=result.raw_response,
        )

    def _chat_blocking(
        self,
        messages: list[dict[str, str]],
    ) -> LiteRTLMChatResult:
        runtime = self._load_runtime()
        system_messages = self._system_messages(runtime, messages)
        user_prompt = self._user_prompt(messages)

        with runtime.Engine(str(self.model_path)) as engine:
            with engine.create_conversation(messages=system_messages) as conversation:
                response = conversation.send_message(user_prompt)

        raw_response = response if isinstance(response, dict) else {"response": response}
        return LiteRTLMChatResult(
            content="",
            model=self.model,
            elapsed_ms=0,
            raw_response=raw_response,
        )

    def _load_runtime(self) -> Any:
        runtime = self._runtime or litert_lm
        if runtime is None:
            raise LiteRTLMClientError(
                LITERT_LM_IMPORT_ERROR_MESSAGE,
                code="runtime_unavailable",
            )
        set_min_log_severity = getattr(runtime, "set_min_log_severity", None)
        log_severity = getattr(runtime, "LogSeverity", None)
        if callable(set_min_log_severity) and log_severity is not None:
            set_min_log_severity(log_severity.ERROR)
        return runtime

    def _system_messages(self, runtime: Any, messages: list[dict[str, str]]) -> list[Any]:
        system_contents = [
            message["content"]
            for message in messages
            if message.get("role") in {"system", "developer"} and message.get("content")
        ]
        return [runtime.Message.system(content) for content in system_contents]

    def _user_prompt(self, messages: list[dict[str, str]]) -> str:
        conversational_messages = [
            message
            for message in messages
            if message.get("role") not in {"system", "developer"} and message.get("content")
        ]
        if not conversational_messages:
            return ""
        if len(conversational_messages) == 1:
            return conversational_messages[0]["content"]

        return "\n\n".join(
            f"{message.get('role', 'user')}: {message['content']}"
            for message in conversational_messages
        )

    def _extract_content(self, payload: dict[str, Any]) -> str:
        content = payload.get("content")
        if isinstance(content, list):
            text_parts = [
                item["text"]
                for item in content
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ]
            return "\n".join(text_parts).strip()

        if isinstance(content, str):
            return content.strip()

        message = payload.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"].strip()

        text = payload.get("text")
        if isinstance(text, str):
            return text.strip()

        return ""

    def _error(self, message: str, *, code: str, started_at: float) -> LiteRTLMClientError:
        return LiteRTLMClientError(
            message,
            code=code,
            elapsed_ms=self._elapsed_ms(started_at),
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((time.perf_counter() - started_at) * 1000))
