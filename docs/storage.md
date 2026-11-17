# Storage

Cloudflare R2 is private. The browser receives only short-lived presigned URLs.

## Bucket

Create a private bucket, for example `graphia`. Do not enable public access.

Object keys:

```text
conversions/{owner_id}/{job_id}/input/source.{ext}
conversions/{owner_id}/{job_id}/output/attempt-{n}/result.{ext}
```

The attempt segment keeps a retried job from overwriting or deleting another
attempt's output.

The `{owner_id}` segment is the owner at upload time. When a guest signs in and
claims a job, the job row changes owner but the existing R2 keys stay in the
guest prefix. Both keys are stored on the row, so downloads and deletion use the
stored keys rather than rebuilding the path.

The original filename is stored in PostgreSQL for display and
`Content-Disposition`; it is never used as an object key.

## Environment

```dotenv
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<access-key>
R2_SECRET_ACCESS_KEY=<secret-key>
R2_BUCKET=graphia
R2_REGION=auto
```

`R2_ENDPOINT` may be omitted if `R2_ACCOUNT_ID` is set.

## CORS

Direct browser uploads require a bucket CORS rule. Replace the origins with your
local and production client origins:

```json
[
  {
    "AllowedOrigins": [
      "http://localhost:3000",
      "http://localhost:3001",
      "https://your-client.example"
    ],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

Apply it with the Cloudflare dashboard or an S3-compatible tool.

## Presigned URLs

- Upload: `put_object`, 10 minutes, signed `Content-Type`.
- Download: `get_object`, 5 minutes, signed `Content-Disposition`.
- Expired or missing objects are not served publicly.
- The API never proxies file bytes, so a 25 MB upload does not hit a Vercel
  request-body limit or a FastAPI request body.

## Lifecycle backstop

Add an R2 lifecycle rule to delete objects older than 30 days. The application
cleanup script is the primary mechanism; the lifecycle rule is a backstop for
orphaned objects.
