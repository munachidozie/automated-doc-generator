# Automated Documentation Generator

## Overview

The **Automated Documentation Generator** is a Python tool that produces comprehensive Markdown documentation from source code automatically. It combines code from a single file, a folder, a GitHub repository, or pasted text, sends it to the DeepSeek AI API with a tailored system prompt, and returns well-structured documentation that includes:

- Project title and overview
- Installation instructions
- Usage examples
- Per-function/per-class API reference
- Contributing guidelines
- License information (when available)

Output can be saved as **Markdown**, **HTML**, **JSON**, or any combination of these formats. The project also includes a simple web interface for generating and previewing documentation in a browser.

The tool supports many common programming languages and attempts to auto-detect the primary language from the file extension.

---

## Installation

### Prerequisites

- Python 3.8+
- A DeepSeek API key

### Steps

1. Clone or download the project.

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/macOS
   venv\Scripts\activate       # Windows
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   If a `requirements.txt` file is not present, install the dependencies directly:

   ```bash
   pip install click requests python-dotenv GitPython Markdown Flask pytest
   ```

   `Pygments` is also recommended for syntax highlighting in HTML output.

4. Create a `.env` file in the project root with your API key:

   ```
   DEEPSEEK_API_KEY=your-api-key-here
   ```

   The application will fail to start if this key is not set.

---

## Usage

### Command‑Line Interface (CLI)

The main entry point is the `cli` command group defined in `src/cli.py`. You can run it via Python:

```bash
python -m src.cli [OPTIONS] COMMAND [ARGS]...
```

The only command is `generate`.

#### Examples

Document a single file:

```bash
python -m src.cli generate --file ./main.py --output docs/README.md
```

Document an entire folder:

```bash
python -m src.cli generate --folder ./my_project --format all
```

Document a GitHub repository (cloned to a temporary directory):

```bash
python -m src.cli generate --github https://github.com/owner/repo.git --title "My Repo"
```

Generate from pasted code:

```bash
python -m src.cli generate --paste "def hello():\n    print('hi')"
```

Specify project metadata and output formats:

```bash
python -m src.cli generate --file ./app.py --title "My App" --author "Jane Doe" --version "1.0" --format both --output docs/README.md
```

#### Available options

| Option | Description | Default |
|--------|-------------|---------|
| `--file` | Path to a single file to document | – |
| `--folder` | Path to a folder containing code files | – |
| `--github` | GitHub repository URL to clone and document | – |
| `--paste` | Inline code string to document | – |
| `--title` | Project title | `""` |
| `--author` | Author name | `""` |
| `--version` | Version number | `""` |
| `--context` | Additional context for the AI | `""` |
| `--language` | Programming language (auto-detected when omitted) | `""` |
| `--output`, `-o` | Output file path | `./docs/README.md` |
| `--format`, `-f` | Output format: `md`, `html`, `json`, `both`, `all` | `md` |
| `--max-tokens` | Maximum tokens for AI response | `300000` |
| `--progress-duration` | Target seconds for the progress bar to reach 100% | `30` |

### Web Interface

The project includes a Flask web application in `web/app.py`.

Run it with:

```bash
python web/app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser. The web app allows you to:

- Paste code directly
- Upload multiple files
- Provide a GitHub repository URL
- Set title, author, version, context, language, and output format
- Preview the generated documentation in your browser
- Download the result as Markdown, HTML, or JSON

---

## API Reference

### `src/ai_client.py`

This module encapsulates interactions with the DeepSeek Chat Completions API.

#### Class `DeepSeekClient`

##### `DeepSeekClient(api_key=DEEPSEEK_API_KEY, model="deepseek-v4-flash")`

Creates a client for the DeepSeek API.

**Parameters**

- `api_key (str)` – DeepSeek API key. Defaults to the value from the environment (`DEEPSEEK_API_KEY`).
- `model (str)` – Model identifier. Defaults to `"deepseek-v4-flash"`.

**Attributes**

- `base_url (str)` – API endpoint URL.
- `max_retries (int)` – Maximum number of retries for transient errors (default `3`).
- `retry_delay (int)` – Base delay in seconds for exponential backoff (default `2`).

##### `generate_documentation(system_prompt, user_code, max_tokens=300000) -> Optional[str]`

Sends the system prompt and code to DeepSeek and returns the generated Markdown documentation.

**Parameters**

- `system_prompt (str)` – System instruction describing the documentation format and style.
- `user_code (str)` – Combined code from all input files.
- `max_tokens (int)` – Maximum tokens for the AI response (default `300000`).

**Returns**

- `Optional[str]` – The generated documentation as a string, or `None` if all retries fail.

**Exceptions**

- Makes up to `max_retries` attempts. On timeout, connection errors, rate limiting (HTTP 429), or server errors (500, 502, 503, 504), it retries with exponential backoff.
- Other non‑200 status codes (e.g. 401, 400) cause an immediate return of `None`.

**Example**

```python
from src.ai_client import DeepSeekClient

client = DeepSeekClient(api_key="your-key")
doc = client.generate_documentation(
    "You are a documentation expert.",
    "# File: main.py\ndef main(): pass"
)
print(doc)
```

##### `generate_with_truncation_warning(system_prompt, user_code, max_tokens=300000) -> Optional[str]`

Call `generate_documentation()` after warning when the estimated code length may exceed `max_tokens`.

**Parameters**

- `system_prompt (str)` – Same as `generate_documentation`.
- `user_code (str)` – Same as `generate_documentation`.
- `max_tokens (int)` – Same as `generate_documentation`.

**Returns**

- `Optional[str]` – The generated documentation, or `None` on failure.

**Example**

```python
client = DeepSeekClient()
doc = client.generate_with_truncation_warning("system prompt", "print('hello')")
```

---

#### Module-level helpers

##### `get_client() -> DeepSeekClient`

Returns a lazily‑initialized module‑wide singleton client.

##### `generate_docs(system_prompt, user_code) -> Optional[str]`

Convenience function that uses the singleton client to generate documentation.

**Parameters**

- `system_prompt (str)` – System instruction.
- `user_code (str)` – Combined code.

**Returns**

- `Optional[str]` – Generated Markdown, or `None` on failure.

---

### `src/config.py`

Loads environment variables and provides the DeepSeek API key.

- Loads the `.env` file using `python-dotenv`.
- Exposes `DEEPSEEK_API_KEY` from the environment.
- Raises `ValueError` if `DEEPSEEK_API_KEY` is not set.

**Example**

```python
from src.config import DEEPSEEK_API_KEY
print(DEEPSEEK_API_KEY is not None)  # True
```

---

### `src/ingest.py`

Contains functions for reading code from various input sources and combining them.

#### Module constants

- `CODE_EXTENSIONS (Set[str])` – Set of recognised code file extensions.

#### `from_paste(code, filename="paste_code") -> List[Tuple[str, str]]`

Returns a list containing a single `(filename, code)` tuple.

**Parameters**

- `code (str)` – The pasted code content.
- `filename (str)` – Filename to label the pasted code (default `"paste_code"`).

**Returns**

- `List[Tuple[str, str]]` – A list with one `(filename, content)` pair.

#### `from_file(filepath) -> List[Tuple[str, str]]`

Reads a single file and returns `(filename, content)`.

**Parameters**

- `filepath (str)` – Path to the file.

**Returns**

- `List[Tuple[str, str]]` – A list with one entry.

**Exceptions**

- `FileNotFoundError` – If the file does not exist.

#### `from_folder(folderpath, extensions=None) -> List[Tuple[str, str]]`

Recursively collects all files with recognised code extensions from a folder.

**Parameters**

- `folderpath (str)` – Root folder path.
- `extensions (Optional[Set[str]])` – Set of extensions to include. Defaults to `CODE_EXTENSIONS`.

**Returns**

- `List[Tuple[str, str]]` – List of `(relative_path, content)` tuples. Files that cannot be read are skipped with a warning.

**Exceptions**

- `FileNotFoundError` – If the folder does not exist.

#### `from_github(url, branch=None) -> List[Tuple[str, str]]`

Clones a GitHub repository to a temporary directory and processes its code files.

**Parameters**

- `url (str)` – Git clone URL.
- `branch (Optional[str])` – Branch to clone. If omitted, the repository’s default branch is used.

**Returns**

- `List[Tuple[str, str]]` – List of `(relative_path, content)` tuples from the repository.

**Exceptions**

- `RuntimeError` – Raised if cloning or reading fails.

#### `from_zip(zip_path) -> List[Tuple[str, str]]`

Extracts a ZIP archive to a temporary directory and processes its code files.

**Parameters**

- `zip_path (str)` – Path to the ZIP file.

**Returns**

- `List[Tuple[str, str]]` – List of `(relative_path, content)` tuples.

**Exceptions**

- `RuntimeError` – Raised if extraction or reading fails.

#### `combine_files(files, separator="\n\n") -> str`

Combines multiple file contents into a single string, prefixing each file with a `# File: <name>` header.

**Parameters**

- `files (List[Tuple[str, str]])` – List of `(filename, content)` tuples.
- `separator (str)` – String inserted between files (default `"\n\n"`).

**Returns**

- `str` – The combined code.

**Example**

```python
files = [("a.py", "x = 1"), ("b.py", "y = 2")]
combined = combine_files(files)
print(combined)
# # File: a.py
# x = 1
#
# # File: b.py
# y = 2
```

#### `detect_language_from_extension(filename) -> str`

Returns a human-readable language name based on file extension.

**Parameters**

- `filename (str)` – File name or path.

**Returns**

- `str` – Language name (e.g. `"Python"`, `"JavaScript"`) or `"Unknown"` if the extension is not recognised.

---

### `src/prompt.py`

Contains the system prompt template and the function used to build it.

#### Module constant

- `SYSTEM_PROMPT_TEMPLATE (str)` – The full documentation instruction template with placeholders for language, project name, author, version, and context.

#### `build_prompt(language="Python", project_name="", author="", version="", context="") -> str`

Fills the system prompt template with the given values.

**Parameters**

- `language (str)` – Target programming language (default `"Python"`).
- `project_name (str)` – Project title. Falls back to `"Unknown Project"` when empty.
- `author (str)` – Author name. Falls back to `"Not specified"` when empty.
- `version (str)` – Version number. Falls back to `"Not specified"` when empty.
- `context (str)` – Additional context. Falls back to `"No additional context provided."` when empty.

**Returns**

- `str` – The complete system prompt ready to be sent to the API.

**Example**

```python
from src.prompt import build_prompt

prompt = build_prompt(
    language="Python",
    project_name="My CLI Tool",
    author="Jane Doe",
    version="2.1.0",
    context="This tool automates documentation generation."
)
```

---

### `src/markdown_utils.py`

Helpers for converting Markdown to styled HTML.

#### `render_markdown_to_html(md_text, title="Documentation") -> str`

Converts Markdown into a complete HTML document with embedded CSS and a table of contents.

**Parameters**

- `md_text (str)` – Markdown content.
- `title (str)` – Page title and `<h1>` heading (default `"Documentation"`).

**Returns**

- `str` – A full HTML page string.

**Example**

```python
from src.markdown_utils import render_markdown_to_html

html = render_markdown_to_html("# Hello\n\nSome docs.", title="My Docs")
```

#### `markdown_to_body_html(md_text) -> str`

Converts Markdown to an HTML fragment (without `<html>`, `<head>`, or `<body>` tags). Useful for embedding in a preview page.

**Parameters**

- `md_text (str)` – Markdown content.

**Returns**

- `str` – HTML body markup.

---

### `src/cli.py`

Implements the command-line interface.

#### Class `ProgressSpinner`

An animated progress bar that displays a percentage while documentation is generated.

##### `ProgressSpinner(message="Generating documentation", target_duration=30)`

- `message (str)` – Text shown beside the progress bar.
- `target_duration (int)` – Number of seconds for the bar to reach 100%.

##### `start()`

Starts the animation in a background thread.

##### `stop()`

Stops the animation and clears the progress line.

##### `_animate()`

Internal worker that updates the bar and percentage.

#### `markdown_to_json(md_text) -> dict`

Parses Markdown into a dict whose keys are section titles (from `##`–`######` headers) and whose values are the section content.

**Parameters**

- `md_text (str)` – Raw Markdown text.

**Returns**

- `dict` – Section-by-section representation of the document.

**Example**

```python
from src.cli import markdown_to_json

data = markdown_to_json("## Installation\n\npip install foo")
print(data)  # {"Installation": "pip install foo"}
```

#### `cli()`

Click group that acts as the root command. Prints help when invoked without arguments.

#### `generate(input_file, input_folder, github_url, paste_code, title, author, version, context, language, output, format, max_tokens, progress_duration)`

The main CLI command. It collects files from the selected input, builds the prompt, calls the AI, and writes the output in the requested format(s).

**Parameters** – all passed via Click options described in the Usage section.

**Behaviors**

- Automatically detects language when `language` is not provided.
- Supports formats: `md`, `html`, `json`, `both`, `all`.
- Displays a progress bar while generating.
- Exits with status 1 if no input files are found or generation fails.

---

### `web/app.py`

Flask web application for generating and previewing documentation.

#### `allowed_file(filename) -> bool`

Returns `True` if the file extension is in the supported set.

#### Route `/` (`GET`)

Renders the upload/paste form (`index.html`).

#### Route `/generate` (`POST`)

Handles documentation generation. Accepts form fields:

- `title`, `author`, `version`, `context`, `language`, `format`
- `input_type`: `paste`, `file`, or `github`
- For paste: `code`
- For file upload: `files` (multiple)
- For github: `github_url`, `branch`

On success, stores the generated document in a temporary directory, saves the doc ID in the Flask session, and redirects to `/result`.

#### Route `/result` (`GET`)

Reads the saved documentation from the session, converts it to an HTML preview, and renders `result.html`.

#### Route `/download/<format>` (`GET`)

Downloads the generated documentation in `md`, `html`, or `json` format.

- Uses the temporary file created during generation.
- Sends the file as an attachment with a sanitised filename.

#### Starting the server

```bash
python web/app.py
```

The default host is `127.0.0.1` and port `5000`.

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Write clear, tested code.
4. Add or update tests under `tests/`.
5. Run the test suite before submitting a pull request.
6. Submit a pull request with a clear description of your changes.

Please keep code style consistent and include documentation updates where appropriate.

---

## License

Not specified. If you intend to distribute this project, please add a license file (e.g., `LICENSE`) and update this section accordingly.