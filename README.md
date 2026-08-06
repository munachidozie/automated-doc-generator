# Automated Documentation Generator

Automated Documentation Generator is a command-line tool that automatically creates comprehensive project documentation from source code. It ingests code from local files, folders, GitHub repositories, or pasted snippets, combines the files into a single input, and sends it to the DeepSeek LLM API. The AI generates structured Markdown documentation, which you can save as Markdown, styled HTML, JSON, or any combination of those formats.

The main entry point is the `generate` command in `src/cli.py`. The project is designed to be run with `python -m src.cli`.

---

## Installation

### Requirements

- Python 3.8+
- A valid DeepSeek API key
- The following Python packages:
  - `requests`
  - `click`
  - `python-dotenv`
  - `GitPython`
  - `Markdown` (for HTML output)

Optional for development/testing:

- `pytest`

### Setup

1. Clone or download the project.
2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   ```

3. Install the dependencies:

   ```bash
   pip install requests click python-dotenv GitPython Markdown pytest
   ```

4. Set your DeepSeek API key. The application reads it from a `.env` file in the project root:

   ```bash
   echo "DEEPSEEK_API_KEY=your-api-key-here" > .env
   ```

   If the key is missing, the application raises `ValueError` at startup.

---

## Usage

Run the CLI from the project root using `python -m src.cli`.

### Basic Example

Generate documentation for a single file:

```bash
python -m src.cli generate --file app.py --title "My Application" --output docs/README.md
```

### Input Sources

Provide exactly one of these options:

| Option | Description |
| --- | --- |
| `--file FILE` | Path to a single code file. |
| `--folder FOLDER` | Folder to scan recursively for supported code files. |
| `--github URL` | GitHub repository URL to clone and process. |
| `--paste "CODE"` | Raw code passed directly as a string. |

### Additional Options

| Option | Default | Description |
| --- | --- | --- |
| `--title TEXT` | `''` | Project title. If empty, the AI infers one. |
| `--author TEXT` | `''` | Author name. If empty, omitted from generated docs. |
| `--version TEXT` | `''` | Version number. If empty, omitted. |
| `--context TEXT` | `''` | Additional context to include in the overview. |
| `--language TEXT` | `''` | Programming language. Auto-detected from the first file's extension if not provided. |
| `--output, -o PATH` | `./docs/README.md` | Output file path. If the extension is `.md`, `.html`, or `.json`, it is replaced with the requested format. |
| `--format, -f` | `md` | Output format(s): `md`, `html`, `json`, `both` (md + html), or `all` (md + html + json). |
| `--max-tokens INT` | `300000` | Maximum tokens for the AI response. DeepSeek V4 supports up to 384000. |
| `--progress-duration INT` | `30` | Target seconds for the animated progress bar to reach 100%. |

### Examples

Generate Markdown and HTML for a folder:

```bash
python -m src.cli generate --folder src --format both --output docs/project
```

Generate documentation from a GitHub repository:

```bash
python -m src.cli generate --github https://github.com/octocat/Hello-World.git --author "Jane Doe"
```

Generate from pasted code:

```bash
python -m src.cli generate --paste 'def add(a, b): return a + b' --language Python
```

---

## API Reference

### Module `src.ai_client`

Handles communication with the DeepSeek API.

#### `class DeepSeekClient`

Primary client for sending code to DeepSeek and receiving generated documentation.

**Constructor:**

```python
DeepSeekClient(api_key: str = DEEPSEEK_API_KEY, model: str = "deepseek-v4-flash")
```

| Parameter | Type | Description |
| --- | --- | --- |
| `api_key` | `str` | DeepSeek API key. Defaults to the value from `.env`. |
| `model` | `str` | Model identifier sent to the API. Default is `"deepseek-v4-flash"`. |

Attributes:

- `base_url` – DeepSeek chat completions endpoint.
- `max_retries` – Number of retry attempts (`3`).
- `retry_delay` – Initial backoff delay in seconds (`2`, doubles per retry).

---

#### `DeepSeekClient.generate_documentation(system_prompt, user_code, max_tokens=300000)`

Sends the system prompt and code to DeepSeek and returns the generated Markdown documentation.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `system_prompt` | `str` | Instructions that define how the documentation should be structured. |
| `user_code` | `str` | Combined source code to document. |
| `max_tokens` | `int` | Maximum number of tokens in the response. Defaults to `300000`. |

**Returns:**

- `Optional[str]` – The generated documentation as a string, or `None` if all retries fail.

**Retry behavior:**

- `429` and `5xx` responses are retried with exponential backoff.
- Timeouts and connection errors are retried.
- Other client errors (e.g., `401`, `400`) fail immediately.

---

#### `DeepSeekClient.generate_with_truncation_warning(system_prompt, user_code, max_tokens=300000)`

Identical to `generate_documentation`, but it first estimates the number of tokens in the input code (roughly 1 token per 4 characters). If the estimate exceeds `max_tokens`, it logs a warning that the AI may truncate the output.

---

#### `get_client()`

Returns a shared, lazily-initialized `DeepSeekClient` instance.

**Returns:**

- `DeepSeekClient`

---

#### `generate_docs(system_prompt, user_code)`

Convenience function that obtains the default client and calls `generate_with_truncation_warning`.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `system_prompt` | `str` | System-level instructions for the AI. |
| `user_code` | `str` | Source code to document. |

**Returns:**

- `Optional[str]`

---

### Module `src.ingest`

Collects and normalizes source code from various inputs.

#### `CODE_EXTENSIONS`

A set of supported file extensions, including `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.scala`, `.cs`, `.sh`, `.pl`, `.pm`, `.lua`, `.r`, `.m`, `.groovy`, `.dart`, `.jl`, `.ex`, `.exs`.

---

#### `from_paste(code, filename="paste_code")`

Creates a single file entry from pasted code.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `code` | `str` | Raw source code. |
| `filename` | `str` | Filename to associate with the code. Defaults to `"paste_code"`. |

**Returns:**

- `List[Tuple[str, str]]` – A single-item list containing `(filename, code)`.

---

#### `from_file(filepath)`

Reads a single file.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `filepath` | `str` | Path to an existing file. |

**Raises:**

- `FileNotFoundError` – If the file does not exist.

**Returns:**

- `List[Tuple[str, str]]` – A list with one tuple: `(file_name, content)`.

---

#### `from_folder(folderpath, extensions=None)`

Recursively walks a folder and reads all files with supported extensions.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `folderpath` | `str` | Path to an existing folder. |
| `extensions` | `Optional[Set[str]]` | Set of extensions to include. Defaults to `CODE_EXTENSIONS`. |

**Raises:**

- `FileNotFoundError` – If the folder does not exist.

**Returns:**

- `List[Tuple[str, str]]` – List of `(relative_path, content)` tuples.

---

#### `from_github(url, branch=None)`

Clones a Git repository into a temporary directory and reads all supported code files.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `url` | `str` | Repository URL. |
| `branch` | `Optional[str]` | Branch to clone. Uses the default branch if omitted. |

**Raises:**

- `RuntimeError` – If cloning or reading fails.

**Returns:**

- `List[Tuple[str, str]]`

---

#### `from_zip(zip_path)`

Extracts a ZIP archive into a temporary directory and reads all supported code files.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `zip_path` | `str` | Path to a ZIP file. |

**Raises:**

- `RuntimeError` – If extraction or reading fails.

**Returns:**

- `List[Tuple[str, str]]`

---

#### `combine_files(files, separator="\n\n")`

Combines multiple file entries into one string, prefixing each file's content with a `# File: <filename>` header.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `files` | `List[Tuple[str, str]]` | List of `(filename, content)` tuples. |
| `separator` | `str` | String used to join file blocks. Defaults to `"\n\n"`. |

**Returns:**

- `str` – The combined code string.

---

#### `detect_language_from_extension(filename)`

Maps a file extension to a human-readable language name.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `filename` | `str` | File name or path. |

**Returns:**

- `str` – E.g., `"Python"`, `"JavaScript"`, or `"Unknown"` if the extension is not recognized.

---

### Module `src.prompt`

Builds the system prompt template used to guide the AI documentation generation.

#### `SYSTEM_PROMPT_TEMPLATE`

A string template with placeholders for `language`, `project_name`, `author`, `version`, and `context`. The template instructs the AI to produce documentation with the following sections:

1. Project Title and overview
2. Installation
3. Usage
4. API Reference
5. Contributing
6. License

---

#### `build_prompt(language="Python", project_name="", author="", version="", context="")`

Fills the system prompt template with the given values.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `language` | `str` | Programming language. Defaults to `"Python"`. |
| `project_name` | `str` | Project title. Defaults to `"Unknown Project"` when empty. |
| `author` | `str` | Author name. Defaults to `"Not specified"` when empty. |
| `version` | `str` | Version. Defaults to `"Not specified"` when empty. |
| `context` | `str` | Additional context. Defaults to `"No additional context provided."` when empty. |

**Returns:**

- `str` – The fully populated system prompt.

---

### Module `src.cli`

Contains the command-line interface and output formatting helpers.

#### `class ProgressSpinner`

Displays an animated progress bar with a percentage that reaches 100% after a target duration.

**Constructor:**

```python
ProgressSpinner(message="Generating documentation", target_duration=30)
```

**Methods:**

- `start()` – Starts the animation in a background daemon thread.
- `stop()` – Stops the animation and clears the progress line.

---

#### `markdown_to_json(md_text)`

Converts Markdown text into a structured dictionary by grouping content under headings (`##` through `######`). Top-level `#` headings are not used as keys.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `md_text` | `str` | Markdown string. |

**Returns:**

- `dict` – Mapping of section heading to section content.

---

#### `cli()`

Click command group. Contains the `generate` subcommand.

---

#### `generate(...)`

The main command that orchestrates the full documentation generation flow:

1. Determines the input source from one of `--file`, `--folder`, `--github`, or `--paste`.
2. Collects and combines the code files.
3. Detects the language if not provided.
4. Builds the system prompt.
5. Calls DeepSeek with a progress bar.
6. Saves the output in the requested format(s).

**CLI options:** See the [Usage](#usage) table above.

---

### Module `src.config`

Loads environment variables from `.env` using `python-dotenv`.

**Exports:**

- `DEEPSEEK_API_KEY` – Reads `DEEPSEEK_API_KEY` from the environment. Raises `ValueError` if not set.

---

### Test Module `tests/test_ai_client.py`

Contains pytest tests for `DeepSeekClient`:

- `test_successful_generation` – Verifies a successful API response returns the expected documentation.
- `test_rate_limit_retry` – Verifies a `429` response triggers a retry that eventually succeeds.
- `test_all_retries_fail` – Verifies that repeated `500` responses return `None`.
- `test_timeout_retry` – Verifies that a timeout triggers retries and ultimately returns `None`.

Run the tests with:

```bash
pytest
```

---

## Development and Manual Testing

The project includes several low-level test scripts:

| File | Purpose |
| --- | --- |
| `src/manual_test.py` | Sends a small sample Python file through `generate_docs`. |
| `src/test_api.py` | Directly calls the DeepSeek API with a tiny code sample. |
| `src/test_ingest.py` | Tests `from_file`, `from_folder`, `from_github`, `combine_files`, and language detection. |
| `src/test_prompt.py` | Tests the full flow on the `src` folder itself. |

These scripts are useful for validating API connectivity and prompt behavior without going through the CLI.

---

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Write or update tests for your changes.
4. Ensure all existing tests pass with `pytest`.
5. Submit a pull request with a clear description of the changes.

Follow standard Python code style and keep new dependencies minimal.

---

## License

Not specified. If you are using or redistributing this project, add a license file that matches your intended terms.