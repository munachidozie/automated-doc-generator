# src/markdown_utils.py
import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.codehilite import CodeHiliteExtension

def render_markdown_to_html(md_text: str, title: str = "Documentation") -> str:
    """Return a complete HTML document with styling and TOC."""
    md = markdown.Markdown(
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
    html_body = md.convert(md_text)
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
    <title>{title}</title>
    {css}
</head>
<body>
    <h1>{title}</h1>
    <div class="toc">
        <strong>Table of Contents</strong>
        {toc}
    </div>
    {html_body}
</body>
</html>"""
    return html_template

def markdown_to_body_html(md_text: str) -> str:
    """
    Convert Markdown to HTML body content (no <html>, <head>, etc.).
    Useful for embedding in a preview page.
    """
    md = markdown.Markdown(
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
    html_body = md.convert(md_text)
    return html_body