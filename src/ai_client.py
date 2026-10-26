# src/ai_client.py
import time
import logging
import requests
from typing import Optional

from src.config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    MAX_INPUT_TOKENS,
    get_api_key,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.deepseek.com/v1/chat/completions"

class DeepSeekClient:
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL,
                 timeout: int = DEFAULT_TIMEOUT, max_retries: int = 3, retry_delay: int = 2):
        # The key is resolved lazily so callers can pass their own (web UI) or defer
        # configuration until a request is actually made.
        self.api_key = api_key or get_api_key()
        self.model = model
        self.base_url = BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def generate_documentation(self, system_prompt: str, user_code: str,
                               max_tokens: int = DEFAULT_MAX_TOKENS) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_code}
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens,
            "top_p": 0.9
        }
        started_at = time.time()
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to DeepSeek (attempt {attempt+1}/{self.max_retries})...")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"].get("content")
                    elapsed = time.time() - started_at
                    if not content:
                        logger.error(f"API returned an empty document after {elapsed:.1f}s.")
                        return None
                    logger.info(f"Documentation generated successfully in {elapsed:.1f}s.")
                    return content
                elif response.status_code == 429:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                elif response.status_code in (500, 502, 503, 504):
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    return None
            except requests.exceptions.Timeout:
                logger.warning(f"Request timed out (attempt {attempt+1}). Retrying...")
                time.sleep(self.retry_delay * (2 ** attempt))
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error (attempt {attempt+1}). Retrying...")
                time.sleep(self.retry_delay * (2 ** attempt))
        logger.error("All retries exhausted. Failed to get documentation.")
        return None

    def generate_with_truncation_warning(self, system_prompt: str, user_code: str,
                                        max_tokens: int = DEFAULT_MAX_TOKENS,
                                        max_input_tokens: int = MAX_INPUT_TOKENS) -> Optional[str]:
        # max_tokens bounds the *response*; the input budget is a separate concern.
        estimated_input_tokens = len(user_code) // 4
        if estimated_input_tokens > max_input_tokens:
            logger.warning(
                f"Input code estimated at ~{estimated_input_tokens} tokens, which exceeds the "
                f"configured input budget of {max_input_tokens} (DEEPSEEK_MAX_INPUT_TOKENS). "
                "The model may truncate the code; consider documenting a smaller subset."
            )
        return self.generate_documentation(system_prompt, user_code, max_tokens)

# Singleton pattern with optional api_key override
_default_client = None

def get_client(api_key: Optional[str] = None, model: Optional[str] = None,
               timeout: Optional[int] = None) -> DeepSeekClient:
    """Return a client, reusing the default singleton when no overrides are given."""
    global _default_client
    if api_key is not None or model is not None or timeout is not None:
        # Custom settings must not be cached, since they vary per call.
        return DeepSeekClient(
            api_key=api_key,
            model=model or DEFAULT_MODEL,
            timeout=timeout or DEFAULT_TIMEOUT,
        )
    if _default_client is None:
        _default_client = DeepSeekClient()
    return _default_client

def generate_docs(system_prompt: str, user_code: str, api_key: Optional[str] = None,
                  model: Optional[str] = None, timeout: Optional[int] = None,
                  max_tokens: Optional[int] = None) -> Optional[str]:
    """Convenience function; optionally override API key, model, timeout or token cap."""
    client = get_client(api_key=api_key, model=model, timeout=timeout)
    return client.generate_with_truncation_warning(
        system_prompt,
        user_code,
        max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS,
    )