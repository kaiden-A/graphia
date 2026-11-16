import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms — Graphia",
  description: "The small print for using the Graphia document arcade.",
};

export default function TermsPage() {
  return (
    <main className="legal-page">
      <Link className="back-link" href="/">
        ← Back to the arcade
      </Link>
      <article className="legal-card">
        <p className="panel-label">Graphia / terms</p>
        <h1>Terms</h1>
        <p>
          Graphia is a small personal document conversion service. Use it only for files you
          have the right to upload and convert.
        </p>
        <h2>Availability</h2>
        <p>
          Jobs are processed asynchronously. A run can fail because of an unsupported file,
          a password protected document, or a processor fault. The ticket keeps the reason
          when a run fails.
        </p>
        <h2>Retention</h2>
        <p>
          Inputs and outputs are temporary. The locker period is shown on the ticket. Eject a
          job if you want its stored objects removed sooner.
        </p>
        <h2>No warranty</h2>
        <p>
          The service is provided as is, without a warranty that a converted file will match
          the original layout exactly. Keep your source file.
        </p>
      </article>
    </main>
  );
}
