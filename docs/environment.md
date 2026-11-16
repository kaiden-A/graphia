# Environment reference

Graphia has three deployables:

| Deployable | Code | Process |
|---|---|---|
| Service A — API | `server/app` | `python -m uvicorn app.main:app` |
| Service B — Processor | `server/processor` | `python -m uvicorn processor.main:app` |
| Client | `client/` | `next dev` / `next start` |

## At a glance

| Variable group | Service A (API) | Service B (Processor) | Client |
|---|:---:|:---:|:---:|
| `APP_NAME`, `APP_ENV`, `LOG_LEVEL` | yes | yes | — |
| `DATABASE_URL`, `DB_SCHEMA` | yes | yes | — |
| `R2_*` | yes | yes | — |
| `INTERNAL_TOKEN` | yes | yes | — |
| Auth, sessions, Zitadel OIDC | yes | — | — |
| `PROCESSOR_URL` | yes | — | — |
| Upload/job limits | yes | — | — |
| `PROCESSOR_MAX_WORKERS`, `CONVERSION_TIMEOUT_SECONDS`, `SOFFICE_BIN` | — | yes | — |
| `SESSION_COOKIE_NAME` | yes | — | yes (must match) |
| `API_ORIGIN` | — | — | yes |

## How settings load

Both FastAPI services import the same `core.config.Settings`. Loading order:

1. Real environment variables.
2. `server/.env` when the process working directory is `server/`.
3. Defaults in `core/config.py`.

The root `npm` scripts use `uv run --directory server`, so they find the file.
Next.js loads `client/.env.local` automatically.

Locally, one `server/.env` is convenient:

- Service A reads the API and shared values; it ignores processor-only values.
- Service B reads the processor and shared values; it ignores API-only values.
- The client reads its own `client/.env.local`.

In production, do **not** give both services one shared env blob. Give each
service only the variables in its scope. The split below is the intended
production contract.

## Shared by Service A and Service B

These must be present for both services. `INTERNAL_TOKEN` must be the same value
on both.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `APP_NAME` | no | `Graphia` | FastAPI title and log identity. |
| `APP_ENV` | no | `development` | Set to `production` in production. Enables default-secret warnings. |
| `LOG_LEVEL` | no | `INFO` | Python log level. |
| `DATABASE_URL` | yes in production | local Postgres | Neon URL. `postgres://` and `postgresql://` are normalized to `postgresql+pg8000://`; libpq-only options such as `sslmode` are stripped. |
| `DB_SCHEMA` | no | `public` | Explicit schema for every table. Keep `public` unless the database is prepared for another schema. |
| `R2_ACCOUNT_ID` | one of `R2_ACCOUNT_ID` / `R2_ENDPOINT` | empty | Builds `https://<account>.r2.cloudflarestorage.com`. |
| `R2_ENDPOINT` | one of `R2_ACCOUNT_ID` / `R2_ENDPOINT` | empty | Explicit S3-compatible endpoint. Overrides `R2_ACCOUNT_ID` when set. |
| `R2_ACCESS_KEY_ID` | yes | empty | R2 access key. |
| `R2_SECRET_ACCESS_KEY` | yes | empty | R2 secret key. Treat as a secret. |
| `R2_BUCKET` | no | `graphia` | Private bucket name. |
| `R2_REGION` | no | `auto` | R2 region; `auto` is correct for Cloudflare R2. |
| `INTERNAL_TOKEN` | yes | development placeholder | Application-level shared secret for `POST /internal/process`. A sends it; B verifies it. Must match on both services. This is separate from Cloud Run IAM; see `docs/deployment.md`. |

## Service A — API only

These are read by `server/app`. The processor does not need them.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `APP_SECRET` | yes | development placeholder | HMAC key for the short-lived Zitadel OAuth handshake cookie. Must be stable across API instances. |
| `ZITADEL_ISSUER` | yes | empty | Zitadel instance URL, no trailing slash. The app reads `/.well-known/openid-configuration` from it. |
| `ZITADEL_CLIENT_ID` | yes | empty | Public client ID of the Zitadel Web application. Not a secret. |
| `ZITADEL_REDIRECT_URI` | yes | `http://localhost:3000/api/auth/callback` | Must be registered exactly in Zitadel. Use the client origin, not the API origin. |
| `ZITADEL_POST_LOGOUT_URI` | yes | `http://localhost:3000/login` | Must be registered exactly in Zitadel. |
| `PUBLIC_BASE_URL` | no | `http://localhost:3000` | Client origin used for login-failure redirects. |
| `SESSION_COOKIE_NAME` | no | `graphia_session` | Session cookie name. Must match the client. On Firebase Hosting rewrites use `__session`. |
| `SESSION_TTL_DAYS` | no | `30` | Session lifetime in days. |
| `COOKIE_SECURE` | no | `false` | Set `true` in HTTPS production. |
| `PROCESSOR_URL` | yes | `http://localhost:8001` | Service B base URL. Locally `http://localhost:8001`; in Compose `http://processor:8080`; on Cloud Run the processor service URL. |
| `MAX_UPLOAD_MB` | no | `25` | Upload size limit checked by A. |
| `MAX_ACTIVE_JOBS_PER_USER` | no | `3` | Maximum `PENDING`/`PROCESSING` jobs per user. |
| `UPLOADS_PER_HOUR_PER_IP` | no | `20` | In-process upload throttle. |
| `DAILY_JOB_LIMIT` | no | `200` | Global daily job cap. |
| `JOB_EXPIRY_HOURS` | no | `24` | Time before stored input/output objects expire. |
| `UPLOAD_URL_TTL_SECONDS` | no | `600` | Presigned R2 PUT lifetime. |
| `DOWNLOAD_URL_TTL_SECONDS` | no | `300` | Presigned R2 GET lifetime. |

## Service B — processor only

These are read by `server/processor` and the converters. The API does not need
them.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `PROCESSOR_MAX_WORKERS` | no | `1` | In-process job executor size. Keep at `1` for LibreOffice memory safety. |
| `CONVERSION_TIMEOUT_SECONDS` | no | `300` | LibreOffice subprocess timeout. |
| `SOFFICE_BIN` | no | `soffice` | LibreOffice executable. Locally may be `soffice` or a full path. In the processor image it is on `PATH`. |

## Client

The client uses Next.js environment variables from `client/.env.local` locally
and from the hosting provider in production.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `API_ORIGIN` | yes in production | `http://localhost:8000` | Service A origin used by the server-side `/api/:path*` rewrite. Do not append `/api`. |
| `SESSION_COOKIE_NAME` | no | `graphia_session` | Must match Service A. Used by `client/proxy.ts` to decide whether to redirect to `/login`. Use `__session` on Firebase Hosting. |

`API_ORIGIN` is read by the Next server for the rewrite; it is not exposed to the
browser. `SESSION_COOKIE_NAME` is read by the proxy.

## Local/test-only variables

| Variable | Scope | Purpose |
|---|---|---|
| `RUN_INTEGRATION` | tests | Set to `1` to run the Neon + R2 integration tests. Not used by either app. |
| `DISABLE_SQLALCHEMY_CEXT` | Windows | Optional. `core/__init__.py` already sets this to `1` to avoid Application Control blocking SQLAlchemy's C extension. |
| `UV_PROJECT_ENVIRONMENT` | local Windows | Optional uv override if the project `.venv` launcher is blocked. `npm run setup` normally handles this. |

## Local `.env` layout

The generated `server/.env` intentionally contains everything because
`npm run dev` starts both FastAPI processes from one directory. The scope labels
in `server/.env.example` show which service each value belongs to.

The client has a separate file:

```dotenv
# client/.env.local
API_ORIGIN=http://localhost:8000
SESSION_COOKIE_NAME=graphia_session
```

## Production split

Use separate env sets:

### API env

```dotenv
APP_NAME=Graphia
APP_ENV=production
LOG_LEVEL=INFO

DATABASE_URL=postgresql+pg8000://...
DB_SCHEMA=public

R2_ACCOUNT_ID=...
R2_ENDPOINT=
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=graphia
R2_REGION=auto

INTERNAL_TOKEN=...

APP_SECRET=...

ZITADEL_ISSUER=https://<instance>.zitadel.cloud
ZITADEL_CLIENT_ID=...
ZITADEL_REDIRECT_URI=https://<client-domain>/api/auth/callback
ZITADEL_POST_LOGOUT_URI=https://<client-domain>/login
PUBLIC_BASE_URL=https://<client-domain>

SESSION_COOKIE_NAME=graphia_session
SESSION_TTL_DAYS=30
COOKIE_SECURE=true

PROCESSOR_URL=https://graphia-processor-<hash>.run.app

MAX_UPLOAD_MB=25
MAX_ACTIVE_JOBS_PER_USER=3
UPLOADS_PER_HOUR_PER_IP=20
DAILY_JOB_LIMIT=200
JOB_EXPIRY_HOURS=24
UPLOAD_URL_TTL_SECONDS=600
DOWNLOAD_URL_TTL_SECONDS=300
```

### Processor env

```dotenv
APP_NAME=Graphia
APP_ENV=production
LOG_LEVEL=INFO

DATABASE_URL=postgresql+pg8000://...
DB_SCHEMA=public

R2_ACCOUNT_ID=...
R2_ENDPOINT=
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=graphia
R2_REGION=auto

INTERNAL_TOKEN=...

PROCESSOR_MAX_WORKERS=1
CONVERSION_TIMEOUT_SECONDS=300
SOFFICE_BIN=soffice
```

Notice what is absent:

- Processor has no `PROCESSOR_URL`, no cookie settings, and no Zitadel settings.
- API has no `SOFFICE_BIN`, `PROCESSOR_MAX_WORKERS`, or
  `CONVERSION_TIMEOUT_SECONDS`.
- `INTERNAL_TOKEN` is the only auth value both services need.

### Docker Compose

The current Compose file uses one local `server/.env`. When you want the split:

```yaml
services:
  api:
    env_file:
      - ./server/.env.api
    environment:
      PROCESSOR_URL: http://processor:8080

  processor:
    env_file:
      - ./server/.env.processor
```

### Cloud Run

Put non-secret values in `--set-env-vars` and secrets in `--set-secrets`.
At minimum, treat these as secrets:

- `DATABASE_URL`
- `R2_SECRET_ACCESS_KEY`
- `INTERNAL_TOKEN`
- `APP_SECRET`

`ZITADEL_CLIENT_ID` is public. There is no `ZITADEL_CLIENT_SECRET` because the
application uses Authorization Code + PKCE as a public client.

`R2_ACCESS_KEY_ID` is also commonly treated as a secret. `R2_ACCOUNT_ID`,
`R2_BUCKET`, `R2_REGION`, and the limits are non-secret configuration.

Deploy the processor first, copy its URL into the API's `PROCESSOR_URL`, then
deploy the API. See `docs/deployment.md` for the commands and the private
processor caveat.

## Quick checks

- `SESSION_COOKIE_NAME` must match between server and client. A mismatch causes
  a login redirect loop.
- `INTERNAL_TOKEN` must match between API and processor. A mismatch means the
  API gets `401 Unauthorized` from B.
- `R2_ENDPOINT` and `R2_ACCOUNT_ID`: set one. If `R2_ENDPOINT` is non-empty it
  wins.
- `ZITADEL_REDIRECT_URI` and `ZITADEL_POST_LOGOUT_URI` must be registered
  exactly in Zitadel. They point at the client origin, not the API origin.
- `APP_SECRET` must be stable across API instances; it signs the OAuth handshake
  cookie. Rotating it invalidates in-flight sign-ins, not existing sessions.
- Signup is controlled by Zitadel registration policy. There is no app-level
  invite code.
- `COOKIE_SECURE=true` on HTTPS only.
- `PROCESSOR_URL` belongs only to the API.
- Migrations are not run by either service at startup. Run
  `python -m alembic upgrade head` manually.
- The processor does not call the API. The API never waits for conversion
  completion; it waits only for B's `202` handshake.

## Zitadel application setup

Create a **Web** application with **Authorization Code + PKCE** and no client
secret. Register:

- Redirect URI: `http://localhost:3000/api/auth/callback`
- Post-logout URI: `http://localhost:3000/login`
- Production equivalents on the public client domain.

Scopes: `openid profile email`.

The app requires an `email` claim. If email verification is enabled, an
unverified email is rejected. Registration is handled by Zitadel; `prompt=create`
opens its registration page. Use Zitadel org membership/invitations rather than
an app-level allowlist.
