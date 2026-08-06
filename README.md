# Automated Documentation Generator

## Overview

Automated Documentation Generator is a command-line tool that automatically creates comprehensive project documentation from source code. It uses the DeepSeek AI API to analyze code files and produce well-structured Markdown documentation, with optional HTML and JSON output.

The tool accepts input from a single file, a folder, a GitHub repository, or directly pasted code. It automatically detects the programming language, combines multiple files into a single context, and sends the code to the DeepSeek API with a carefully crafted prompt. The generated documentation follows a consistent template that includes an overview, installation, usage, API reference, contributing, and license sections.

## Installation

### Requirements

- Python 3.8 or later
- A DeepSeek API key

### Dependencies

The tool uses the following Python packages:

- `requests` – HTTP client for the DeepSeek AI API
- `click` – command-line interface framework
- `python-dotenv` – loading the API key from a `.env` file
- `GitPython` – cloning GitHub repositories
- `markdown` (optional) – generating styled HTML output
- `pytest` (development) – running tests

### Setup

1. Clone or download the project.

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install requests click python-dotenv GitPython markdown
# For development only:
pip install pytest
```

4. Create a `.env` file in the project root with your DeepSeek API key:

```
DEEPSEEK_API_KEY=your-api-key-here
```

The application will fail to start if the key is missing.

## Usage

The CLI is built around the `generate` command. The main entry point is `src/cli.py`, and the command group is defined there.

### General Syntax

```bash
python -m src.cli generate [OPTIONS]
```

or

```bash
python src/cli.py generate [OPTIONS]
```

### Input Sources

You must specify exactly one input source:

| Option | Description |
|--------|-------------|
| `--file PATH` | Path to a single code file |
| `--folder PATH` | Path to a folder containing code files |
| `--github URL` | GitHub repository URL (cloned internally) |
| `--paste CODE` | Raw code passed directly as a string |

### Output Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o PATH` | `./docs/README.md` | Output file path |
| `--format`, `-f` | `md` | Output format: `md`, `html`, `json`, `both` (md + html), or `all` (md + html + json) |

### Metadata Options

| Option | Default | Description |
|--------|---------|-------------|
| `--title TEXT` | empty | Project title for the documentation |
| `--author TEXT` | empty | Author name |
| `--version TEXT` | empty | Version number |
| `--context TEXT` | empty | Additional context about the project |
| `--language TEXT` | auto-detect | Programming language of the code |

### AI Generation Options

| Option | Default | Description |
|--------|---------|-------------|
| `--max-tokens` | 300000 | Maximum tokens for the AI response (V4 max is 384000) |
| `--progress-duration` | 30 | Target seconds for the percentage progress bar to reach 100% |

### Examples

Document a single file:

```bash
python -m src.cli generate --file src/ai_client.py --title "AI Client" --author "Munachimso Ukaoha"
```

Document an entire folder and output all formats:

```bash
python -m src.cli generate --folder ./src --format all --output ./docs/project
```

Document a GitHub repository:

```bash
python -m src.cli generate --github https://github.com/user/repo --title "My Repo"
```

Document pasted code:

```bash
python -m src.cli generate --paste "def hello(): print('Hello')" --language python
```

### Output Formats

- **Markdown (`md`)** – the standard output with full AI-generated documentation.
- **HTML (`html`)** – styled HTML version with table of contents and syntax highlighting. Requires the `markdown` package.
- **JSON (`json`)** – a structured representation of the Markdown sections, split by headings.

When `--output` is given with an extension (e.g., `.md`), the other formats reuse the same base name with the appropriate extension.

## API Reference

This section documents the project’s internal modules and key functions.

### Module `src.config`

#### `DEEPSEEK_API_KEY`

- **Type:** `str`
- **Description:** DeepSeek API key loaded from the environment using `python-dotenv`. Read from the `.env` file.
- **Exception:** Raises `ValueError` if the key is not set.

---

### Module `src.ai_client`

This module handles all DeepSeek API communication.

#### `class DeepSeekClient`

A client for the DeepSeek chat completions endpoint.

##### `__init__(api_key: str, model: str = "deepseek-v4-flash")`

- **Parameters:**
  - `api_key` (`str`): DeepSeek API key.
  - `model` (`str`): Model identifier. Default `"deepseek-v4-flash"`.
- **Description:** Initializes the client, base URL, and retry settings (`max_retries=3`, `retry_delay=2`).

##### `generate_documentation(system_prompt: str, user_code: str, max_tokens: int = 300000) -> Optional[str]`

- **Parameters:**
  - `system_prompt` (`str`): Instructions sent to the model as the system message.
  - `user_code` (`str`): Full source code sent as the user message.
  - `max_tokens` (`int`): Maximum tokens for the response. Default `300000`.
- **Returns:** `Optional[str]` – Generated Markdown documentation on success, or `None` if all retries fail.
- **Behavior:**
  - Sends a POST request to `https://api.deepseek.com/v1/chat/completions`.
  - Uses `temperature=0.3` and `top_p=0.9` for deterministic output.
  - Retries with exponential backoff on:
    - HTTP 429 (rate limit)
    - HTTP 500, 502, 503, 504 (server errors)
    - Timeouts and connection errors
  - Fails immediately on other client errors (e.g., 401, 400).
- **Example:**

```python
client = DeepSeekClient(api_key="your-key")
doc = client.generate_documentation(
    "You are an expert documenter.",
    "# File: app.py\nprint('hello')"
)
if doc:
    print(doc)
```

##### `generate_with_truncation_warning(system_prompt: str, user_code: str, max_tokens: int = 300000) -> Optional[str]`

- **Parameters:** Same as `generate_documentation`.
- **Returns:** `Optional[str]` – Same as above.
- **Behavior:** Calls `generate_documentation()` but first performs a rough token estimation (`len(user_code) // 4`) and logs a warning if the input may exceed `max_tokens`.

#### `get_client() -> DeepSeekClient`

- **Returns:** A singleton `DeepSeekClient` instance.
- **Description:** Lazily creates and reuses a single client.

#### `generate_docs(system_prompt: str, user_code: str) -> Optional[str]`

- **Parameters:**
  - `system_prompt` (`str`): System prompt for the model.
  - `user_code` (`str`): Source code to document.
- **Returns:** `Optional[str]` – Generated documentation.
- **Description:** Convenience wrapper around `DeepSeekClient.generate_with_truncation_warning()`.

---

### Module `src.ingest`

This module provides input handling and file collection functions.

#### `CODE_EXTENSIONS: Set[str]`

- **Type:** `set` of file extensions.
- **Description:** Supported code file extensions including `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.scala`, `.cs`, `.sh`, `.pl`, `.lua`, `.r`, `.m`, `.groovy`, `.dart`, `.jl`, `.ex`, `.exs`.

#### `from_paste(code: str, filename: str = "paste_code") -> List[Tuple[str, str]]`

- **Parameters:**
  - `code` (`str`): Source code string.
  - `filename` (`str`): Name to associate with the pasted code. Default `"paste_code"`.
- **Returns:** `List[Tuple[str, str]]` – List with one `(filename, code)` tuple.

#### `from_file(filepath: str) -> List[Tuple[str, str]]`

- **Parameters:** `filepath` (`str`): Path to a file.
- **Returns:** `List[Tuple[str, str]]` – List containing `(filename, content)`.
- **Exceptions:** `FileNotFoundError` if the file does not exist.

#### `from_folder(folderpath: str, extensions: Optional[Set[str]] = None) -> List[Tuple[str, str]]`

- **Parameters:**
  - `folderpath` (`str`): Path to a folder.
  - `extensions` (`Optional[Set[str]]`): File extensions to include. Defaults to `CODE_EXTENSIONS`.
- **Returns:** `List[Tuple[str, str]]` – List of `(relative_path, content)` tuples. Recursively walks the folder. Files that cannot be read are skipped with a warning.
- **Exceptions:** `FileNotFoundError` if the folder does not exist.

#### `from_github(url: str, branch: Optional[str] = None) -> List[Tuple[str, str]]`

- **Parameters:**
  - `url` (`str`): GitHub repository URL.
  - `branch` (`Optional[str]`): Branch to clone. If not given, the default branch is used.
- **Returns:** `List[Tuple[str, str]]` – List of `(relative_path, content)` from the cloned repository.
- **Behavior:** Clones the repository into a temporary directory, then processes it with `from_folder()`.
- **Exceptions:** `RuntimeError` if cloning or reading fails.

#### `from_zip(zip_path: str) -> List[Tuple[str, str]]`

- **Parameters:** `zip_path` (`str`): Path to a ZIP archive.
- **Returns:** `List[Tuple[str, str]]` – List of `(relative_path, content)` extracted from the archive.
- **Exceptions:** `RuntimeError` if extraction or reading fails.

#### `combine_files(files: List[Tuple[str, str]], separator: str = "\n\n") -> str`

- **Parameters:**
  - `files` (`List[Tuple[str, str]]`): List of `(filename, content)` tuples.
  - `separator` (`str`): Separator between combined files. Default `"\n\n"`.
- **Returns:** `str` – Combined string where each file is prefixed with `# File: <filename>`.

#### `detect_language_from_extension(filename: str) -> str`

- **Parameters:** `filename` (`str`): File name or path.
- **Returns:** `str` – Human-readable language name (e.g., `"Python"`, `"JavaScript"`). Returns `"Unknown"` if the extension is not recognized.

---

### Module `src.prompt`

#### `SYSTEM_PROMPT_TEMPLATE: str`

- **Type:** `str`
- **Description:** The base prompt template used to instruct the AI to generate documentation. It includes placeholders for language, project title, author, version, and context.

#### `build_prompt(language: str = "Python", project_name: str = "", author: str = "", version: str = "", context: str = "") -> str`

- **Parameters:**
  - `language` (`str`): Programming language of the code. Default `"Python"`.
  - `project_name` (`str`): Project title. Default empty.
  - `author` (`str`): Author name. Default empty.
  - `version` (`str`): Version number. Default empty.
  - `context` (`str`): Additional context. Default empty.
- **Returns:** `str` – The fully formatted system prompt with placeholders filled.

---

### Module `src.cli`

This module contains the command-line interface and output helpers.

#### `cli()`

- **Type:** Click group.
- **Description:** Root command group for the CLI.

#### `generate()`

The main command for generating documentation.

- **Options:** See the Usage section above for a full list.
- **Behavior:**
  1. Validates that exactly one input source is provided.
  2. Loads code files from the chosen source.
  3. Combines files and auto-detects the language if not specified.
  4. Builds the system prompt via `build_prompt()`.
  5. Displays an animated percentage progress bar while calling `generate_docs()`.
  6. Saves output in the requested format(s).
- **Exceptions:** Exits with status code `1` on invalid input or failure.

#### `class ProgressSpinner`

A terminal progress bar that displays elapsed progress as a percentage.

- `__init__(message: str = "Generating documentation", target_duration: int = 30)`
- `start()` – Starts the animation thread.
- `stop()` – Stops the animation and clears the line.

#### `markdown_to_json(md_text: str) -> dict`

- **Parameters:** `md_text` (`str`): Markdown text with headings.
- **Returns:** `dict` – A dictionary mapping section titles to their content. Sections are detected from headings of level 2–6 (`##` through `######`).

---

### Module `tests.test_ai_client`

Pytest suite for the DeepSeek client.

- `test_successful_generation`: Verifies a 200 response returns the expected content.
- `test_rate_limit_retry`: Verifies that a 429 response triggers a retry and eventually succeeds.
- `test_all_retries_fail`: Verifies that persistent 500 errors return `None`.
- `test_timeout_retry`: Verifies that a timeout triggers retries and returns `None` after exhaustion.

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Add tests for any new functionality.
4. Ensure all tests pass with `pytest`.
5. Submit a pull request with a clear description of the changes.

Please maintain consistent code style and keep the documentation generator’s output high-quality.

## License

Not specified. No license file or license headers were detected in the provided source code.