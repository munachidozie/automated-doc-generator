# tests/test_config.py
import pytest

from src.config import ConfigError, get_api_key
from src.ai_client import DeepSeekClient


def test_get_api_key_returns_env_value(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    assert get_api_key() == "test-key"


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ConfigError):
        get_api_key()


def test_client_accepts_explicit_key_without_env(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = DeepSeekClient(api_key="explicit-key", model="deepseek-flash", timeout=5)
    assert client.api_key == "explicit-key"
    assert client.model == "deepseek-flash"
    assert client.timeout == 5
