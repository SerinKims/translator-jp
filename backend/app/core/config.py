from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_env: str = "local"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    database_url: str = "sqlite:///./translation.db"

    ollama_model_name: str = "gemma4:26b-a4b-it-q4_K_M"
    ollama_timeout_seconds: float = 120.0
    ollama_health_timeout_seconds: float = 3.0

    max_chars_per_chunk: int = 1800
    chunk_overlap_paragraphs: int = 1
    prompt_version: str = "translate_ja_ko_v1"

    log_level: str = "INFO"
    save_raw_model_response: bool = True
    cache_enabled: bool = True

    pixiv_fetch_enabled: bool = True
    pixiv_fetch_timeout_seconds: float = 30.0
    pixiv_fetch_min_interval_seconds: float = 3.0
    pixiv_fetch_max_retries: int = 2
    pixiv_use_playwright: bool = False

    ollama_runtime_error_message: str = Field(
        default="Ollama를 사용할 수 없습니다. backend requirements와 로컬 Ollama 실행 상태를 확인해주세요."
    )
    ollama_model_not_found_message: str = Field(
        default=(
            "gemma4:26b-a4b-it-q4_K_M 모델을 찾을 수 없습니다. ollama pull 명령으로 모델을 준비해주세요."
        )
    )

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
