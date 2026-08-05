import pytest
import requests
from unittest.mock import patch, Mock
from src.ai_client import DeepSeekClient

@pytest.fixture
def client():
    return DeepSeekClient(api_key="fake-key")

def test_successful_generation(client):
    """Test that a successful API response returns the expected documentation."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "# My Docs\n\nThis is a test."}}]
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = client.generate_documentation("system prompt", "def foo(): pass")
        assert result == "# My Docs\n\nThis is a test."
        mock_post.assert_called_once()

def test_rate_limit_retry(client):
    """Test that rate limit (429) triggers retry and eventually succeeds."""
    mock_response_429 = Mock()
    mock_response_429.status_code = 429

    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {
        "choices": [{"message": {"content": "Retry worked!"}}]
    }

    with patch("requests.post", side_effect=[mock_response_429, mock_response_200]) as mock_post:
        result = client.generate_documentation("prompt", "code")
        assert result == "Retry worked!"
        assert mock_post.call_count == 2

def test_all_retries_fail(client):
    """Test that if all retries fail, the function returns None."""
    mock_response = Mock()
    mock_response.status_code = 500

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = client.generate_documentation("prompt", "code")
        assert result is None
        assert mock_post.call_count == client.max_retries

def test_timeout_retry(client):
    """Test that a timeout triggers a retry."""
    with patch("requests.post", side_effect=requests.exceptions.Timeout()) as mock_post:
        result = client.generate_documentation("prompt", "code")
        assert result is None  # after all retries fail
        assert mock_post.call_count == client.max_retries