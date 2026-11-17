import type { Metadata } from "next";
import Link from "next/link";

import Logo from "@/components/brand/Logo";
import { safeNextPath } from "@/lib/next-path";

export const metadata: Metadata = {
  title: "Create account — Graphia",
  description: "Create a Graphia account through Zitadel.",
};

const FACTS = [
  { label: "Account", value: "Zitadel SSO" },
  { label: "Password", value: "Never stored" },
  { label: "Max file", value: "25 MB" },
  { label: "Locker", value: "24 hours" },
];

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const params = await searchParams;
  const next = safeNextPath(typeof params.next === "string" ? params.next : undefined);

  return (
    <main className="auth-page">
      <aside className="auth-aside on-dark">
        <Link className="brand-link" href="/" aria-label="Graphia home">
          <Logo tone="light" />
        </Link>

        <div className="auth-aside-copy">
          <p className="eyebrow caption-3">New account</p>
          <h1 className="auth-display heading-2">Open an account.</h1>
          <p className="body-5">
            Accounts are created and secured by Elysiaa SSO. Graphia keeps a local identity
            record and a server session. There is no Graphia password.
          </p>
        </div>

        <ul className="fact-list">
          {FACTS.map((fact) => (
            <li key={fact.label}>
              <span className="caption-4">{fact.label}</span>
              <span className="title-3">{fact.value}</span>
            </li>
          ))}
        </ul>

        <p className="auth-aside-foot caption-5">Graphia / Document atelier</p>
      </aside>

      <div className="auth-main">
        <div className="auth-card">
          <p className="eyebrow caption-3">Create account</p>
          <h2 className="heading-4">Claim your account.</h2>
          <p className="auth-copyline body-5">
            Zitadel opens its registration page. If registration is invite only, ask the
            owner for an invitation first.
          </p>

          <form action="/api/auth/signup" method="get" className="form">
            <input type="hidden" name="next" value={next} />
            <label className="field">
              <span className="caption-1">
                Email <em>optional</em>
              </span>
              <input
                name="login_hint"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
              />
              <small className="field-hint caption-5">
                Zitadel uses this to prefill registration.
              </small>
            </label>
            <button className="btn btn-primary btn-large btn-wide" type="submit">
              Create account with Zitadel
            </button>
          </form>

          <div className="auth-divider">
            <span />
            <em className="caption-5">or</em>
            <span />
          </div>

          <form
            action={`/api/auth/guest?next=${encodeURIComponent(next)}`}
            method="post"
          >
            <button className="btn btn-ghost btn-wide" type="submit">
              Continue as guest
            </button>
          </form>
          <p className="auth-guest-note caption-5">
            Convert without an account. Sign in or create one when you are ready to download.
          </p>

          <p className="auth-switch caption-5">
            Already have an account? <Link href={`/login?next=${encodeURIComponent(next)}`}>Sign in</Link>
          </p>
          <p className="auth-legal caption-5">
            <Link href="/privacy">Privacy</Link>
            <span aria-hidden="true"> / </span>
            <Link href="/terms">Terms</Link>
          </p>
        </div>
      </div>
    </main>
  );
}
