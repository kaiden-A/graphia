# Graphia master plan

## Goal

A small authenticated document converter with asynchronous processing and no
message broker.

```text
Next.js client
   |  JSON only (no file bytes)
   v
FastAPI A  ---- PostgreSQL (jobs, users, sessions)
   |  HTTP POST /internal/process
   v
FastAPI B  ---- PostgreSQL
   |  reads/writes R2
   v
Cloudflare R2  <--- browser presigned PUT
```

## Boundaries

- The browser uploads the document directly to R2.
- A validates metadata, creates the job, signs the upload, verifies the object
  after upload, and triggers B.
- B claims the job atomically, downloads from R2, runs a pure converter, uploads
  the result, and updates the job.
- The frontend polls A. Downloads use short-lived presigned GET URLs.

## Operations

1. DOCX → PDF (LibreOffice Writer)
2. PPTX → PDF (LibreOffice Impress)
3. XLSX → PDF (LibreOffice Calc)
4. PDF → Markdown (PyMuPDF)
5. PDF → Text (PyMuPDF)
6. DOCX → Markdown (mammoth + markdownify)
7. TXT → Markdown
8. Markdown → PDF (Python-Markdown → HTML → LibreOffice)
9. Images → PDF (Pillow)
10. Compress PDF (Ghostscript)

## Status model

- `PENDING`: row exists; upload may not be complete yet.
- `PROCESSING`: B claimed the job.
- `COMPLETED`: output exists in R2.
- `FAILED`: `error_message` is user-safe.

`PENDING -> PROCESSING` is a single conditional `UPDATE ... RETURNING`.
Duplicate triggers are ignored. Stale `PROCESSING` jobs are reset by
`scripts/requeue_stale.py`.

## Future queue migration

Replace only `app/services/processor_client.py:trigger()` with Cloud Tasks.
`processor/runner.py:run_job()` and all converters stay unchanged.
