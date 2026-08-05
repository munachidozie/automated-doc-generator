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

from src.ingest import (
    from_file, from_folder, from_github, from_paste,
    combine_files, detect_language_from_extension, CODE_EXTENSIONS
)
from src.prompt import build_prompt
from src.ai_client import generate_docs

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
        self.target_duration = target_duration  # seconds to reach 100%
        self.running = False
        self.start_time = None
        self.thread = None
        self.width = 40  # width of the progress bar

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
        # Clear the line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 50) + '\r')
        sys.stdout.flush()

    def _animate(self):
        while self.running:
            elapsed = time.time() - self.start_time
            # Calculate percentage: cap at 100% after target_duration
            progress = min(1.0, elapsed / self.target_duration)
            percent = int(progress * 100)
            bar_length = int(progress * self.width)
            bar = '█' * bar_length + '░' * (self.width - bar_length)
            sys.stdout.write(f'\r{self.message} [{bar}] {percent}%')
            sys.stdout.flush()
            time.sleep(0.1)


# ==============================
# MARKDOWN → JSON HELPER
# ==============================
def markdown_to_json(md_text: str) -> dict:
    """Convert markdown to a structured dict with sections (by headings)."""
    lines = md_text.splitlines()
    result = {}
    current_section = None
    current_content = []

    def save_section():
        if current_section:
            result[current_section] = '\n'.join(current_content).strip()

    for line in lines:
        heading_match = re.match(r'^(#{2,6})\s+(.*)', line)
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
    """Automated Documentation Generator – CLI tool."""
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
@click.option('--max-tokens', default=300000, help='Max tokens for AI response (V4 max is 384000).')
@click.option('--progress-duration', default=30, help='Target seconds for the progress bar to reach 100%.')
def generate(input_file, input_folder, github_url, paste_code,
             title, author, version, context, language,
             output, format, max_tokens, progress_duration):
    """Generate documentation from code."""

    # 1. Determine input source and get files
    files = []
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
            lang = 'Python'  # fallback
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
    doc = generate_docs(prompt, combined_code)
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
            from markdown import Markdown
            from markdown.extensions.toc import TocExtension
            from markdown.extensions.codehilite import CodeHiliteExtension

            md = Markdown(
                extensions=[
                    'tables',
                    'fenced_code',
                    TocExtension(permalink=True, baselevel=2),
                    CodeHiliteExtension(linenums=False, guess_lang=True)
                ],
                extension_configs={
                    'codehilite': {'css_class': 'highlight'}
                }
            )
            html_body = md.convert(doc)
            toc = md.toc

            css = """
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                    max-width: 980px;
                    margin: 40px auto;
                    padding: 0 20px;
                    line-height: 1.6;
                    color: #24292e;
                    background: #fff;
                }
                h1, h2, h3, h4, h5, h6 {
                    border-bottom: 1px solid #eaecef;
                    padding-bottom: 0.3em;
                    margin-top: 24px;
                    margin-bottom: 16px;
                }
                code {
                    background: #f6f8fa;
                    padding: 0.2em 0.4em;
                    border-radius: 3px;
                    font-size: 85%;
                }
                pre {
                    background: #f6f8fa;
                    padding: 16px;
                    border-radius: 6px;
                    overflow: auto;
                    font-size: 85%;
                    line-height: 1.45;
                }
                pre code {
                    background: transparent;
                    padding: 0;
                }
                .highlight {
                    background: #f6f8fa;
                }
                blockquote {
                    border-left: 4px solid #dfe2e5;
                    padding: 0 15px;
                    color: #6a737d;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                }
                table th, table td {
                    border: 1px solid #dfe2e5;
                    padding: 6px 13px;
                }
                table tr:nth-child(2n) {
                    background: #f6f8fa;
                }
                .toc {
                    background: #f6f8fa;
                    padding: 16px 24px;
                    border-radius: 6px;
                    margin-bottom: 24px;
                }
                .toc ul {
                    list-style-type: none;
                    padding-left: 16px;
                }
                .toc li {
                    margin: 4px 0;
                }
                .toc a {
                    color: #0366d6;
                    text-decoration: none;
                }
                .toc a:hover {
                    text-decoration: underline;
                }
            </style>
            """

            html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title or 'Documentation'}</title>
    {css}
</head>
<body>
    <h1>{title or 'Documentation'}</h1>
    <div class="toc">
        <strong>Table of Contents</strong>
        {toc}
    </div>
    {html_body}
</body>
</html>"""

            html_path = base.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
            click.echo(f"HTML documentation saved to: {html_path}")

        except ImportError as e:
            click.echo(f"Warning: missing dependencies for styled HTML – {e}. Falling back to plain HTML.", err=True)
            # Fallback to plain markdown→html without extensions
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