from __future__ import annotations

import html
import re
from pathlib import Path

import markdown

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.libreoffice import convert_to_pdf

_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LEADING_H1 = re.compile(r"^\s*<h1\b", re.IGNORECASE)

_CSS = """
@page { size: A4; margin: 18mm 17mm 20mm; }
body {
  font-family: "Liberation Serif", "DejaVu Serif", Georgia, serif;
  font-size: 11pt; line-height: 1.55; color: #1f1b16;
}
h1, h2, h3, h4 {
  font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif;
  line-height: 1.2;
}
h1 { font-size: 22pt; margin: 0 0 14pt; }
h2 { font-size: 15pt; margin: 20pt 0 7pt; }
h3 { font-size: 12pt; margin: 16pt 0 5pt; }
p { margin: 0 0 9pt; }
code, pre { font-family: "Liberation Mono", "DejaVu Sans Mono", monospace; font-size: 9.5pt; }
pre { background: #f2ece1; border: 1px solid #d8cdbb; padding: 8pt; white-space: pre-wrap; }
blockquote {
  border-left: 3pt solid #b23a1f;
  margin: 10pt 0;
  padding: 2pt 0 2pt 10pt;
  color: #62594e;
}
table { border-collapse: collapse; width: 100%; margin: 10pt 0; }
th, td { border: 1px solid #d8cdbb; padding: 5pt 6pt; text-align: left; }
th { background: #f2ece1; }
hr { border: 0; border-top: 1px solid #d8cdbb; margin: 16pt 0; }
"""


def render_markdown_html(text: str, title: str) -> str:
    # Markdown output is untrusted: escape raw HTML tags and do not fetch remote images.
    safe = text.replace("<", "&lt;").replace(">", "&gt;")
    safe = _IMAGE.sub(lambda match: match.group(1), safe)
    body = markdown.markdown(safe, extensions=["extra", "sane_lists"])
    safe_title = html.escape(title)
    heading = "" if _LEADING_H1.match(body) else f"<h1>{safe_title}</h1>"
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{safe_title}</title><style>{_CSS}</style></head>"
        f"<body>{heading}{body}</body></html>"
    )


def convert(input_path: Path, context: ConversionContext) -> ConversionResult:
    try:
        source = input_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        source = input_path.read_text(encoding="cp1252", errors="replace")

    if not source.strip():
        raise ConversionError("This Markdown file is empty.")

    title = Path(context.original_filename).stem
    rendered = render_markdown_html(source, title)
    html_path = context.workdir / "input.html"
    html_path.write_text(rendered, encoding="utf-8")

    output = convert_to_pdf(
        html_path,
        context.workdir,
        timeout_seconds=context.timeout_seconds,
        soffice_bin=context.soffice_bin,
    )
    return ConversionResult(path=output, media_type="application/pdf", extension="pdf")
