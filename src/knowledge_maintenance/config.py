"""Configuration via pydantic-settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM connection settings for temporal validation (stale_claim checks)."""

    model_config = SettingsConfigDict(env_prefix="KM_LLM_")

    base_url: str = Field(default="https://api.openai.com/v1", description="LLM API base URL")
    model: str = Field(default="gpt-4o-mini", description="LLM model name")
    api_key: str = Field(default="", description="LLM API key (empty = skip LLM-assisted checks)")


class Settings(BaseSettings):
    """Main application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="KM_", env_file=".env", env_file_encoding="utf-8")

    repo_url: str = Field(
        default="https://github.com/Layr-Labs/d-inference",
        description="Source repo to track for knowledge generation",
    )
    repo_branch: str = Field(default="main", description="Branch to track")
    knowledge_repo_path: Path = Field(
        default=Path("."),
        description="Local path to the knowledge-maintenance repo (contains artifacts/)",
    )
    last_known_commit_file: Path = Field(
        default=Path(".last_known_commit"),
        description="File storing the last known commit SHA",
    )
    llm: LLMConfig = Field(default_factory=LLMConfig)
