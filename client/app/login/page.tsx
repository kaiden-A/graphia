import type { Metadata } from "next";
import Link from "next/link";
import { Drop, Ticket, Waves } from "@phosphor-icons/react/dist/ssr";

export const metadata: Metadata = {
  title: "Sign in — Graphia",
  description: "Sign in to the Graphia document arcade with your Zitadel account.",
};

function safeNext(value: string | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/convert";
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
          <span className="brand-badge">G</span>
          <span className="brand-lockup">
            <span className="brand-name">Graphia</span>
            <span className="brand-tag">Document arcade</span>
          </span>
        </Link>

        <p className="panel-label">Front desk</p>
        <h1 className="auth-display">
          Your files
          <br />
          Your lane
        </h1>
        <p className="lede">
          Sign in through Elysiaa SSO to open the control deck, start a run, and collect the
          result. Graphia never sees your password.
        </p>

        <div className="pass-stub" aria-hidden="true">
          <span className="pass-stub__stripe" />
          <span className="pass-stub__label">
            <Ticket size={20} weight="bold" />
            Pool pass
          </span>
          <span className="pass-stub__big">ADMIT ONE</span>
          <span className="pass-stub__meta">Zitadel SSO / server sessions</span>
          <Waves className="pass-stub__wave" size={56} weight="bold" />
        </div>
      </aside>

      <div className="auth-card">
        <div className="auth-card-head">
          <div>
            <p className="panel-label">Membership</p>
            <h2 className="panel-title">Pick up your pool pass.</h2>
          </div>
          <Drop className="auth-glyph" size={40} weight="bold" aria-hidden="true" />
        </div>

        {error ? (
          <p className="alert" role="alert">
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
            <small className="field-hint">We pass this to Zitadel to prefill the login.</small>
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
          No pass yet? <Link href="/signup">Make one</Link>
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
