# Deployment

## Two Cloud Run services

The variable-by-variable split is in `docs/environment.md`. Give each service
only its own scope; do not copy the whole local `server/.env` to both.

Build two images from the same `server/` context:

```powershell
docker build -f server/Dockerfile.api -t graphia-api server
docker build -f server/Dockerfile.processor -t graphia-processor server
```

Deploy them as separate Cloud Run services:

- `graphia-api` — public, light, no LibreOffice.
- `graphia-processor` — private, heavy, includes LibreOffice.

Set `PROCESSOR_URL` on the API to the processor's Cloud Run URL. Set
`INTERNAL_TOKEN` to the same long random value on both. The current client uses
only that shared token. For stronger isolation, add a Google service-account ID
token in `processor_client.py` and deploy the processor with
`--no-allow-unauthenticated`; otherwise leave the processor public but
token-protected.

## Zitadel

Create one Zitadel Web application with Authorization Code + PKCE and no client
secret. Register the **client** URLs exactly:

```text
https://<client-domain>/api/auth/callback
https://<client-domain>/login
```

Register both localhost and production URLs; do not point them at the Cloud Run
API URL. Set on the API:

```text
ZITADEL_ISSUER
ZITADEL_CLIENT_ID
ZITADEL_REDIRECT_URI
ZITADEL_POST_LOGOUT_URI
PUBLIC_BASE_URL
APP_SECRET
```

`APP_SECRET` signs the short-lived OAuth handshake cookie; keep it stable across
API revisions and instances. There is no `ZITADEL_CLIENT_SECRET`.

Vercel/Firebase preview deployments have different origins. Either use a stable
auth domain, register each preview origin, or accept that previews cannot
complete sign-in. Likewise, if Next runs on `localhost:3001`, register 3001 or
free 3000 and use 3000 consistently.

## Processor CPU

The processor returns `202` and then converts in a bounded executor. On Cloud
Run, use CPU always allocated and one worker:

```powershell
gcloud run deploy graphia-processor `
  --image <image> `
  --region asia-southeast1 `
  --no-allow-unauthenticated `
  --no-cpu-throttling `
  --concurrency 1 `
  --max-instances 1 `
  --memory 2Gi
```

The future Cloud Tasks migration removes the need for CPU always allocated.

## Migrations

Run Alembic manually against Neon:

```powershell
uv run --directory server python -m alembic upgrade head
```

Do not run migrations from the container start command or the CD workflow.

## Client

The Next client can run on Vercel or Firebase Hosting. Because files go directly
to R2, only small JSON requests pass through the `/api` rewrite, so Vercel's
request-body limit is not an issue.

Set:

```dotenv
API_ORIGIN=https://graphia-api-<hash>.run.app
SESSION_COOKIE_NAME=graphia_session
```

Set `COOKIE_SECURE=true` on the API in production. The Zitadel redirect and
post-logout URIs must use the public client origin, not `API_ORIGIN`.

If the client is on **Firebase Hosting** and `/api` is proxied through a
Firebase rewrite, Firebase strips every cookie except `__session`. In that case
set `SESSION_COOKIE_NAME=__session` on both the API and the client, and use
`COOKIE_SECURE=true`. Vercel does not have that restriction.

## Cleanup

Schedule the cleanup script daily (Cloud Scheduler → a small job, or a cron host):

```powershell
uv run --directory server python -m scripts.cleanup_expired
```

Schedule stale-job recovery every few minutes if the processor can be interrupted:

```powershell
uv run --directory server python -m scripts.requeue_stale --minutes 15
```
