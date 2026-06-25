from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class OllamaRequestOptions(BaseModel):
    think: str | bool = False
    options: dict[str, Any] | None = None

    @field_validator("think", mode="before")
    @classmethod
    def validate_think(cls, value: Any) -> Any:
        if isinstance(value, bool) or isinstance(value, str):
            return value
        raise ValueError("think must be a string or boolean")
