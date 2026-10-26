# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Defaults come from the environment so deployments can tune them without code changes.
DEFAULT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEFAULT_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "180"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "300000"))
MAX_INPUT_TOKENS = int(os.getenv("DEEPSEEK_MAX_INPUT_TOKENS", "120000"))


class ConfigError(RuntimeError):
    """Raised when a required setting is missing."""


def get_api_key() -> str:
    """
    Return the DeepSeek API key.

    The key is only looked up when it is actually needed, so the CLI and web app
    can be imported/started without one (the web UI can supply a key per request).
    """
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ConfigError(
            "DEEPSEEK_API_KEY is not set. Add it to your .env file, export it in "
            "your shell, or pass an api_key explicitly."
        )
    return key