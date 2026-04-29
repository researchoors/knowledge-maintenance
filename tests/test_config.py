"""Tests for config module."""

import os
from unittest.mock import patch

from knowledge_maintenance.config import LLMConfig, Settings


class TestLLMConfig:
    def test_defaults(self) -> None:
        with patch.dict(os.environ, {"KM_LLM_API_KEY": "test-key"}, clear=False):
            cfg = LLMConfig()
            assert cfg.base_url == "https://api.openai.com/v1"
            assert cfg.model == "gpt-4o-mini"

    def test_env_override(self) -> None:
        env = {
            "KM_LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "KM_LLM_MODEL": "anthropic/claude-sonnet-4",
            "KM_LLM_API_KEY": "or-key",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = LLMConfig()
            assert cfg.base_url == "https://openrouter.ai/api/v1"
            assert cfg.model == "anthropic/claude-sonnet-4"


class TestSettings:
    def test_defaults(self) -> None:
        env = {"KM_KNOWLEDGE_REPO_PATH": "/tmp/test"}
        with patch.dict(os.environ, env, clear=False):
            s = Settings()
            assert s.repo_url == "https://github.com/Layr-Labs/d-inference"
            assert s.repo_branch == "main"
