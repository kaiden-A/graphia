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
