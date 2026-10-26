# src/cli.py
import os
import sys
import time
import threading
import json
import re
import click
from pathlib import Path
from typing import Optional

from src.config import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_TIMEOUT
from src.ingest import (
    from_file, from_folder, from_github, from_paste,
    combine_files, detect_language_from_extension, CODE_EXTENSIONS
)
from src.prompt import build_prompt
from src.ai_client import generate_docs
from src.markdown_utils import render_markdown_to_html  # shared helper

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================
# PROGRESS BAR (PERCENTAGE)
# ==============================
class ProgressSpinner:
    """Animated progress bar with percentage."""
    def __init__(self, message="Generating documentation", target_duration=30):
        self.message = message
        self.target_duration = target_duration
        self.running = False
        self.start_time = None
        self.thread = None
        self.width = 40
        # Legacy Windows consoles (e.g. cp1252) cannot encode block glyphs, which
        # made the animation thread die with UnicodeEncodeError. Fall back to ASCII.
        self.bar_chars = ('█', '░') if self._stdout_supports_unicode() else ('#', '-')

    @staticmethod
    def _stdout_supports_unicode() -> bool:
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        try:
            '█░'.encode(encoding)
        except (UnicodeEncodeError, LookupError):
            return False
        return True

    def start(self):
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        try:
            sys.stdout.write('\r' + ' ' * (len(self.message) + 50) + '\r')
            sys.stdout.flush()
        except (OSError, UnicodeEncodeError, ValueError):
            # Nothing sensible to do if the stream is gone; never raise from cleanup.
            pass

    def _animate(self):
        filled, empty = self.bar_chars
        while self.running:
            elapsed = time.time() - self.start_time
            progress = min(1.0, elapsed / self.target_duration)
            percent = int(progress * 100)
            bar_length = int(progress * self.width)
            bar = filled * bar_length + empty * (self.width - bar_length)
            try:
                sys.stdout.write(f'\r{self.message} [{bar}] {percent}%')
                sys.stdout.flush()
            except (OSError, UnicodeEncodeError, ValueError):
                # A closed or non-encodable stdout must not kill the loop with a
                # traceback that would be painted over the real output.
                self.running = False
                return
            time.sleep(0.1)


# ==============================
# MARKDOWN → JSON HELPER
# ==============================
def markdown_to_json(md_text: str) -> dict:
    """Convert markdown to a structured dict with sections (by headings).

    Headings inside fenced code blocks are skipped: shell comments such as
    ``# Install the tool`` would otherwise be exported as doc sections.
    """
    lines = md_text.splitlines()
    result = {}
    current_section = None
    current_content = []
    in_fence = False
    fence_char = None

    def save_section():
        if not current_section:
            return
        content = '\n'.join(current_content).strip()
        if current_section not in result:
            result[current_section] = content
        elif content:
            # Repeated headings are merged rather than silently overwriting.
            existing = result[current_section]
            result[current_section] = f"{existing}\n\n{content}".strip() if existing else content

    for line in lines:
        fence_match = re.match(r'^(`{3,}|~{3,})', line.lstrip())
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence, fence_char = True, marker[0]
            elif marker[0] == fence_char:
                in_fence, fence_char = False, None
            current_content.append(line)
            continue

        heading_match = None if in_fence else re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            save_section()
            title = heading_match.group(2).strip()
            current_section = title
            current_content = []
        else:
            current_content.append(line)

    save_section()
    return result


# ==============================
# CLI COMMANDS
# ==============================
@click.group()
def cli():
    """Automatic Source Code Document Generator – CLI tool."""
    pass


@cli.command()
@click.option('--file', 'input_file', type=click.Path(exists=True, dir_okay=False),
              help='Single file to document.')
@click.option('--folder', 'input_folder', type=click.Path(exists=True, file_okay=False),
              help='Folder containing code files.')
@click.option('--github', 'github_url', help='GitHub repository URL.')
@click.option('--paste', 'paste_code', help='Paste code directly as a string.')
@click.option('--title', default='', help='Project title.')
@click.option('--author', default='', help='Author name.')
@click.option('--version', default='', help='Version number.')
@click.option('--context', default='', help='Additional context about the project.')
@click.option('--language', default='', help='Programming language (auto-detect if not given).')
@click.option('--output', '-o', default='./docs/README.md', help='Output file path (default: ./docs/README.md).')
@click.option('--format', '-f', default='md',
              type=click.Choice(['md', 'html', 'json', 'both', 'all']),
              help='Output format(s): md, html, json, both (md+html), all (md+html+json).')
@click.option('--max-tokens', default=DEFAULT_MAX_TOKENS, show_default=True, type=int,
              help='Max tokens for the AI response.')
@click.option('--model', default=DEFAULT_MODEL, show_default=True,
              help='DeepSeek model to use (e.g. deepseek-v4-flash, deepseek-v4-pro).')
@click.option('--timeout', default=DEFAULT_TIMEOUT, show_default=True, type=int,
              help='Per-request timeout in seconds.')
@click.option('--progress-duration', default=30, help='Target seconds for the progress bar to reach 100%.')
def generate(input_file, input_folder, github_url, paste_code,
             title, author, version, context, language,
             output, format, max_tokens, model, timeout, progress_duration):
    """Generate documentation from code."""

    # 1. Determine input source and get files
    files = []
    try:
        if input_file:
            files = from_file(input_file)
        elif input_folder:
            files = from_folder(input_folder)
        elif github_url:
            files = from_github(github_url)
        elif paste_code:
            files = from_paste(paste_code)
        else:
            click.echo("Error: Please provide one of --file, --folder, --github, or --paste.", err=True)
            sys.exit(1)
    except (FileNotFoundError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not files:
        click.echo("No code files found.", err=True)
        sys.exit(1)

    click.echo(f"Found {len(files)} code file(s).")

    # 2. Combine files
    combined_code = combine_files(files)

    # 3. Detect language if not provided
    if not language:
        lang = detect_language_from_extension(files[0][0])
        if lang == 'Unknown':
            lang = 'Python'
        language = lang
        click.echo(f"Auto-detected language: {language}")

    # 4. Build the system prompt
    prompt = build_prompt(
        language=language,
        project_name=title,
        author=author,
        version=version,
        context=context
    )

    # 5. Generate documentation (with percentage progress bar)
    spinner = ProgressSpinner("Generating documentation", target_duration=progress_duration)
    spinner.start()
    try:
        doc = generate_docs(
            prompt,
            combined_code,
            model=model,
            timeout=timeout,
            max_tokens=max_tokens,
        )
    finally:
        # Always stop the animation, otherwise it keeps painting over tracebacks.
        spinner.stop()

    if doc is None:
        click.echo("Failed to generate documentation. Check logs for details.", err=True)
        sys.exit(1)

    # 6. Save output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Helper to get base name without extension
    base = output_path.with_suffix('') if output_path.suffix in ['.md', '.html', '.json'] else output_path

    # ---- Markdown ----
    if format in ('md', 'both', 'all'):
        md_path = base.with_suffix('.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(doc)
        click.echo(f"Markdown documentation saved to: {md_path}")

    # ---- HTML ----
    if format in ('html', 'both', 'all'):
        try:
            # Use the shared helper
            html_content = render_markdown_to_html(doc, title or 'Documentation')
            html_path = base.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            click.echo(f"HTML documentation saved to: {html_path}")
        except ImportError as e:
            click.echo(f"Warning: missing dependencies for styled HTML – {e}. Falling back to plain HTML.", err=True)
            import markdown
            html_body = markdown.markdown(doc)
            html_path = base.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"<html><body>{html_body}</body></html>")
            click.echo(f"Plain HTML saved to: {html_path}")

    # ---- JSON ----
    if format in ('json', 'all'):
        json_data = markdown_to_json(doc)
        json_path = base.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        click.echo(f"JSON documentation saved to: {json_path}")

    click.echo("Documentation generation complete.")


if __name__ == '__main__':
    cli()