import asyncio
import time
from typing import Any

from app.llm import ollama_client
from app.llm.ollama_client import (
    OLLAMA_EMPTY_RESPONSE_MESSAGE,
    OLLAMA_IMPORT_ERROR_MESSAGE,
    OLLAMA_INVALID_OPTIONS_MESSAGE,
    OLLAMA_INVALID_THINK_MESSAGE,
    OLLAMA_MODEL_NAME,
    OLLAMA_TIMEOUT_MESSAGE,
    OllamaClient,
    OllamaClientError,
    ollama_model_not_found_message,
)


def test_ollama_client_returns_success_response() -> None:
    async def run_test() -> None:
        client = OllamaClient(
            timeout_seconds=1,
            runtime=FakeRuntime,
            options={"temperature": 0.2, "max_tokens": 2048},
            think=False,
        )

        result = await client.chat(
            [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "原文"},
            ]
        )

        assert FakeRuntime.last_model == OLLAMA_MODEL_NAME
        assert FakeRuntime.last_messages == [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "原文"},
        ]
        assert FakeRuntime.last_think is False
        assert FakeRuntime.last_options == {"temperature": 0.2, "max_tokens": 2048}
        assert result.content == "번역 결과"
        assert result.text == "번역 결과"
        assert result.model == OLLAMA_MODEL_NAME
        assert result.elapsed_ms >= 0
        assert result.raw_response["message"]["content"] == "번역 결과"

    asyncio.run(run_test())


def test_ollama_client_extracts_content_from_model_dump_response() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=1, runtime=ModelDumpRuntime)

        result = await client.chat([{"role": "user", "content": "原文"}])

        assert result.content == "model dump translation"
        assert result.model == "model-dump-model"
        assert result.raw_response["message"]["content"] == "model dump translation"

    asyncio.run(run_test())


def test_ollama_client_accepts_user_supplied_think_and_options_per_call() -> None:
    async def run_test() -> None:
        client = OllamaClient(
            timeout_seconds=1,
            runtime=FakeRuntime,
            options={"temperature": 0.8},
            think=False,
        )

        await client.chat(
            [{"role": "user", "content": "原文"}],
            options={"num_ctx": 4096},
            think="low",
        )

        assert FakeRuntime.last_think == "low"
        assert FakeRuntime.last_options == {"num_ctx": 4096}

    asyncio.run(run_test())


def test_ollama_client_defaults_think_to_false_and_options_to_none() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=1, runtime=FakeRuntime)

        await client.chat([{"role": "user", "content": "原文"}])

        assert FakeRuntime.last_think is False
        assert FakeRuntime.last_options is None

    asyncio.run(run_test())


def test_ollama_client_rejects_non_dict_options() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=1, runtime=FakeRuntime)

        try:
            await client.chat(
                [{"role": "user", "content": "原文"}],
                options=["temperature", 0.2],  # type: ignore[arg-type]
            )
        except OllamaClientError as exc:
            assert exc.code == "invalid_options"
            assert exc.message == OLLAMA_INVALID_OPTIONS_MESSAGE
            return

        raise AssertionError("OllamaClientError was not raised")

    asyncio.run(run_test())


def test_ollama_client_rejects_non_str_bool_think() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=1, runtime=FakeRuntime)

        try:
            await client.chat(
                [{"role": "user", "content": "原文"}],
                think=1,  # type: ignore[arg-type]
            )
        except OllamaClientError as exc:
            assert exc.code == "invalid_think"
            assert exc.message == OLLAMA_INVALID_THINK_MESSAGE
            return

        raise AssertionError("OllamaClientError was not raised")

    asyncio.run(run_test())


def test_ollama_client_normalizes_missing_runtime(monkeypatch) -> None:  # noqa: ANN001
    async def run_test() -> None:
        monkeypatch.setattr(ollama_client, "ollama", None)
        client = OllamaClient(timeout_seconds=1)

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except OllamaClientError as exc:
            assert exc.code == "runtime_unavailable"
            assert exc.message == OLLAMA_IMPORT_ERROR_MESSAGE
            return

        raise AssertionError("OllamaClientError was not raised")

    asyncio.run(run_test())


def test_ollama_client_normalizes_timeout() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=0.001, runtime=SlowRuntime)

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except OllamaClientError as exc:
            assert exc.code == "timeout"
            assert exc.message == OLLAMA_TIMEOUT_MESSAGE
            return

        raise AssertionError("OllamaClientError was not raised")

    asyncio.run(run_test())


def test_ollama_client_normalizes_empty_response() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=1, runtime=EmptyRuntime)

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except OllamaClientError as exc:
            assert exc.code == "empty_response"
            assert exc.message == OLLAMA_EMPTY_RESPONSE_MESSAGE
            return

        raise AssertionError("OllamaClientError was not raised")

    asyncio.run(run_test())


def test_ollama_client_error_response_is_normalized() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=1, runtime=ErrorRuntime)

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except OllamaClientError as exc:
            assert exc.to_dict() == {
                "code": "ollama_error",
                "message": "engine failed",
                "status_code": None,
                "elapsed_ms": exc.elapsed_ms,
            }
            return

        raise AssertionError("OllamaClientError was not raised")

    asyncio.run(run_test())


def test_ollama_client_model_not_found_is_normalized() -> None:
    async def run_test() -> None:
        client = OllamaClient(timeout_seconds=1, runtime=ModelNotFoundRuntime)

        try:
            await client.chat([{"role": "user", "content": "原文"}])
        except OllamaClientError as exc:
            assert exc.code == "model_not_found"
            assert exc.status_code == 404
            assert exc.message == ollama_model_not_found_message(OLLAMA_MODEL_NAME)
            return

        raise AssertionError("OllamaClientError was not raised")

    asyncio.run(run_test())


class FakeRuntime:
    last_model = ""
    last_messages: list[dict[str, str]] = []
    last_think: str | bool | None = None
    last_options: dict[str, Any] | None = None

    @staticmethod
    def chat(
        *,
        model: str,
        messages: list[dict[str, str]],
        think: str | bool | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        FakeRuntime.last_model = model
        FakeRuntime.last_messages = messages
        FakeRuntime.last_think = think
        FakeRuntime.last_options = options
        return {
            "model": model,
            "message": {"role": "assistant", "content": "번역 결과"},
        }


class ModelDumpResponse:
    def model_dump(self) -> dict[str, Any]:
        return {
            "model": "model-dump-model",
            "message": {"role": "assistant", "content": "model dump translation"},
        }


class ModelDumpRuntime:
    @staticmethod
    def chat(**_kwargs) -> ModelDumpResponse:  # noqa: ANN003
        return ModelDumpResponse()


class EmptyRuntime:
    @staticmethod
    def chat(**_kwargs) -> dict[str, Any]:  # noqa: ANN003
        return {"message": {"role": "assistant", "content": "   "}}


class ErrorRuntime:
    @staticmethod
    def chat(**_kwargs) -> dict[str, Any]:  # noqa: ANN003
        raise RuntimeError("engine failed")


class ModelNotFoundError(RuntimeError):
    status_code = 404
    error = "model not found"


class ModelNotFoundRuntime:
    @staticmethod
    def chat(**_kwargs) -> dict[str, Any]:  # noqa: ANN003
        raise ModelNotFoundError()


class SlowRuntime:
    @staticmethod
    def chat(**_kwargs) -> dict[str, Any]:  # noqa: ANN003
        time.sleep(0.1)
        return {"message": {"role": "assistant", "content": "번역 결과"}}
