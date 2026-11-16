import type { Metadata } from "next";
import Link from "next/link";

import Logo from "@/components/brand/Logo";

export const metadata: Metadata = {
  title: "Sign in — Graphia",
  description: "Sign in to Graphia with your Zitadel account.",
};

function safeNext(value: string | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/convert";
  return value;
}

const FACTS = [
  { label: "Identity", value: "Zitadel SSO" },
  { label: "Session", value: "Server side token" },
  { label: "Storage", value: "Private bucket" },
  { label: "Locker", value: "24 hours" },
];

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const params = await searchParams;
  const next = safeNext(typeof params.next === "string" ? params.next : undefined);
  const error = typeof params.error === "string" ? params.error : null;

  return (
    <main className="auth-page">
      <aside className="auth-aside on-dark">
        <Link className="brand-link" href="/" aria-label="Graphia home">
          <Logo tone="light" />
        </Link>

        <div className="auth-aside-copy">
          <p className="eyebrow caption-3">Membership</p>
          <h1 className="auth-display heading-2">Sign in to the press.</h1>
          <p className="body-5">
            Elysiaa SSO handles the password. Graphia keeps a session and a job record, and
            nothing more.
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
          <p className="eyebrow caption-3">Sign in</p>
          <h2 className="heading-4">Pick up where you left off.</h2>

          {error ? (
            <p className="alert" role="alert">
              {error}
            </p>
          ) : null}

          <form action="/api/auth/login" method="get" className="form">
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
                We pass this to Zitadel to prefill the login.
              </small>
            </label>
            <button className="btn btn-primary btn-large btn-wide" type="submit">
              Continue to Elysiaa SSO
            </button>
          </form>

          <div className="auth-divider">
            <span />
            <em className="caption-5">or</em>
            <span />
          </div>

          <a
            className="btn btn-ghost btn-wide"
            href={`/api/auth/login?next=${encodeURIComponent(next)}`}
          >
            Continue without an email hint
          </a>

          <p className="auth-switch caption-5">
            No account yet? <Link href="/signup">Create one</Link>
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
