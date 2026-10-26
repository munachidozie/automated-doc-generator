# tests/test_markdown_utils.py
from src.markdown_utils import markdown_to_body_html, render_markdown_to_html


def test_render_includes_toc_and_body():
    out = render_markdown_to_html("## Section\n\nSome text", "My Docs")
    assert "<title>My Docs</title>" in out
    assert "Table of Contents" in out
    assert "Section" in out


def test_render_escapes_title():
    out = render_markdown_to_html("# Doc", "<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out


def test_markdown_to_body_html_has_no_document_shell():
    body = markdown_to_body_html("## Section\n\nSome text")
    assert "<html" not in body.lower()
    assert "Section" in body


def test_render_syntax_highlights_fenced_code():
    """Pygments must stay installed, otherwise HTML output loses token colours."""
    md = "## Snippet\n\n```python\ndef f(x):\n    return x\n```"
    out = render_markdown_to_html(md, "Docs")
    assert 'class="codehilite"' in out
    assert '<span class="k">def</span>' in out

