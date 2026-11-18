# Graphia master plan

## Goal

A small document converter with asynchronous processing, optional accounts, and
no message broker.

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

## Guest access

- `POST /api/auth/guest` creates a disposable local user with `is_guest=true`
  and a 24 hour session. No Zitadel round trip is needed to start a run.
- Guests can create, read, complete, and delete their own jobs. Downloads use
  `require_member` and return `403` for a guest session.
- A guest who completes Zitadel login has their jobs reassigned to the member
  account; the guest user and sessions are deleted. R2 keys keep the upload-time
  owner prefix, and the job row stores both keys.
- Guest sessions are rate limited per IP, and cleanup removes unclaimed guests
  after their jobs expire.

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

## CLI

`cli/` is a Python/Typer client for batch conversion. It scans folders, maps
files to existing operations, and uses the same upload contract as the browser:
create job, PUT to R2 with the presigned URL, complete, poll, download.

- Member-only. `graphia login` uses a 10-minute browser approval request with a
  hashed code and a verifier that never leaves the terminal. The exchange mints
  an ordinary `sessions` row with `client=cli`.
- Tokens live in the OS keychain per host, with a `0600` file fallback.
- Members are throttled per user (120 uploads/hour by default); guests stay on
  the per-IP browser limit and cannot use the CLI.
- The batch runner keeps up to `MAX_ACTIVE_JOBS_PER_USER` files in flight,
  isolates per-file failures, and resumes by skipping completed outputs.

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
