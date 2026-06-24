import asyncio
from pathlib import Path
from typing import Any

from app.llm import litert_lm_client
from app.llm.litert_lm_client import (
    LITERT_LM_EMPTY_RESPONSE_MESSAGE,
    LITERT_LM_IMPORT_ERROR_MESSAGE,
    LITERT_LM_MODEL_NAME,
    LITERT_LM_TIMEOUT_MESSAGE,
    LiteRTLMClient,
    LiteRTLMClientError,
    litert_lm_model_not_found_message,
)


def test_litert_lm_client_returns_success_response() -> None:
    async def run_test() -> None:
        client = LiteRTLMClient(
            model_path="C:/models/gemma4-e4b/model.litertlm",
            timeout_seconds=1,
            runtime=FakeRuntime,
            path_exists=lambda path: True,
        )

        result = await client.chat(
            [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "原文"},
            ]
        )

        assert Path(FakeRuntime.Engine.last_model_path) == Path(
            "C:/models/gemma4-e4b/model.litertlm"
        )
        assert FakeConversation.last_messages == [("system", "system prompt")]
        assert FakeConversation.last_prompt == "原文"
        assert result.content == "번역 결과"
        assert result.text == "번역 결과"
        assert result.model == LITERT_LM_MODEL_NAME
        assert result.elapsed_ms >= 0
        assert result.raw_response["content"][0]["text"] == "번역 결과"

    asyncio.run(run_test())


def test_litert_lm_client_normalizes_missing_model_file() -> None:
    async def run_test() -> None:
        client = LiteRTLMClient(
            model_path="C:/missing/model.litertlm",
            timeout_seconds=1,
            runtime=FakeRuntime,
            path_exists=lambda path: False,
        )

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except LiteRTLMClientError as exc:
            assert exc.code == "model_not_found"
            assert exc.message == litert_lm_model_not_found_message(
                Path("C:/missing/model.litertlm")
            )
            assert exc.elapsed_ms is not None
            return

        raise AssertionError("LiteRTLMClientError was not raised")

    asyncio.run(run_test())


def test_litert_lm_client_normalizes_missing_runtime(monkeypatch) -> None:  # noqa: ANN001
    async def run_test() -> None:
        monkeypatch.setattr(litert_lm_client, "litert_lm", None)
        client = LiteRTLMClient(
            model_path="C:/models/gemma4-e4b/model.litertlm",
            timeout_seconds=1,
            path_exists=lambda path: True,
        )

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except LiteRTLMClientError as exc:
            assert exc.code == "runtime_unavailable"
            assert exc.message == LITERT_LM_IMPORT_ERROR_MESSAGE
            return

        raise AssertionError("LiteRTLMClientError was not raised")

    asyncio.run(run_test())


def test_litert_lm_client_normalizes_timeout() -> None:
    async def run_test() -> None:
        client = LiteRTLMClient(
            model_path="C:/models/gemma4-e4b/model.litertlm",
            timeout_seconds=0.001,
            runtime=SlowRuntime,
            path_exists=lambda path: True,
        )

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except LiteRTLMClientError as exc:
            assert exc.code == "timeout"
            assert exc.message == LITERT_LM_TIMEOUT_MESSAGE
            return

        raise AssertionError("LiteRTLMClientError was not raised")

    asyncio.run(run_test())


def test_litert_lm_client_normalizes_empty_response() -> None:
    async def run_test() -> None:
        client = LiteRTLMClient(
            model_path="C:/models/gemma4-e4b/model.litertlm",
            timeout_seconds=1,
            runtime=EmptyRuntime,
            path_exists=lambda path: True,
        )

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except LiteRTLMClientError as exc:
            assert exc.code == "empty_response"
            assert exc.message == LITERT_LM_EMPTY_RESPONSE_MESSAGE
            return

        raise AssertionError("LiteRTLMClientError was not raised")

    asyncio.run(run_test())


def test_litert_lm_client_error_response_is_normalized() -> None:
    async def run_test() -> None:
        client = LiteRTLMClient(
            model_path="C:/models/gemma4-e4b/model.litertlm",
            timeout_seconds=1,
            runtime=ErrorRuntime,
            path_exists=lambda path: True,
        )

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except LiteRTLMClientError as exc:
            assert exc.to_dict() == {
                "code": "litert_lm_error",
                "message": "engine failed",
                "status_code": None,
                "elapsed_ms": exc.elapsed_ms,
            }
            return

        raise AssertionError("LiteRTLMClientError was not raised")

    asyncio.run(run_test())


class FakeMessage:
    @staticmethod
    def system(content: str) -> tuple[str, str]:
        return ("system", content)


class FakeConversation:
    last_messages: list[Any] = []
    last_prompt: str = ""

    def __init__(self, messages: list[Any], response: dict[str, Any] | None = None) -> None:
        self.messages = messages
        self.response = response or {"content": [{"text": "번역 결과"}]}

    def __enter__(self) -> "FakeConversation":
        FakeConversation.last_messages = self.messages
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # noqa: ANN001
        return None

    def send_message(self, prompt: str) -> dict[str, Any]:
        FakeConversation.last_prompt = prompt
        return self.response


class FakeEngine:
    last_model_path = ""

    def __init__(self, model_path: str, response: dict[str, Any] | None = None) -> None:
        FakeEngine.last_model_path = model_path
        self.response = response

    def __enter__(self) -> "FakeEngine":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # noqa: ANN001
        return None

    def create_conversation(self, *, messages: list[Any]) -> FakeConversation:
        return FakeConversation(messages, self.response)


class FakeRuntime:
    Message = FakeMessage
    Engine = FakeEngine


class EmptyRuntime:
    Message = FakeMessage

    class Engine(FakeEngine):
        def __init__(self, model_path: str) -> None:
            super().__init__(model_path, {"content": [{"text": "   "}]})


class ErrorRuntime:
    Message = FakeMessage

    class Engine(FakeEngine):
        def __enter__(self) -> "ErrorRuntime.Engine":
            raise RuntimeError("engine failed")


class SlowRuntime:
    Message = FakeMessage

    class Engine(FakeEngine):
        def create_conversation(self, *, messages: list[Any]) -> FakeConversation:
            import time

            time.sleep(0.1)
            return super().create_conversation(messages=messages)
