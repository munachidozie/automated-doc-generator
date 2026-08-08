# tests/test_web.py
import pytest
from web.app import app
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    with app.test_client() as client:
        yield client

def test_index_page(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Automated Documentation Generator' in rv.data

@patch('web.app.generate_docs')
def test_generate_paste(mock_generate, client):
    mock_generate.return_value = "# Test Doc\n\nThis is a test."
    data = {
        'input_type': 'paste',
        'code': 'def hello(): pass',
        'title': 'Test',
        'format': 'md',
        'api_key': 'sk-test'
    }
    rv = client.post('/generate', data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Test' in rv.data
    assert b'This is a test' in rv.data

@patch('web.app.from_github')
@patch('web.app.generate_docs')
def test_generate_github(mock_generate, mock_from_github, client):
    # Mock the GitHub ingestion to return a dummy file
    mock_from_github.return_value = [('dummy.py', 'print("hello")')]
    mock_generate.return_value = "# GitHub Docs\n\nGenerated from GitHub repo."

    data = {
        'input_type': 'github',
        'github_url': 'https://github.com/user/repo',
        'title': 'GitHub Test',
        'format': 'all',
        'api_key': 'sk-test'
    }
    rv = client.post('/generate', data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert b'GitHub Test' in rv.data
    assert b'Generated from GitHub repo' in rv.data

@patch('web.app.generate_docs')
def test_generate_missing_api_key(mock_generate, client):
    # Even without an API key, the default should be used (no error)
    mock_generate.return_value = "# Fallback doc"
    data = {
        'input_type': 'paste',
        'code': 'def foo(): pass',
        'title': 'No Key Test',
        'format': 'md',
        'api_key': ''  # empty, use default
    }
    rv = client.post('/generate', data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert b'No Key Test' in rv.data
    # ensure generate_docs was called with api_key=None (the default)
    mock_generate.assert_called_once()
    # the call's third argument (api_key) should be None
    args, kwargs = mock_generate.call_args
    assert kwargs.get('api_key') is None or args[2] is None  # depends on order

@patch('web.app.generate_docs')
def test_generate_github_failure(mock_generate, client):
    # Simulate a failure from generate_docs (e.g., API error)
    mock_generate.return_value = None
    data = {
        'input_type': 'paste',
        'code': 'def foo(): pass',
        'title': 'Fail Test',
        'format': 'md',
        'api_key': 'invalid-key'
    }
    rv = client.post('/generate', data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Documentation generation failed' in rv.data