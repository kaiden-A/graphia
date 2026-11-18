# Graphia CLI

Batch document conversion from the terminal, powered by a Graphia server.

```powershell
uv tool install graphia
graphia login
graphia convert .\decks --to pdf
```

The default server is the deployed Graphia API at
`https://elysiaa-graphia-api-1023333674013.asia-southeast1.run.app`. For local
development use `--server http://localhost:3000` or `GRAPHIA_SERVER`.

## Commands

```text
graphia login      Sign in by approving this terminal in a browser.
graphia logout     Revoke the stored session.
graphia whoami     Show the signed-in account.
graphia doctor     Check the server, session, limits, and operations.
graphia operations List supported conversions.
graphia convert    Convert files or scan folders.
```

## Convert

```powershell
# One file, output beside the source
graphia convert deck.pptx --to pdf

# A folder, mirrored into .\graphia-output
graphia convert .\decks --to pdf

# A mixed folder: PDFs, DOCX, and TXT become Markdown
graphia convert .\documents --to md

# Compress every PDF (no target format needed)
graphia convert .\pdfs --operation compress_pdf --out .\small

# Inspect first, upload nothing
graphia convert .\decks --to pdf --dry-run

# Script-friendly report
graphia convert .\decks --to pdf --json
```

- Folders are recursive by default; use `--no-recursive` to scan only the top
  level.
- A single file writes beside itself. Folders write to `.\graphia-output\` with
  the source tree mirrored. `--out` overrides both.
- Existing output files are skipped. Pass `--overwrite` to replace them.
- `--jobs` defaults to 3 and is capped by the server's active-job limit.
- `--operation` takes an id from `graphia operations`; `--to` picks the
  operation per file (`pptx`, `docx`, `xlsx`, images, and Markdown to PDF; PDF,
  DOCX, and TXT to Markdown; PDF to text).
- Images become one PDF per image, matching the browser app.
- Re-running a batch resumes: completed outputs are skipped.

Exit codes: `0` success, `1` one or more files failed or the plan has errors,
`2` usage/auth/server error, `130` interrupted.

## Sign-in

The CLI is member-only. `graphia login` opens a Graphia page where you approve
the terminal; a one-time code plus a local verifier is exchanged for a normal
server session. No password is typed in the terminal and no token appears in
the browser. The approval page URL comes from the API's `PUBLIC_BASE_URL`; it
must be the deployed client origin, not the Cloud Run API origin. If the client
is intentionally local while the API is remote, add `--allow-local-approval`.

Tokens are stored per server host in the OS keychain. If the keychain is
unavailable, Graphia falls back to a `0600` credentials file. Set
`GRAPHIA_NO_KEYRING=1` to force the file, and `GRAPHIA_TOKEN` to use a session
token from another source.

## Configuration

Resolution order:

1. `--server`
2. `GRAPHIA_SERVER`
3. the saved config file (`graphia doctor` prints its path)
4. the deployed API (`https://elysiaa-graphia-api-1023333674013.asia-southeast1.run.app`)

For local development use `--server http://localhost:3000` or set
`GRAPHIA_SERVER=http://localhost:3000`. `graphia login` saves the server after a
successful approval. `GRAPHIA_CONFIG_DIR` overrides the config directory.

## Notes

- The CLI uploads directly to R2 using the presigned URL from the API, so file
  bytes never pass through the API, exactly like the browser.
- Presigned URLs and tokens are never printed. `--verbose` shows request paths
  only, with storage URLs redacted.
- The server keeps results for 24 hours; download the batch when it finishes.
