# CLI

`graphia` is a batch client for the same conversion service the browser uses. It
scans a folder, maps each file to an operation, uploads directly to R2, polls the
job, and writes the result into a mirrored output tree.

The CLI is **member-only**. Guests can use the browser converter, but cannot
approve terminal access.

## Install

```powershell
uv tool install graphia
```

During development:

```powershell
uv sync --directory cli
uv run --directory cli graphia --help
```

## Sign in

```powershell
graphia login --server http://localhost:3000
```

The command creates a one-time request and opens the Graphia `/cli` page. Sign in
with Zitadel if needed, check the device name, and click **Approve**. The CLI
exchanges the code plus a verifier that never leaves the terminal for a normal
server session.

- Tokens are stored per server host in the OS keychain.
- If the keychain is unavailable, Graphia writes a `0600` credentials file.
- `GRAPHIA_NO_KEYRING=1` forces the file fallback.
- `GRAPHIA_TOKEN` overrides both for tests and automation.
- `graphia logout` revokes the session and removes the local token.

The approval request expires after 10 minutes and can be used once. A shared
approval URL is not enough to mint a token without the CLI's verifier.

## Convert

```powershell
# One file, output beside the source
graphia convert deck.pptx --to pdf

# A folder, mirrored into .\graphia-output
graphia convert .\decks --to pdf

# Mixed folder: PDF, DOCX, and TXT become Markdown
graphia convert .\documents --to md

# Explicit operation
graphia convert .\pdfs --operation compress_pdf --out .\small

# Inspect the plan, upload nothing
graphia convert .\decks --to pdf --dry-run

# Machine-readable report
graphia convert .\decks --to pdf --json
```

### Target mapping

| Target | Sources |
|---|---|
| `pdf` | DOCX, PPTX, XLSX, Markdown, PNG/JPG/JPEG/WEBP/GIF/BMP/TIF/TIFF |
| `md` | PDF, DOCX, TXT |
| `txt` | PDF |

`--operation` overrides the mapping and takes an id from `graphia operations`
(hyphens and underscores both work). `compress_pdf` has no target format, so it
must use `--operation`.

Each image becomes its own PDF, matching the browser operation. Combining
images into one PDF is not a Graphia operation.

### Scan rules

- Folders are recursive by default; `--no-recursive` scans only the top level.
- Dotfiles and dot-directories are skipped unless `--include-hidden`.
- `node_modules`, `.git`, `.venv`, `__pycache__`, `.next`, and similar tool
  directories are always skipped.
- Office temp files (`~$...`) are skipped.
- Empty files, files over the server limit, unsupported extensions, and files
  that are already the target format are reported as skipped, not failures.
- The output directory is excluded from the scan, so reruns do not convert
  their own results.

### Output layout

- A single file writes beside itself: `deck.pptx` → `deck.pdf`.
- A folder writes to `.\graphia-output\`, mirroring relative paths:
  `decks\q1\deck.pptx` → `graphia-output\q1\deck.pdf`.
- Multiple input roots get a folder per root to avoid collisions.
- `--out` overrides the location for both single files and folders.
- Existing output is skipped unless `--overwrite`.
- Two sources that would write the same destination are reported as errors
  before anything is uploaded.

Rerunning a failed batch resumes: completed outputs are skipped, and the
remaining files are converted.

### Parallelism and limits

- `--jobs` defaults to 3 and is capped by the server's `MAX_ACTIVE_JOBS_PER_USER`.
- Signed-in users get `UPLOADS_PER_HOUR_PER_MEMBER` uploads per hour (default
  120). Guests remain on the per-IP browser limit and cannot use the CLI.
- The processor converts one job at a time; the CLI's parallelism overlaps
  upload, conversion, and download, not CPU.
- Outputs stay in the locker for `JOB_EXPIRY_HOURS` (default 24 hours).

## Configuration

Resolution order:

1. `--server`
2. `GRAPHIA_SERVER`
3. the saved config file (`graphia doctor` prints the path)
4. `http://localhost:3000`

`graphia login` saves the server after a successful approval.
`GRAPHIA_CONFIG_DIR` overrides the config directory.

## Commands

```text
graphia login       Sign in by approving the terminal in a browser.
graphia logout      Revoke the stored session.
graphia whoami      Show the signed-in account.
graphia doctor      Check the server, session, limits, and operations.
graphia operations  List supported conversions.
graphia convert     Convert files or scan folders.
```

`graphia doctor` reports the resolved server, config path, token source, API
version, limits, and operation count. It never prints a token.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Everything requested was converted or deliberately skipped |
| `1` | One or more conversions failed, or the plan has errors |
| `2` | Usage, auth, connection, or server error |
| `130` | Interrupted |

## How it works

1. `POST /api/cli/requests` creates a hashed, 10-minute approval request.
2. The browser approves it with the normal `graphia_session` cookie.
3. `POST /api/cli/token` checks the code and verifier, then creates a normal
   server-side session with `client=cli` and the device name as its label.
4. Every API call uses `Authorization: Bearer <token>`. The API stores only the
   token's sha256 hash, exactly like a browser session.
5. `POST /api/conversions` returns a presigned R2 PUT URL. The CLI uploads the
   bytes directly to R2, then calls `complete-upload`.
6. The CLI polls the job and downloads the result with the presigned GET URL.

File bytes never pass through Service A. R2 object keys are still generated by
the API.

## Release

The package is `graphia` on PyPI and the command is `graphia`.

One-time setup on PyPI: **Your projects → Publishing → Add a pending publisher**
(or, once the project exists, **graphia → Publishing → Add a trusted publisher**),
with:

- Publisher: GitHub
- Repository: `kaiden-A/graphia`
- Workflow: `release-cli.yml`
- Environment: `pypi`

Then bump both version strings, commit, and push a tag:

```powershell
# cli/pyproject.toml and cli/src/graphia_cli/__init__.py
uv run --directory cli python -m pytest
uv run --directory cli python -m ruff check .
git tag cli-v0.1.0
git push origin cli-v0.1.0
```

The `Release CLI` workflow checks that the tag matches the package version, runs
the tests, builds the sdist and wheel, and publishes with PyPI trusted
publishing (OIDC, no long-lived token).

Manual fallback with an API token:

```powershell
Remove-Item .\cli\dist -Recurse -Force -ErrorAction SilentlyContinue
uv build --directory cli
uv publish --dry-run --directory cli
uv publish --directory cli --token pypi-...
```

Inspect the artifacts before publishing:

```powershell
uv run --isolated --with .\cli\dist\graphia-0.1.0-py3-none-any.whl graphia --version
```

## Troubleshooting

- **`This server does not support the Graphia CLI yet.`** The API is older than
  the CLI. Deploy the current API and run the new migration.
- **`Single sign-on is not configured`** Set `ZITADEL_ISSUER` and
  `ZITADEL_CLIENT_ID` on the API; the CLI reuses the browser login.
- **`Not signed in`** Run `graphia login`, or pass `--server` for the right host.
- **`Your session has expired`** The 30-day session ended or was revoked. Run
  `graphia login` again.
- **`The CLI requires a member account`** A guest session cannot be used. Sign in
  with a member account.
- **`Too many uploads`** The hourly member limit or the active-job limit was hit.
  Wait for active jobs to finish, or raise the server limit.
- **Approval page says the request expired** Requests last 10 minutes. Rerun
  `graphia login`.
- **Windows paths with spaces** Quote the path: `graphia convert ".\Q1 decks" --to pdf`.
