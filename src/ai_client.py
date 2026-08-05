# src/ai_client.py
import time
import logging
import requests
from typing import Optional, Dict, Any
from src.config import DEEPSEEK_API_KEY

# Configure logging (so you can see what's happening)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekClient:
    def __init__(self, api_key: str = DEEPSEEK_API_KEY, model: str = "deepseek-v4-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1/chat/completions"  # verify this endpoint
        self.max_retries = 3
        self.retry_delay = 2  # seconds, will double each retry

    def generate_documentation(self, system_prompt: str, user_code: str, max_tokens: int = 300000) -> Optional[str]:
        """
        Send code + system prompt to DeepSeek and return the generated Markdown documentation.
        Returns None if all retries fail.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build the payload – adjust temperature/top_p if needed
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_code}
            ],
            "temperature": 0.3,       # lower = more deterministic
            "max_tokens": max_tokens,
            "top_p": 0.9
        }

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to DeepSeek (attempt {attempt+1}/{self.max_retries})...")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60  # seconds
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info("Documentation generated successfully.")
                    return content

                elif response.status_code == 429:
                    # Rate limit – wait and retry
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)

                elif response.status_code in (500, 502, 503, 504):
                    # Server errors – retry with backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)

                else:
                    # Other client errors (e.g., 401 auth, 400 bad request) – fail immediately
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

    def generate_with_truncation_warning(self, system_prompt: str, user_code: str, max_tokens: int = 300000) -> Optional[str]:
        """
        Same as generate_documentation, but warns if the code input might be too long.
        DeepSeek's token limit is around 32k for deepseek-chat, but we keep a safety margin.
        """
        # Rough estimation: 1 token ~ 4 characters (for English code). This is not exact but helpful.
        estimated_tokens = len(user_code) // 4
        if estimated_tokens > max_tokens:
            logger.warning(f"Input code estimated at {estimated_tokens} tokens, which exceeds max_tokens={max_tokens}. "
                           "The AI may truncate. Consider splitting your code into multiple files.")
        return self.generate_documentation(system_prompt, user_code, max_tokens)

# At the bottom of src/ai_client.py
_default_client = None

def get_client() -> DeepSeekClient:
    global _default_client
    if _default_client is None:
        _default_client = DeepSeekClient()
    return _default_client

def generate_docs(system_prompt: str, user_code: str) -> Optional[str]:
    """Convenience function to generate documentation."""
    client = get_client()
    return client.generate_with_truncation_warning(system_prompt, user_code)