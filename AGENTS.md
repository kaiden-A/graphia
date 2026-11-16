# Graphia — agent rules

## Commands

- `npm run setup` — create local env files and install client + server deps.
- `npm run dev` — start API (8000), processor (8001), client (3000).
- `npm run test:unit` — mock unit tests; no cloud services needed.
- `npm run test:integration` — Neon + R2 round trip; set `RUN_INTEGRATION=1`.
- `npm run lint:server` — ruff.
- `uv run --directory server python -m alembic upgrade head` — apply migrations.
- `uv run --directory server python -m scripts.cleanup_expired` — delete expired files.
- `uv run --directory server python -m scripts.requeue_stale` — recover stale jobs.

## Architecture invariants

- Service A (`server/app`) is public. Service B (`server/processor`) is internal.
- Auth is email/password with server-side sessions; only the sha256 session token
  hash is stored. Every job read/write is scoped by `owner_id`; not-owned is 404.
- A and B never import each other. They share only `server/core` and communicate
  through HTTP, PostgreSQL, and R2.
- `server/converters` contains pure conversion code. It must not import FastAPI,
  SQLAlchemy, or storage code.
- A triggers B with `POST /internal/process` and `X-Internal-Token`. The trigger
  lives only in `app/services/processor_client.py`.
- A never waits for conversion completion. It waits only for B's 202 handshake.
- Job state transitions are conditional SQL updates:
  `PENDING -> PROCESSING -> COMPLETED|FAILED`.
- File bytes never pass through Service A. The browser uploads directly to R2
  with a presigned PUT URL, then confirms the upload.
- R2 objects use generated keys only:
  `conversions/{owner_id}/{job_id}/input/source.{ext}` and
  `.../output/attempt-{n}/result.{ext}`. Never use a user filename as an object key.
- Temp files are cleaned up in `finally`. No permanent local storage.
- API errors use `{"error": "sentence"}`; validation adds `details`.
- Timestamps are tz-aware UTC in PostgreSQL and integer milliseconds on the wire.
- The client talks to the API only through the Next `/api` rewrite. Never add
  `client/app/api` route handlers.

## Local quirks

- LibreOffice is not required for unit tests. DOCX→PDF and Markdown→PDF tests
  skip when `soffice` is unavailable.
- Tests use SQLite with an attached `public` schema; production uses Neon.
- On Windows, run Python entrypoints through `python -m` (for example
  `python -m uvicorn`), not the `.exe` launcher in `.venv/Scripts`; Application
  Control may block the launcher. `npm run setup` patches the venv.
- SQLAlchemy C extensions are disabled by `core/__init__.py` for Windows
  compatibility. The pure-Python fallback is fine at this scale.
- Do not commit `server/.env` or any R2/Neon secret.
