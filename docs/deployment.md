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
- `graphia-processor` — heavy, includes LibreOffice and Ghostscript. It should
  only be reachable by the API; today that means public but
  `X-Internal-Token`-protected (see below), not private.

Set `PROCESSOR_URL` on the API to the processor's Cloud Run URL. Set
`INTERNAL_TOKEN` to the same long random value on both. The current client uses
only that shared token. For stronger isolation, add a Google service-account ID
token in `processor_client.py` and deploy the processor with
`--no-allow-unauthenticated`; otherwise leave the processor public but
token-protected.

## CI/CD

`.github/workflows/cd.yml` runs on pushes to `main` that touch `server/**`, and
on manual dispatch. It builds both images from the `server/` context, pushes
them to Docker Hub, and deploys both Cloud Run services **by digest**.

Repository settings (Settings → Secrets and variables → Actions):

| Kind | Name | Value |
|---|---|---|
| Variable | `APP_NAME` | `graphia`; derives `<APP_NAME>-api` / `<APP_NAME>-processor` for image names and Cloud Run services |
| Variable | `GCP_REGION` | optional; defaults to `asia-southeast1` |
| Secret | `DOCKERHUB_USERNAME` | Docker Hub account |
| Secret | `DOCKERHUB_TOKEN` | Docker Hub access token |
| Secret | `GCP_SA_KEY` | service-account JSON key for `google-github-actions/auth` |

The GCP project comes from the service-account key, so it is not a variable.

Rules the workflow enforces:

- Images are tagged `sha-<full-commit>`. There is no `:latest`.
- Cloud Run deploys `image@sha256:...` from `build-push-action`, not a tag.
  `mirror.gcr.io` can 404 a freshly pushed tag for a minute or two and
  negative-cache that miss; a digest skips the tag lookup.
- Each deploy retries with 30/60/90 s backoff to absorb the remaining
  propagation and rate-limit window. There is no fixed pre-deploy sleep.
- The processor deploys first, then the API, with a `/health` check between.
- Deploys never run migrations.

The workflow ships images and the processor's shape flags only. It expects both
services to exist with their environment variables already set
(`docs/environment.md`); it does not manage env vars, the runtime service
account, or IAM beyond keeping both services invokable. See the processor caveat
above: the workflow keeps the processor public because `processor_client.py`
authenticates only with `X-Internal-Token`.

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

A deploy from the Cloud Console uses Cloud Run's defaults (CPU throttled,
512 MiB, concurrency 80) and makes conversions crawl, because the work runs
after the `202` response. Use the CD workflow or the flags above. PPTX and XLSX
renders are the heaviest jobs, so treat 2 GiB as the floor for the processor.

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
