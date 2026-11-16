import type { Metadata } from "next";
import Link from "next/link";
import { Drop, Ticket, Waves } from "@phosphor-icons/react/dist/ssr";

export const metadata: Metadata = {
  title: "Create account — Graphia",
  description: "Create a Graphia account through Zitadel.",
};

export default function SignupPage() {
  return (
    <main className="auth-layout">
      <aside className="auth-copy">
        <Link className="brand" href="/">
          <span className="brand-badge">G</span>
          <span className="brand-lockup">
            <span className="brand-name">Graphia</span>
            <span className="brand-tag">Document arcade</span>
          </span>
        </Link>

        <p className="panel-label">New membership</p>
        <h1 className="auth-display">
          Get in
          <br />
          Get a pass
        </h1>
        <p className="lede">
          Accounts are created and secured by Elysiaa SSO. Graphia keeps a local identity
          record and a server session. There is no Graphia password.
        </p>

        <div className="pass-stub" aria-hidden="true">
          <span className="pass-stub__stripe" />
          <span className="pass-stub__label">
            <Ticket size={20} weight="bold" />
            New pool pass
          </span>
          <span className="pass-stub__big">ADMIT ONE</span>
          <span className="pass-stub__meta">25 MB / file · 24 hour locker</span>
          <Waves className="pass-stub__wave" size={56} weight="bold" />
        </div>
      </aside>

      <div className="auth-card">
        <div className="auth-card-head">
          <div>
            <p className="panel-label">Join the arcade</p>
            <h2 className="panel-title">Claim a pass.</h2>
          </div>
          <Drop className="auth-glyph" size={40} weight="bold" aria-hidden="true" />
        </div>

        <p className="auth-copyline">
          Zitadel opens its registration page. If registration is invite only, ask the owner
          for an invitation first.
        </p>

        <form action="/api/auth/signup" method="get" className="form">
          <input type="hidden" name="next" value="/convert" />
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
            <small className="field-hint">Zitadel uses this to prefill registration.</small>
          </label>
          <button className="btn btn-primary btn-wide" type="submit">
            Create account with Zitadel
          </button>
        </form>

        <p className="auth-switch">
          Already have a pass? <Link href="/login">Sign in</Link>
        </p>
        <p className="auth-legal">
          <Link href="/privacy">Privacy</Link>
          <span aria-hidden="true"> / </span>
          <Link href="/terms">Terms</Link>
        </p>
      </div>
    </main>
  );
}
