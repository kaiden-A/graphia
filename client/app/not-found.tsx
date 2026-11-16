import Link from "next/link";

import { TempleIcon } from "@/components/scrapbook/icons";

export default function NotFound() {
  return (
    <main className="site-shell">
      <div className="folio">
        <div className="page">
          <section className="center-card">
            <TempleIcon className="gate-icon" />
            <p className="eyebrow">404 — off the map</p>
            <h1 className="card-title">This route is not on the map.</h1>
            <p className="muted">
              The address does not point at anything in Graphia.
            </p>
            <Link className="btn btn-primary" href="/">
              Back to the desk
            </Link>
          </section>
        </div>
      </div>
    </main>
  );
}
