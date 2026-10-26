# Automatic Source Code Document Generator


A Python-based tool that generates comprehensive Markdown documentation from source code using the DeepSeek API. It supports multiple input sources (single file, folder, GitHub repository, or pasted code) and can output documentation in Markdown, HTML, or JSON formats. The project provides both a command-line interface (CLI) and a web interface.

## Overview

The tool reads source code files, combines them into a single prompt, and sends the prompt to the DeepSeek API to generate structured documentation. It handles file ingestion, language detection, prompt construction, API communication with retry logic, and output formatting. The generated documentation follows a standard template with sections like Project Title, Installation, Usage, API Reference, Contributing, and License.

Key features:
- **Multiple input sources**: single file, folder, GitHub repo, or pasted code.
- **Automatic language detection** from file extensions.
- **Retry logic** for API rate limits and server errors.
- **Progress bar** for CLI feedback.
- **Output formats**: Markdown, styled HTML (with syntax highlighting and TOC), and JSON (structured by headings).
- **Web interface** with file upload, GitHub cloning, and preview/download options.
- **Configuration** via environment variables or `.env` file.

## Installation

### Prerequisites
- Python 3.7 or higher
- pip

### Dependencies
The project relies on the following Python packages (inferred from imports):

| Package | Purpose |
|---------|---------|
| `click` | CLI framework |
| `requests` | HTTP client for DeepSeek API |
| `python-dotenv` | Load environment variables from `.env` |
| `GitPython` | Clone GitHub repositories |
| `markdown` | Convert Markdown to HTML |
| `Pygments` | Syntax highlighting for code blocks |
| `Flask` | Web framework |
| `Werkzeug` | Flask utilities (secure filenames, file serving) |

Install all dependencies with:

```bash
pip install click requests python-dotenv GitPython markdown Pygments Flask Werkzeug
```

Alternatively, if a `requirements.txt` exists (not included in the provided code), run:

```bash
pip install -r requirements.txt
```

### API Key Configuration
The tool requires a DeepSeek API key. You can set it in one of three ways:

1. **Environment variable**:
   ```bash
   export DEEPSEEK_API_KEY="your-api-key"
   ```

2. **`.env` file** in the project root:
   ```
   DEEPSEEK_API_KEY=your-api-key
   ```

3. **Per-request** in the web interface (the CLI does not currently expose an API key option; it uses the environment variable or `.env`).

Optional environment variables (with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | Model to use |
| `DEEPSEEK_TIMEOUT` | `180` | Request timeout in seconds |
| `DEEPSEEK_MAX_TOKENS` | `300000` | Maximum tokens for the AI response |
| `DEEPSEEK_MAX_INPUT_TOKENS` | `120000` | Input token budget warning threshold |
| `FLASK_SECRET_KEY` | `dev-secret-key-change-in-production` | Flask session secret (web only) |

## Usage

### Command-Line Interface (CLI)

The CLI is implemented with Click. Run it as a module from the project root:

```bash
python -m src.cli generate [OPTIONS]
```

**Note:** Running `python src/cli.py` directly will fail because of package-relative imports. Use `python -m src.cli` or install the package.

#### Options

| Option | Description |
|--------|-------------|
| `--file PATH` | Single file to document. |
| `--folder PATH` | Folder containing code files. |
| `--github URL` | GitHub repository URL. |
| `--paste TEXT` | Paste code directly as a string. |
| `--title TEXT` | Project title (used as main heading). |
| `--author TEXT` | Author name. |
| `--version TEXT` | Version number. |
| `--context TEXT` | Additional context about the project. |
| `--language TEXT` | Programming language (auto-detect if not given). |
| `--output, -o PATH` | Output file path (default: `./docs/README.md`). |
| `--format, -f [md\|html\|json\|both\|all]` | Output format(s). `both` = md+html, `all` = md+html+json. Default: `md`. |
| `--max-tokens INTEGER` | Max tokens for the AI response (default: from env). |
| `--model TEXT` | DeepSeek model to use (default: from env). |
| `--timeout INTEGER` | Per-request timeout in seconds (default: from env). |
| `--progress-duration INTEGER` | Target seconds for the progress bar to reach 100% (default: 30). |

#### Examples

Generate Markdown from a single file:
```bash
python -m src.cli generate --file path/to/code.py --title "My Project" --output docs/README.md
```

Generate all formats from a folder:
```bash
python -m src.cli generate --folder ./src --title "My Library" --format all --output docs/README
```

Generate from a GitHub repository:
```bash
python -m src.cli generate --github https://github.com/user/repo --title "Repo Docs" --format both
```

Generate from pasted code:
```bash
python -m src.cli generate --paste "def hello():\n    return 'world'" --title "Snippet"
```

### Web Interface

Start the Flask development server:

```bash
python web/app.py
```

The application will be available at `http://localhost:5000`.

**Workflow:**
1. Choose an input type: **Paste Code**, **Upload Files**, or **GitHub Repository**.
2. Fill in optional metadata (title, author, version, context, language).
3. Optionally provide an API key (overrides the environment variable).
4. Select the desired output format (Markdown, HTML, JSON).
5. Click **Generate**.
6. Preview the generated documentation and download it in your chosen format.

**Routes:**
- `GET /` – Home page with input form.
- `POST /generate` – Processes the form, generates documentation, stores it temporarily, and redirects to the result page.
- `GET /result` – Displays the generated documentation as HTML.
- `GET /download/<format>` – Downloads the documentation as `md`, `html`, or `json`.

Generated files are stored in a temporary directory (`/tmp/adoc_generated` on Unix-like systems) and automatically cleaned up after 24 hours.

## API Reference

### Module: `src.config`

Configuration constants and API key retrieval.

#### Constants
- `DEFAULT_MODEL: str` – Default model (`deepseek-v4-flash`), overridable via `DEEPSEEK_MODEL`.
- `DEFAULT_TIMEOUT: int` – Default request timeout (`180` seconds), overridable via `DEEPSEEK_TIMEOUT`.
- `DEFAULT_MAX_TOKENS: int` – Default max response tokens (`300000`), overridable via `DEEPSEEK_MAX_TOKENS`.
- `MAX_INPUT_TOKENS: int` – Input token warning threshold (`120000`), overridable via `DEEPSEEK_MAX_INPUT_TOKENS`.

#### `class ConfigError(RuntimeError)`
Raised when a required configuration setting (e.g., API key) is missing.

#### `get_api_key() -> str`
Returns the DeepSeek API key from the `DEEPSEEK_API_KEY` environment variable.

**Returns:** The API key string.

**Raises:** `ConfigError` if the environment variable is not set.

**Example:**
```python
from src.config import get_api_key
key = get_api_key()  # or raises ConfigError
```

---

### Module: `src.ai_client`

Handles communication with the DeepSeek API.

#### `class DeepSeekClient`
A client for the DeepSeek chat completions API.

##### `__init__(api_key: Optional[str] = None, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT, max_retries: int = 3, retry_delay: int = 2)`
Initializes the client.

- `api_key` – API key. If `None`, attempts to load from environment.
- `model` – Model name.
- `timeout` – Request timeout in seconds.
- `max_retries` – Number of retry attempts for transient failures.
- `retry_delay` – Base delay (seconds) for exponential backoff.

**Raises:** `ConfigError` if no API key is provided and none is found in the environment.

##### `generate_documentation(system_prompt: str, user_code: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> Optional[str]`
Sends a request to the DeepSeek API to generate documentation.

- `system_prompt` – The system prompt instructing the model.
- `user_code` – The combined source code to document.
- `max_tokens` – Maximum tokens for the response.

**Returns:** The generated documentation as a string, or `None` if the request fails after all retries.

**Behavior:**
- Retries on HTTP 429 (rate limit) and 5xx server errors with exponential backoff.
- Retries on timeout and connection errors.
- Returns `None` for other HTTP errors.

**Example:**
```python
client = DeepSeekClient(api_key="sk-...")
doc = client.generate_documentation("You are a documenter...", "def foo(): pass")
if doc:
    print(doc)
```

##### `generate_with_truncation_warning(system_prompt: str, user_code: str, max_tokens: int = DEFAULT_MAX_TOKENS, max_input_tokens: int = MAX_INPUT_TOKENS) -> Optional[str]`
Wraps `generate_documentation` and logs a warning if the estimated input size exceeds `max_input_tokens`.

- `max_input_tokens` – Threshold for warning (default from config).

**Returns:** Same as `generate_documentation`.

#### `get_client(api_key: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None) -> DeepSeekClient`
Returns a `DeepSeekClient`. If no overrides are provided, returns a cached singleton; otherwise creates a new client.

#### `generate_docs(system_prompt: str, user_code: str, api_key: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None, max_tokens: Optional[int] = None) -> Optional[str]`
Convenience function that obtains a client and calls `generate_with_truncation_warning`.

**Example:**
```python
from src.ai_client import generate_docs
doc = generate_docs("system prompt", "code", api_key="sk-...", max_tokens=10000)
```

---

### Module: `src.ingest`

Utilities for reading code from various sources and combining them.

#### Constants
- `CODE_EXTENSIONS: Set[str]` – Supported file extensions (e.g., `.py`, `.js`, `.java`, …).
- `IGNORED_DIRS: Set[str]` – Directories to skip during folder traversal (e.g., `.git`, `node_modules`, `venv`).
- `MAX_FILE_BYTES: int` – Maximum file size (1,000,000 bytes) before skipping.

#### `from_paste(code: str, filename: str = "paste_code") -> List[Tuple[str, str]]`
Returns a list with one tuple `(filename, code)`.

#### `from_file(filepath: str) -> List[Tuple[str, str]]`
Reads a single file and returns `[(filename, content)]`.

**Raises:** `FileNotFoundError` if the file does not exist.

#### `from_folder(folderpath: str, extensions: Optional[Set[str]] = None) -> List[Tuple[str, str]]`
Recursively walks a folder, collecting files with allowed extensions. Skips ignored directories, hidden directories, and files larger than `MAX_FILE_BYTES`.

**Returns:** List of `(relative_path, content)` tuples.

**Raises:** `FileNotFoundError` if the folder does not exist.

#### `from_github(url: str, branch: Optional[str] = None) -> List[Tuple[str, str]]`
Clones a GitHub repository into a temporary directory, processes its code files via `from_folder`, and cleans up.

**Returns:** List of `(relative_path, content)` tuples.

**Raises:** `RuntimeError` if cloning or reading fails.

#### `from_zip(zip_path: str) -> List[Tuple[str, str]]`
Extracts a ZIP archive to a temporary directory, processes code files, and cleans up.

**Returns:** List of `(relative_path, content)` tuples.

**Raises:** `RuntimeError` if extraction or reading fails.

#### `combine_files(files: List[Tuple[str, str]], separator: str = "\n\n") -> str`
Combines multiple file contents into a single string, prefixing each with `# File: <path>`.

**Example:**
```python
combined = combine_files([("a.py", "x = 1"), ("b.py", "y = 2")])
# "# File: a.py\nx = 1\n\n# File: b.py\ny = 2"
```

#### `detect_language_from_extension(filename: str) -> str`
Returns a human-readable language name based on the file extension (e.g., `'.py'` → `'Python'`). Returns `'Unknown'` if not recognized.

---

### Module: `src.prompt`

Builds the system prompt for the AI.

#### `SYSTEM_PROMPT_TEMPLATE: str`
A template string with placeholders for language, project name, author, version, and context. It instructs the model to produce structured Markdown documentation.

#### `build_prompt(language: str = "Python", project_name: str = "", author: str = "", version: str = "", context: str = "") -> str`
Fills the template with provided values. Empty strings are replaced with sensible defaults (e.g., `"Unknown Project"`, `"No additional context provided."`).

**Example:**
```python
from src.prompt import build_prompt
prompt = build_prompt(language="Python", project_name="My App", author="Jane")
```

---

### Module: `src.markdown_utils`

Converts Markdown to styled HTML.

#### `render_markdown_to_html(md_text: str, title: str = "Documentation") -> str`
Returns a complete HTML document with embedded CSS, a table of contents, and syntax-highlighted code blocks (using Pygments). The title is HTML-escaped for safety.

**Example:**
```python
from src.markdown_utils import render_markdown_to_html
html = render_markdown_to_html("# Hello\n\nWorld", "My Docs")
```

#### `markdown_to_body_html(md_text: str) -> str`
Converts Markdown to HTML body content only (no `<html>`, `<head>`, or `<body>` tags). Useful for embedding in a preview page.

---

### Module: `src.cli`

Command-line interface built with Click.

#### `class ProgressSpinner`
An animated progress bar with percentage display. It automatically falls back to ASCII characters (`#`, `-`) if the terminal cannot encode Unicode block characters.

- `__init__(message="Generating documentation", target_duration=30)`
- `start()` – Starts the animation in a daemon thread.
- `stop()` – Stops the animation and clears the line.

#### `markdown_to_json(md_text: str) -> dict`
Parses Markdown into a dictionary mapping heading titles to their content. Headings inside fenced code blocks are ignored. Duplicate headings are merged.

**Example:**
```python
from src.cli import markdown_to_json
data = markdown_to_json("# Title\n\n## Section\n\nContent")
# {'Title': '', 'Section': 'Content'}
```

#### `cli()`
Click group entry point. Displays help when called with `--help`.

#### `generate(...)`
Click command that performs the documentation generation workflow:
1. Reads input from the selected source.
2. Combines files.
3. Detects language if not provided.
4. Builds the prompt.
5. Calls `generate_docs`.
6. Saves output in the requested format(s).

**Exit codes:** `0` on success, `1` on error (e.g., no input, API failure).

**Main entry point:**
```python
if __name__ == '__main__':
    cli()
```

---

### Module: `web.app`

Flask web application.

#### Global objects
- `app: Flask` – The Flask application instance.
- `DOCS_DIR: str` – Temporary directory for generated documents.
- `ALLOWED_EXTENSIONS: Set[str]` – Same as `CODE_EXTENSIONS` from `src.ingest`.

#### `allowed_file(filename: str) -> bool`
Returns `True` if the file extension is in `ALLOWED_EXTENSIONS`.

#### `cleanup_old_docs(max_age_seconds: int = DOC_MAX_AGE_SECONDS)`
Best-effort removal of generated documents older than `max_age_seconds` (default 24 hours).

#### Routes

##### `GET /`
Renders the home page (`index.html`).

##### `POST /generate`
Handles form submission for documentation generation. Reads input type (`paste`, `file`, `github`), processes the input, calls `generate_docs`, stores the result in a temporary file, and redirects to `/result`.

**Form fields:**
- `input_type` – `paste`, `file`, or `github`.
- `code` – Pasted code (for `paste`).
- `files` – Uploaded files (for `file`).
- `github_url` – GitHub URL (for `github`).
- `branch` – Optional branch name.
- `title`, `author`, `version`, `context`, `language` – Metadata.
- `format` – Desired output format (`md`, `html`, `json`).
- `api_key` – Optional API key override.

**Returns:** Redirect to `/result` on success; renders `index.html` with an error message on failure.

##### `GET /result`
Displays the generated documentation as HTML (using `markdown_to_body_html`). Requires a `doc_id` in the session.

##### `GET /download/<format>`
Downloads the generated documentation in the specified format (`md`, `html`, or `json`). Sets appropriate MIME type and filename.

**Main entry point:**
```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

### Tests

The `tests/` directory contains unit tests for most modules:

- `test_ai_client.py` – Tests for `DeepSeekClient` (success, retries, failures).
- `test_cli.py` – Tests for `markdown_to_json`, CLI help, and `ProgressSpinner`.
- `test_config.py` – Tests for API key retrieval and client initialization.
- `test_ingest.py` – Tests for file ingestion, folder traversal, and utilities.
- `test_markdown_utils.py` – Tests for HTML rendering and escaping.
- `test_web.py` – Tests for Flask routes (paste, GitHub, missing API key, failures).

Run the test suite with:

```bash
pytest
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Write tests for new functionality (the project uses `pytest`).
4. Ensure all tests pass: `pytest`.
5. Submit a pull request with a clear description of your changes.

Please follow the existing code style (PEP 8 for Python) and include docstrings for new public functions.

## License

No license file or header was detected in the provided code. The project is currently **not specified** under any license. Please contact the maintainers for licensing information.
