# Conversions

Conversion engines live in `server/converters/` and import nothing from FastAPI,
SQLAlchemy, or storage. The processor is responsible for moving files and
updating job state.

## Operation matrix

| Operation | Input | Output | Engine |
|---|---|---|---|
| `docx_to_pdf` | `.docx` | PDF | LibreOffice headless |
| `pptx_to_pdf` | `.pptx` | PDF | LibreOffice headless |
| `xlsx_to_pdf` | `.xlsx` | PDF | LibreOffice headless |
| `pdf_to_markdown` | `.pdf` (selectable text) | Markdown | PyMuPDF |
| `pdf_to_text` | `.pdf` (selectable text) | Text | PyMuPDF |
| `docx_to_markdown` | `.docx` | Markdown | mammoth + markdownify |
| `txt_to_markdown` | `.txt` | Markdown | stdlib + charset-normalizer |
| `markdown_to_pdf` | `.md`, `.markdown` | PDF | Python-Markdown → HTML → LibreOffice |
| `images_to_pdf` | PNG/JPEG/WebP/GIF/BMP/TIFF | PDF | Pillow |
| `compress_pdf` | `.pdf` | PDF | Ghostscript |

## Limits

- 25 MB per input file.
- 200 MB per output file.
- 500 PDF pages for PDF inputs and for any LibreOffice render.
- 200 slides per PPTX.
- 50 MP / 10,000 px maximum image.
- 300 second LibreOffice and Ghostscript subprocess timeout.
- DOCX, PPTX, and XLSX inputs are checked for zip bombs before conversion.
- Text files must be UTF-8 or Windows-1252.
- DOCX to Markdown drops images. The output is one Markdown file, so images are
  not inlined or packaged alongside it.
- Compress PDF uses the Ghostscript `/ebook` preset and returns the original file
  when the result would be larger. The output is named
  `<stem>-compressed.pdf`.

## Error messages

Errors are written to `conversion_jobs.error_message` and shown on the job
ticket. They should be short and actionable:

- “This PDF has no selectable text. Scanned PDFs need OCR, which is not supported yet.”
- “This PDF is password-protected. Remove the password and try again.”
- “This file is not a valid DOCX document.”
- “This file is not a valid PPTX presentation.”
- “This file is not a valid XLSX workbook.”
- “This presentation has more than 200 slides.”
- “This document produced more than 500 PDF pages.”
- “LibreOffice is not installed on the conversion server.”
- “Ghostscript is not installed on the conversion server.”

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

DOCX to PDF, PPTX to PDF, XLSX to PDF, and Markdown to PDF run LibreOffice
headless. The processor image installs it at build time (`libreoffice-writer`,
`libreoffice-impress`, and `libreoffice-calc` plus Liberation, Carlito, and
Caladea fonts) and fails the build if `soffice --version` does not answer. Local
development does not use that image, so the engine must be installed once on the
host.

Windows:

```powershell
winget install --id TheDocumentFoundation.LibreOffice -e --silent --accept-package-agreements --accept-source-agreements
```

Then point the processor at the binary in `server/.env`:

```dotenv
SOFFICE_BIN=C:/Program Files/LibreOffice/program/soffice.exe
```

Verify both the binary and the setting:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.com" --version
uv run --directory server python -c "from core.config import settings; from converters.libreoffice import soffice_available; print(settings.soffice_bin, soffice_available(settings.soffice_bin))"
```

Use `soffice.com` for console output. `soffice.exe` is a GUI subsystem launcher
and prints nothing, but works for conversions.

Restart the processor after changing `.env`; settings are read at startup. The
processor logs the resolved binary on boot and `GET /` reports
`{"soffice": true}`. The first conversion is slow because every run gets a fresh
LibreOffice profile.

Unit tests read `settings.soffice_bin`, so an absolute path is enough. When the
binary is missing, the Office tests skip and every PDF producing run fails with
“LibreOffice is not installed on the conversion server.”

## Local Ghostscript

Compress PDF runs Ghostscript. The processor image installs it at build time;
local development needs it only for that operation.

Windows:

```powershell
winget install --id ArtifexSoftware.GhostScript -e
```

If the package is unavailable, install the official build from
<https://ghostscript.com/releases/>. Then point the processor at the console
binary in `server/.env`:

```dotenv
GHOSTSCRIPT_BIN=C:/Program Files/gs/gs10.05.1/bin/gswin64c.exe
```

On Linux the default `gs` works when it is on `PATH`. Verify both the binary and
the setting:

```powershell
& "C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe" --version
uv run --directory server python -c "from core.config import settings; from converters.ghostscript import ghostscript_available; print(settings.ghostscript_bin, ghostscript_available(settings.ghostscript_bin))"
```

Restart the processor after changing `.env`. `GET /` reports
`{"ghostscript": true}` when the binary resolves, and the Compress test skips
when it does not.
