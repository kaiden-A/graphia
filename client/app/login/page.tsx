import type { Metadata } from "next";
import Link from "next/link";

import { TempleIcon } from "@/components/scrapbook/icons";
import { TapeStrip } from "@/components/scrapbook/Ornaments";

export const metadata: Metadata = {
  title: "Sign in — Graphia",
  description: "Sign in to Graphia with your Zitadel account.",
};

function safeNext(value: string | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/";
  return value;
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const params = await searchParams;
  const next = safeNext(typeof params.next === "string" ? params.next : undefined);
  const error = typeof params.error === "string" ? params.error : null;

  return (
    <main className="auth-layout">
      <aside className="auth-copy">
        <Link className="brand" href="/">
          <span className="brand-mark">G</span>
          <span className="brand-word">Graphia</span>
        </Link>
        <p className="eyebrow">Private desk</p>
        <h1 className="auth-display">
          Your documents,
          <br />
          not a public drop box.
        </h1>
        <p className="lede">
          Sign in through Elysiaa SSO to send a document on its way, follow the ticket, and
          collect the result. Graphia never sees your password.
        </p>
        <TempleIcon className="gate-icon" />
        <div className="auth-note">
          <span>Zitadel SSO</span>
          <span>Server sessions</span>
          <span>Private R2</span>
        </div>
      </aside>

      <div className="auth-card card">
        <TapeStrip className="auth-tape" rotate={-4} />
        <div className="card-head">
          <div>
            <p className="eyebrow">Sign in</p>
            <h2 className="card-title">Back to the desk.</h2>
          </div>
          <span className="card-index mono">A1</span>
        </div>

        {error ? (
          <p className="error-banner" role="alert">
            {error}
          </p>
        ) : null}

        <form action="/api/auth/login" method="get" className="form">
          <input type="hidden" name="next" value={next} />
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
              We pass this to Zitadel so its hosted login is prefilled.
            </small>
          </label>
          <button className="btn btn-primary btn-wide" type="submit">
            Continue to Elysiaa SSO
          </button>
        </form>

        <div className="auth-divider">
          <span />
          <em>or</em>
          <span />
        </div>

        <a
          className="btn btn-ghost btn-wide"
          href={`/api/auth/login?next=${encodeURIComponent(next)}`}
        >
          Continue without an email hint
        </a>

        <p className="auth-switch">
          No account yet? <Link href="/signup">Create one</Link>
        </p>
      </div>
    </main>
  );
}
