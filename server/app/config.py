from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """后端运行配置，全部可通过 server/.env 覆盖。"""

    model_config = SettingsConfigDict(
        env_file=SERVER_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.3

    # Provider-specific settings keep the original LLM_* variables working
    # while allowing the UI to switch between OpenAI and Xiaomi MiMo.
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = ""
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_model: str = "mimo-v2.5-pro"

    data_dir: str = "../frontend/data"
    web_dist_dir: str = ""

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def data_path(self) -> Path:
        path = Path(self.data_dir)
        if not path.is_absolute():
            path = (SERVER_ROOT / path).resolve()
        return path

    @property
    def web_dist_path(self) -> Path | None:
        if not self.web_dist_dir:
            return None
        path = Path(self.web_dist_dir)
        if not path.is_absolute():
            path = (SERVER_ROOT / path).resolve()
        return path if path.exists() else None

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def llm_enabled(self) -> bool:
        return self.llm_enabled_for()

    @staticmethod
    def normalize_llm_provider(provider: str | None) -> str:
        value = (provider or "").strip().lower()
        if value in {"mimo", "xiaomi", "xiaomi-mimo"}:
            return "mimo"
        return "openai"

    def get_llm_config(self, provider: str | None = None) -> dict[str, str]:
        """Return the selected provider's non-secret connection settings."""
        normalized = self.normalize_llm_provider(provider or self.llm_provider)
        if normalized == "mimo":
            return {
                "provider": normalized,
                "api_key": self.mimo_api_key.strip(),
                "base_url": self.mimo_base_url.strip(),
                "model": self.mimo_model.strip(),
            }

        # LLM_* is the legacy configuration used by the existing project.
        # Prefer the explicit OpenAI_* variables when present.
        return {
            "provider": "openai",
            "api_key": (self.openai_api_key.strip() or self.llm_api_key.strip()),
            "base_url": (self.openai_base_url.strip() or self.llm_base_url.strip()),
            "model": (self.openai_model.strip() or self.llm_model.strip()),
        }

    def llm_enabled_for(self, provider: str | None = None) -> bool:
        config = self.get_llm_config(provider)
        return bool(config["api_key"] and config["base_url"] and config["model"])

    def llm_provider_options(self) -> list[dict[str, str | bool]]:
        options = (
            ("openai", "GPT / OpenAI", self.get_llm_config("openai")),
            ("mimo", "小米 MiMo", self.get_llm_config("mimo")),
        )
        return [
            {
                "id": provider,
                "label": label,
                "configured": self.llm_enabled_for(provider),
                "model": config["model"],
                "base_url": config["base_url"],
            }
            for provider, label, config in options
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
