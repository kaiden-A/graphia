# Architecture

Graphia has one Next.js client and two FastAPI processes. There is no message
broker. PostgreSQL is the durable job record; Cloudflare R2 is the file store.

```text
Browser
  │  JSON only (metadata, status, download ticket)
  ▼
Next.js  ──/api rewrite──►  Service A (FastAPI)
                               │  INSERT job, presigned PUT, HTTP trigger
                               ▼
                          PostgreSQL
                               ▲
                               │  atomic claim, status updates
                               ▼
Browser ──PUT/GET────────►  R2  ◄──── Service B (FastAPI)
                               │        LibreOffice / PyMuPDF / Pillow
                               └──────── run_job()
```

## Service A — public API

- Owns auth (Zitadel OIDC + server-side sessions), job records, and R2 signing.
  The login flow is documented in `docs/auth.md`.
- Validates upload metadata and the first bytes of the uploaded object.
- Never receives the file body. The browser gets a presigned PUT URL and sends
  the bytes directly to R2.
- Calls Service B only after `complete-upload` verifies the object.
- Polls are served from PostgreSQL; downloads are short-lived presigned GET URLs.

## Service B — internal processor

- Exposes `POST /internal/process` behind `X-Internal-Token`.
- Atomically claims a job:
  `UPDATE ... WHERE status='PENDING' RETURNING` → `PROCESSING`.
- Hands the claimed job to a bounded `ThreadPoolExecutor`, then returns `202`.
- Downloads the input to a temp directory, validates it deeply, runs one pure
  converter, uploads the output, and conditionally updates the job to
  `COMPLETED` or `FAILED`.
- Cleans the temp directory in `finally`.

## Upload sequence

1. `POST /api/conversions` with operation, filename, size, and content type.
2. A validates metadata, creates a `PENDING` job, and returns a presigned PUT URL.
3. Browser `PUT`s the file directly to R2.
4. `POST /api/conversions/{id}/complete-upload`.
5. A checks the object size, content type, and magic bytes, marks the upload
   complete, and triggers B.
6. B claims the job, executes the converter, and writes the result to R2.
7. Browser polls `GET /api/conversions/{id}`.
8. `GET /api/conversions/{id}/download` returns a 5-minute signed URL.

## Why the trigger is a handshake, not fire-and-forget

A waits for B's **202 acceptance**, not for the conversion. This matters on
Cloud Run: CPU is throttled after an HTTP response, so a background task
scheduled in A after the response may never send the request. The handshake is
fast and gives A a reliable failure signal. Conversion itself remains fully
asynchronous.

On Cloud Run, run B with CPU always allocated (and one worker) while it uses an
in-process executor. A future Cloud Tasks migration removes that caveat.

## Status transitions

```sql
-- claim
UPDATE conversion_jobs
SET status = 'PROCESSING', started_at = now(), attempts = attempts + 1
WHERE id = :id AND status = 'PENDING' AND upload_completed_at IS NOT NULL
RETURNING *;

-- complete (attempts pins this run)
UPDATE conversion_jobs
SET status = 'COMPLETED', output_key = :key, completed_at = now()
WHERE id = :id AND status = 'PROCESSING' AND attempts = :attempt;

-- fail
UPDATE conversion_jobs
SET status = 'FAILED', error_message = :message, completed_at = now()
WHERE id = :id AND status = 'PROCESSING' AND attempts = :attempt;
```

Duplicate triggers match zero rows and are ignored. The input key is stable;
the output key includes the attempt number
(`output/attempt-{n}/result.{ext}`) so a retried run cannot delete another
attempt's output.

## Failure recovery

- A trigger failure marks the job `FAILED` only while it is still `PENDING`.
  If B claimed it, A's conditional update does nothing.
- `scripts/requeue_stale.py` resets `PROCESSING` jobs older than a threshold to
  `PENDING` and re-triggers them.
- `scripts/cleanup_expired.py` deletes expired jobs and abandoned uploads from
  PostgreSQL and R2.
- Jobs cannot be downloaded after `expires_at`; the API returns `410 Gone`.
