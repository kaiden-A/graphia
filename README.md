# Graphia

A small, asynchronous document converter.

- **Client** — Next.js App Router
- **Service A** — FastAPI public API, auth, job records, signed R2 URLs
- **Service B** — FastAPI internal processor, LibreOffice/PyMuPDF/Pillow/Ghostscript conversions
- **Database** — Neon PostgreSQL via SQLAlchemy + pg8000
- **Storage** — Cloudflare R2; files go **directly from the browser to R2** with a presigned PUT URL

## Quick start

1. Install Node.js 20+ and `uv`.
2. Install dependencies and create the environment templates:

   ```powershell
   npm install
   npm run setup
   ```

   `npm run setup` copies `server/.env.example` → `server/.env` and
   `client/.env.example` → `client/.env.local` if they do not exist. It also
   patches the Windows venv so Application Control does not block its launcher.

3. Fill in `server/.env` with the Neon URL, R2 credentials, `APP_SECRET`, and
   the Zitadel OIDC values. The file is annotated with `[shared]`, `[api]`, and
   `[processor]` scopes; `docs/environment.md` has the full table and production
   split, and `docs/auth.md` covers the Zitadel application setup. Keep the
   Zitadel redirect URI in sync with the client port. For DOCX/PPTX/XLSX→PDF
   and Markdown→PDF locally, install LibreOffice and put `soffice` on `PATH` (or
   set `SOFFICE_BIN`). For Compress PDF, install Ghostscript and set
   `GHOSTSCRIPT_BIN`. Otherwise use the processor Docker image. Configure R2
   bucket CORS for `PUT` from the client origin; see `docs/storage.md`.
4. Run all three services:

   ```powershell
   npm run dev
   ```

   - Client: <http://localhost:3000>
   - API: <http://localhost:8000>
   - Processor: <http://localhost:8001>

   If port 3000 is already in use, Next chooses the next free port. Zitadel
   redirect URIs must match that port exactly, so either free 3000 or register
   the alternate port and update `ZITADEL_REDIRECT_URI` /
   `ZITADEL_POST_LOGOUT_URI`.

5. Run the database migration:

   ```powershell
   uv run --directory server python -m alembic upgrade head
   ```

6. Visit `/` for the landing page, then `/convert` for the converter. Sign in at
   `/login` through Zitadel. `/signup` opens the Zitadel registration flow with
   `prompt=create`.

## Tests

Mock unit tests do not need Neon, R2, LibreOffice, or Ghostscript:

```powershell
npm run test:unit
```

Integration tests are opt-in and require real credentials in `server/.env`:

```powershell
$env:RUN_INTEGRATION="1"
npm run test:integration
```

The integration suite checks the Neon connection and does a small R2
put/head/read/delete round trip.

## Operations

```powershell
# Delete expired jobs and abandoned uploads
uv run --directory server python -m scripts.cleanup_expired

# Requeue jobs left PROCESSING by a crashed processor
uv run --directory server python -m scripts.requeue_stale --minutes 15

# Create a placeholder user; the first Zitadel login adopts it by email
uv run --directory server python -m scripts.create_user you@example.com
```

## Direct-to-R2 upload

The browser never sends the document through Next.js or Service A:

1. `POST /api/conversions` returns a job and a presigned R2 PUT URL.
2. The browser uploads the file directly to R2.
3. `POST /api/conversions/{id}/complete-upload` verifies the object and triggers
   Service B.

This avoids Vercel's request-body limit. R2 bucket CORS must allow `PUT` from
the client origin. See `docs/storage.md`.

## Why two Python services in one repo

One codebase, two processes, two deployment images. Service A imports only
`core/` and `app/`; Service B imports only `core/`, `processor/`, and
`converters/`. The Docker images enforce the boundary; HTTP, PostgreSQL, and R2
are the runtime contract.

## Docs

- `docs/environment.md` — every env var, its scope, and the API/processor split.
- `docs/auth.md` — Zitadel setup, OIDC flow, provisioning, and troubleshooting.
- `docs/design.md` — private press palette, type, spacing, components, and motion.
- `docs/architecture.md` — request flow, status transitions, failure recovery.
- `docs/storage.md` — R2 keys, CORS, presigned URLs, lifecycle rules.
- `docs/conversions.md` — operation matrix, limits, adding a converter.
- `docs/deployment.md` — Docker, Cloud Run, Firebase/Vercel cookie notes.
