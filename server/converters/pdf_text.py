from __future__ import annotations

from pathlib import Path

import pymupdf

from converters.base import ConversionError

MAX_PAGES = 500
MIN_TEXT_CHARS = 20


def extract_pages(path: Path) -> list[str]:
    """Return the selectable text of every page, stripped, in page order."""
    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise ConversionError("This PDF could not be read.") from exc

    try:
        if document.needs_pass:
            raise ConversionError(
                "This PDF is password protected. Remove the password and try again."
            )
        if document.page_count > MAX_PAGES:
            raise ConversionError(f"This PDF has more than {MAX_PAGES} pages.")
        pages = [page.get_text("text").strip() for page in document]
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError("This PDF could not be read.") from exc
    finally:
        document.close()

    if sum(len(text) for text in pages) < MIN_TEXT_CHARS:
        raise ConversionError(
            "This PDF has no selectable text. Scanned PDFs need OCR, which is not supported yet."
        )
    return pages
