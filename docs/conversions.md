# Conversions

Conversion engines live in `server/converters/` and import nothing from FastAPI,
SQLAlchemy, or storage. The processor is responsible for moving files and
updating job state.

## Operation matrix

| Operation | Input | Output | Engine |
|---|---|---|---|
| `docx_to_pdf` | `.docx` | PDF | LibreOffice headless |
| `pdf_to_markdown` | `.pdf` (selectable text) | Markdown | PyMuPDF + pypdf |
| `txt_to_markdown` | `.txt` | Markdown | stdlib + charset-normalizer |
| `markdown_to_pdf` | `.md`, `.markdown` | PDF | Python-Markdown → HTML → LibreOffice |
| `images_to_pdf` | PNG/JPEG/WebP/GIF/BMP/TIFF | PDF | Pillow |

## Limits

- 25 MB per input file.
- 200 MB per output file.
- 500 PDF pages.
- 50 MP / 10,000 px maximum image.
- 300 second LibreOffice subprocess timeout.
- One DOCX is checked for zip bombs before conversion.
- Text files must be UTF-8 or Windows-1252.

## Error messages

Errors are written to `conversion_jobs.error_message` and shown on the job
ticket. They should be short and actionable:

- “This PDF has no selectable text. Scanned PDFs need OCR, which is not supported yet.”
- “This PDF is password-protected. Remove the password and try again.”
- “This file is not a valid DOCX document.”
- “LibreOffice is not installed on the conversion server.”

Unexpected exceptions are logged with the job ID and displayed as a generic
message, never a traceback.

## Adding a converter

1. Add an operation value to `core/models/enums.py`.
2. Add its metadata to `core/operations.py`.
3. Create `converters/<name>.py` with
   `convert(input_path: Path, context: ConversionContext) -> ConversionResult`.
4. Register it in `processor/registry.py`.
5. Add deep validation in `processor/validation.py` if the format needs it.
6. Add a fixture test in `tests/test_converters.py`.
7. Add the operation to the client automatically through `GET /api/operations`.

## Local LibreOffice

The processor image installs LibreOffice Writer. For local development, install
LibreOffice and make `soffice` available on `PATH`, or set:

```dotenv
SOFFICE_BIN=C:/Program Files/LibreOffice/program/soffice.exe
```

Unit tests skip DOCX→PDF and Markdown→PDF when `soffice` is unavailable.
