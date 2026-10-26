# tests/test_cli.py
import sys
import time

from click.testing import CliRunner

from src.cli import ProgressSpinner, cli, markdown_to_json


def test_markdown_to_json_captures_h1_title():
    data = markdown_to_json("# My Project\n\n## Overview\n\nHello")
    assert data["My Project"] == ""
    assert data["Overview"] == "Hello"


def test_markdown_to_json_merges_duplicate_headings():
    data = markdown_to_json("## Notes\n\na\n\n## Notes\n\nb")
    assert "a" in data["Notes"]
    assert "b" in data["Notes"]


def test_markdown_to_json_ignores_content_before_first_heading():
    data = markdown_to_json("preamble\n\n## Section\n\nbody")
    assert list(data) == ["Section"]


def test_markdown_to_json_ignores_headings_inside_fenced_code():
    md = (
        "## Usage\n\n```bash\n# Install the tool\npip install x\n```\n\n"
        "## Notes\n\ntext\n"
    )
    data = markdown_to_json(md)
    assert list(data) == ["Usage", "Notes"]
    assert "# Install the tool" in data["Usage"]


def test_markdown_to_json_handles_tilde_fences():
    md = "## A\n\n~~~\n## not a heading\n~~~\n\n## B\n\nb\n"
    assert list(markdown_to_json(md)) == ["A", "B"]


def test_markdown_to_json_unclosed_fence_swallows_remaining_headings():
    md = "## A\n\n```\n# not a heading\n"
    assert list(markdown_to_json(md)) == ["A"]



def test_cli_help_mentions_project_name():
    result = CliRunner().invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Automatic Source Code Document Generator' in result.output


def test_generate_help_exposes_model_and_timeout():
    result = CliRunner().invoke(cli, ['generate', '--help'])
    assert result.exit_code == 0
    assert '--model' in result.output
    assert '--timeout' in result.output
    assert '--max-tokens' in result.output


class _FakeStdout:
    """Minimal stdout stand-in with a configurable encoding."""

    def __init__(self, encoding):
        self.encoding = encoding
        self.written = []

    def write(self, text):
        self.written.append(text)

    def flush(self):
        pass


class _UnencodableStdout(_FakeStdout):
    def write(self, text):
        raise UnicodeEncodeError('charmap', text, 0, 1, 'not representable')


def test_spinner_uses_block_glyphs_on_utf8(monkeypatch):
    monkeypatch.setattr(sys, 'stdout', _FakeStdout('utf-8'))
    assert ProgressSpinner().bar_chars == ('█', '░')


def test_spinner_falls_back_to_ascii_on_legacy_codepage(monkeypatch):
    # cp1252 consoles cannot encode the block glyphs (real Windows CLI crash).
    monkeypatch.setattr(sys, 'stdout', _FakeStdout('cp1252'))
    assert ProgressSpinner().bar_chars == ('#', '-')


def test_spinner_never_raises_when_stdout_cannot_encode(monkeypatch):
    monkeypatch.setattr(sys, 'stdout', _UnencodableStdout('cp1252'))
    spinner = ProgressSpinner(target_duration=0.01)
    spinner.start()
    time.sleep(0.15)
    spinner.stop()  # must not raise
    assert spinner.running is False

