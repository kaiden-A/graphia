import type { Metadata } from "next";
import Link from "next/link";

import { TempleIcon } from "@/components/scrapbook/icons";
import { TapeStrip } from "@/components/scrapbook/Ornaments";

export const metadata: Metadata = {
  title: "Create account — Graphia",
  description: "Create a Graphia account through Zitadel.",
};

export default function SignupPage() {
  return (
    <main className="auth-layout">
      <aside className="auth-copy">
        <Link className="brand" href="/">
          <span className="brand-mark">G</span>
          <span className="brand-word">Graphia</span>
        </Link>
        <p className="eyebrow">New account</p>
        <h1 className="auth-display">
          A small desk
          <br />
          for heavy files.
        </h1>
        <p className="lede">
          Accounts are created and secured by Elysiaa SSO. Graphia keeps only a local
          identity projection and a server-side session; there is no Graphia password.
        </p>
        <TempleIcon className="gate-icon" />
        <div className="auth-note">
          <span>25 MB / file</span>
          <span>Async jobs</span>
          <span>Private R2</span>
        </div>
      </aside>

      <div className="auth-card card">
        <TapeStrip className="auth-tape" rotate={-4} />
        <div className="card-head">
          <div>
            <p className="eyebrow">Create account</p>
            <h2 className="card-title">Claim a seat.</h2>
          </div>
          <span className="card-index mono">A2</span>
        </div>

        <p className="muted signup-copy">
          Zitadel will open its registration page. If registration is invite-only, ask the
          owner for an invitation first.
        </p>

        <form action="/api/auth/signup" method="get" className="form">
          <input type="hidden" name="next" value="/" />
          <label className="field">
            <span>
              Email <em>optional</em>
            </span>
            <input
              name="login_hint"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
            />
            <small className="field-hint">
              Zitadel uses this to prefill the registration form.
            </small>
          </label>
          <button className="btn btn-primary btn-wide" type="submit">
            Create account with Zitadel
          </button>
        </form>

        <p className="auth-switch">
          Already have a seat? <Link href="/login">Sign in</Link>
        </p>
      </div>
    </main>
  );
}
