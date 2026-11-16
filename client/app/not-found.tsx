import Link from "next/link";

export default function NotFound() {
  return (
    <main className="page">
      <section className="center-card card">
        <p className="eyebrow">404</p>
        <h1 className="card-title">This page missed the filing tray.</h1>
        <p className="muted">The address does not point at anything in Graphia.</p>
        <Link className="btn btn-primary" href="/">
          Back to the desk
        </Link>
      </section>
    </main>
  );
}
