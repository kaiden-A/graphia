import Link from "next/link";
import { Drop } from "@phosphor-icons/react/dist/ssr";

export default function NotFound() {
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
        <p className="panel-label">Error 404</p>
        <h1 className="auth-display">
          This lane
          <br />
          is empty
        </h1>
        <p className="lede">The address does not point at anything on the floor.</p>
      </aside>

      <div className="auth-card">
        <div className="auth-card-head">
          <div>
            <p className="panel-label">Out of bounds</p>
            <h2 className="panel-title">Back to the control deck.</h2>
          </div>
          <Drop className="auth-glyph" size={40} weight="bold" aria-hidden="true" />
        </div>
        <p className="auth-copyline">
          Check the address, or head back and start a new run.
        </p>
        <Link className="btn btn-primary btn-wide" href="/">
          Back to the arcade
        </Link>
      </div>
    </main>
  );
}
