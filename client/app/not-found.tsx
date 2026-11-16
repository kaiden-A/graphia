import Link from "next/link";

import Logo from "@/components/brand/Logo";

export default function NotFound() {
  return (
    <main className="auth-page">
      <aside className="auth-aside on-dark">
        <Link className="brand-link" href="/" aria-label="Graphia home">
          <Logo tone="light" />
        </Link>

        <div className="auth-aside-copy">
          <p className="eyebrow caption-3">Error 404</p>
          <h1 className="auth-display heading-2">This page left the press.</h1>
          <p className="body-5">
            The address does not point at anything Graphia knows about.
          </p>
        </div>

        <ul className="fact-list">
          <li>
            <span className="caption-4">Try</span>
            <span className="title-3">The converter</span>
          </li>
          <li>
            <span className="caption-4">Or</span>
            <span className="title-3">The landing page</span>
          </li>
        </ul>

        <p className="auth-aside-foot caption-5">Graphia / Document atelier</p>
      </aside>

      <div className="auth-main">
        <div className="auth-card">
          <p className="eyebrow caption-3">Nothing here</p>
          <h2 className="heading-4">Check the address.</h2>
          <p className="auth-copyline body-5">
            The page may have moved, or the link may be incomplete. Both ways back are
            below.
          </p>
          <Link className="btn btn-primary btn-large btn-wide" href="/convert">
            Open the converter
          </Link>
          <Link className="btn btn-ghost btn-wide" href="/">
            Back to the landing page
          </Link>
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
