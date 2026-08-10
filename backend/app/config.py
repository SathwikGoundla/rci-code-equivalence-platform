"""
Application Configuration

Pydantic-settings based configuration with environment variable support.
All settings have safe offline defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_name: str = Field(default="RCI Code Equivalence Platform")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)

    # ── Server ─────────────────────────────────────────────────────────────────
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./rci_platform.db"
    )

    # ── Security ───────────────────────────────────────────────────────────────
    redact_source_code_in_logs: bool = Field(default=True)
    max_source_file_size: int = Field(default=5 * 1024 * 1024)  # 5 MB

    # ── Execution Engine ───────────────────────────────────────────────────────
    execution_timeout: int = Field(default=30)
    execution_tmp_dir: str = Field(default="")
    max_process_memory_mb: int = Field(default=512)

    # ── Compiler Overrides (empty = auto-detect) ───────────────────────────────
    c_compiler_path: str = Field(default="")
    fortran_compiler_path: str = Field(default="")

    # ── Local AI ───────────────────────────────────────────────────────────────
    local_ai_enabled: bool = Field(default=False)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="codellama")

    # ── Frontend / CORS ────────────────────────────────────────────────────────
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # ── Logging ────────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v

    @property
    def is_offline(self) -> bool:
        """Always True — this platform never connects to the internet at runtime."""
        return True

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings. Thread-safe via lru_cache."""
    return Settings()
