# Authentication — Zitadel OIDC

Graphia uses Zitadel as its only identity provider. There are no Graphia
passwords and no password login endpoints.

## Model

- Browser → `GET /api/auth/login` on the Next origin.
- Service A creates a PKCE verifier, state, and nonce.
- Service A sets a signed, HttpOnly `graphia_oauth` cookie (10 minutes).
- Browser is redirected to Zitadel’s hosted login.
- Zitadel redirects to `/api/auth/callback?code=...&state=...`.
- Service A verifies state, exchanges the code server-side, verifies the ID token
  with JWKS, and provisions/updates the local user.
- Service A creates a server-side session row and sets `graphia_session`.
- Browser is redirected to the safe `next` path.

Logout revokes the local session, clears both cookies, and returns a Zitadel
`end_session` URL. The client navigates there so the Zitadel session is also
ended.

## Zitadel configuration

Create a **Web** application:

- Authentication method: **Authorization Code + PKCE**
- Client secret: none
- Scopes: `openid profile email`

Register exactly:

```text
http://localhost:3000/api/auth/callback
http://localhost:3000/login
```

Production:

```text
https://<client-domain>/api/auth/callback
https://<client-domain>/login
```

The redirect URI is on the **client origin**, because Next rewrites `/api/*` to
FastAPI. It is not the Cloud Run API URL.

## Environment

```dotenv
APP_SECRET=<long-random-value>
ZITADEL_ISSUER=https://<instance>.zitadel.cloud
ZITADEL_CLIENT_ID=<public-client-id>
ZITADEL_REDIRECT_URI=http://localhost:3000/api/auth/callback
ZITADEL_POST_LOGOUT_URI=http://localhost:3000/login
PUBLIC_BASE_URL=http://localhost:3000

SESSION_COOKIE_NAME=graphia_session
SESSION_TTL_DAYS=30
COOKIE_SECURE=false
GUEST_SESSION_TTL_HOURS=24
GUEST_SESSIONS_PER_HOUR_PER_IP=10
```

`APP_SECRET` signs the OAuth handshake cookie. It must be stable across API
instances. `ZITADEL_CLIENT_ID` is public; there is no client secret.

## User provisioning

The local `users` table is a projection of the Zitadel identity:

- `idp_issuer` — normalized Zitadel issuer
- `zitadel_sub` — ID token `sub`
- unique `(idp_issuer, zitadel_sub)`

On first login:

1. Match by `(issuer, sub)`.
2. Otherwise match an existing local user by lowercased email and adopt it.
3. Otherwise create a new user.

Existing conversion jobs stay attached to the adopted user row. If an email is
already linked to a different Zitadel subject, sign-in is rejected rather than
silently reassigning ownership.

## Guest access

A visitor can convert without an account:

- `POST /api/auth/guest` creates a disposable local user with `is_guest=true`.
  The user has a generated `@guest.graphia.local` email, no Zitadel subject, no
  password, and a 24 hour session.
- Guests can create, read, complete, and delete their own jobs. The download
  endpoint uses `require_member` and returns `403` for a guest session.
- The guest form is rate limited by IP. The endpoint checks the `Origin` header
  when a browser sends one, so another site cannot silently mint sessions.
- When a guest completes a Zitadel login, jobs owned by the guest session are
  reassigned to the member account and the guest user plus its sessions are
  deleted. R2 keys keep the guest prefix from upload time; the job row stores the
  full keys, so downloads follow the row.
- Guest sessions expire with the locker. `scripts/cleanup_expired.py` removes
  unclaimed guest users that have no jobs left.

## CLI access

The CLI is member-only and does not use a second OIDC application. It reuses the
existing Web application through a browser approval handoff:

1. `graphia login` creates a 10-minute request with a random code and a
   SHA-256 challenge of a verifier that stays in the CLI.
2. The CLI opens `GET /cli?code=...` on the client origin. The page sends an
   unauthenticated visitor through the normal Zitadel login and back to `/cli`.
3. A signed-in member clicks **Approve**. `POST /api/cli/requests/{code}/approve`
   binds the request to that user. Guests cannot approve.
4. The CLI polls `POST /api/cli/token` with the code and verifier. A successful
   exchange creates a normal `sessions` row with `client=cli` and the device name
   as `label`, then returns the raw token once.
5. API calls send `Authorization: Bearer <token>`. `require_auth` accepts the
   browser cookie or a bearer token; a bearer token belonging to a guest is
   rejected with `403`.

Only the code hash, challenge, and session token hash are stored. Codes are
single-use and expire after 10 minutes. `graphia logout` calls
`POST /api/cli/logout` with the bearer token and revokes the session.

## Security checks

- PKCE S256; verifier stays in the signed HttpOnly handshake cookie.
- State compared with `hmac.compare_digest`.
- ID token signature checked against Zitadel JWKS.
- Exact issuer and audience (`client_id`).
- `exp`, `iat`, `sub`, `aud`, `iss`, and `nonce` required.
- 60-second clock skew.
- Email required.
- `email_verified=false` rejected.
- No Zitadel tokens are stored in the browser or database; only the local
  session token hash is stored.
- CLI approval codes and verifiers are stored only as hashes. Requests are
  single-use, expire after `CLI_AUTH_REQUEST_TTL_MINUTES`, and the token
  exchange is claimed atomically.
- `next` accepts only local paths.
- Guest creation checks `Origin` when present and is rate limited per IP.
- Guest downloads are blocked at the API, not only hidden in the client.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/auth/login` | Start login. Supports `next`, `login_hint`, `prompt`. |
| `GET /api/auth/signup` | Start login with `prompt=create`. |
| `POST /api/auth/guest` | Create a guest session and redirect to `next`. |
| `GET /api/auth/callback` | OIDC callback. |
| `GET /api/auth/me` | Current local user, including `isGuest`. |
| `POST /api/auth/logout` | Revoke local session; returns `{ logoutUrl }`. |
| `GET /api/config` | Public CLI bootstrap: version, web URL, limits. |
| `POST /api/cli/requests` | Create a hashed, 10-minute CLI approval request. |
| `GET /api/cli/requests/{code}` | Request name and status for the approval page. |
| `POST /api/cli/requests/{code}/approve` | Bind a request to a member cookie session. |
| `POST /api/cli/requests/{code}/deny` | Deny a request before it is claimed. |
| `POST /api/cli/token` | Exchange code + verifier for a CLI session token. |
| `POST /api/cli/logout` | Revoke the bearer session. |

## Troubleshooting

- **Redirect loop:** `SESSION_COOKIE_NAME` must match between server and client.
- **Zitadel “redirect URI mismatch”:** the URI in Zitadel must match
  `ZITADEL_REDIRECT_URI` byte-for-byte, including port. If Next runs on 3001
  because 3000 is busy, register 3001 or free 3000.
- **Login works, `/me` returns 401:** check `COOKIE_SECURE` (must be false on
  local HTTP, true on HTTPS) and that the callback is on the client origin.
- **Logout leaves the user signed in:** the browser must navigate to the returned
  `logoutUrl`, not just clear the local cookie.
- **Email rejected:** ensure the Zitadel user has an email claim and it is
  verified.
- **Existing jobs disappeared:** the Zitadel email differs from the local user’s
  email; the app created a new user. Link the old row or update its email.
- **`APP_SECRET` changed:** in-flight sign-ins fail with a state-cookie error;
  existing sessions remain valid.
- **Guest download returns 403:** expected. Sign in or create an account; the
  guest run is claimed by that account during the callback.
- **CLI approval returns 403:** the page session is a guest, or the browser
  `Origin` does not match `PUBLIC_BASE_URL`. Sign in with a member account and
  open the link on the same origin.
- **CLI says `Not signed in` after login:** the token is stored per host. Check
  the resolved server with `graphia doctor`; `localhost:3000` and a production
  host keep separate sessions.
- **CLI request expired:** approval links last 10 minutes. Run `graphia login`
  again.
