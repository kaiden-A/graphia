# Graphia — agent rules

## Commands

- `npm run setup` — create local env files and install client, server, and CLI deps.
- `npm run dev` — start API (8000), processor (8001), client (3000).
- `npm run test:unit` — mock unit tests; no cloud services needed.
- `npm run test:integration` — Neon + R2 round trip; set `RUN_INTEGRATION=1`.
- `npm run test:cli` — CLI unit and command tests; no server needed.
- `npm run lint:server` — ruff for the server.
- `npm run lint:cli` — ruff for the CLI.
- `uv run --directory server python -m alembic upgrade head` — apply migrations.
- `uv run --directory server python -m scripts.cleanup_expired` — delete expired files.
- `uv run --directory server python -m scripts.requeue_stale` — recover stale jobs.

Environment scope reference: `docs/environment.md`. Local `server/.env` contains
shared, API-only, and processor-only values for convenience; production must give
each service only its own scope.

Design reference: `docs/design.md`. The client follows the private press system:
warm sand surfaces, espresso ink, and a cobalt action accent kept under 5% of the
page, Manrope with Geist Mono only for ticket data, Phosphor icons, and
scale-bound spacing and radii. Do not reintroduce the poolside arcade, the
scrapbook, the Greek journal, or gradient-heavy backgrounds.

## Architecture invariants

- Service A (`server/app`) is public. Service B (`server/processor`) is internal.
- Auth is Zitadel OIDC Authorization Code + PKCE (public client, no secret).
  Session tokens are random; only their sha256 hash is stored. The OAuth
  handshake cookie is signed with `APP_SECRET`. Every job read/write is scoped by
  `owner_id`; not-owned is 404. See `docs/auth.md` and `docs/environment.md`.
- Guest runs use a disposable local user with `is_guest=true` and a 24 hour
  session. Guests can convert and read their own jobs, but `GET .../download`
  uses `require_member` and returns 403. Signing in claims guest jobs; the job
  row keeps the R2 keys from upload time.
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
- The CLI (`cli/`) is a client, not a service. It never imports `server/`, never
  touches PostgreSQL or R2 directly, and uses the same public API. It uploads
  with the presigned PUT URL, like the browser.
- CLI access is member-only. `POST /api/cli/requests` is public, but approval
  requires a member cookie and a guest bearer token is rejected by
  `require_auth`. CLI tokens are ordinary `sessions` rows with `client=cli`.
- CLI approval codes and verifiers are stored only as hashes. Requests are
  single-use, expire in `CLI_AUTH_REQUEST_TTL_MINUTES`, and are bound to the
  verifier. Never log a raw code, token, or presigned URL.
- Upload throttling is per user for members and per IP for guests. Do not
  re-key guests onto the member limit.

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
