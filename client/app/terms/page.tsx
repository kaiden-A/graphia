import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms — Graphia",
  description: "The small print for using the Graphia document converter.",
};

export default function TermsPage() {
  return (
    <main className="legal-page">
      <div className="legal-inner">
        <Link className="back-link caption-1" href="/">
          ← Back to Graphia
        </Link>

        <article className="legal-card">
          <p className="eyebrow caption-3">Graphia / Terms</p>
          <h1 className="heading-2">Terms</h1>
          <p className="body-2">
            Graphia is a small personal document conversion service. Use it only for files
            you have the right to upload and convert.
          </p>

          <h2 className="heading-5">Availability</h2>
          <p className="body-3">
            Jobs are processed asynchronously. A run can fail because of an unsupported
            file, a password protected document, or a processor fault. The ticket keeps the
            reason when a run fails.
          </p>

          <h2 className="heading-5">Retention</h2>
          <p className="body-3">
            Inputs and outputs are temporary. The locker period is shown on the ticket.
            Delete a run if you want its stored objects removed sooner.
          </p>

          <h2 className="heading-5">No warranty</h2>
          <p className="body-3">
            The service is provided as is, without a warranty that a converted file will
            match the original layout exactly. Keep your source file.
          </p>
        </article>

        <p className="legal-foot caption-5">
          <span>Graphia / Document atelier</span>
          <span>
            <Link href="/privacy">Privacy</Link>
            <span aria-hidden="true"> / </span>
            <Link href="/">Home</Link>
          </span>
        </p>
      </div>
    </main>
  );
}
