import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy — Graphia",
  description: "How Graphia handles account data, uploaded files, and conversion results.",
};

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <div className="legal-inner">
        <Link className="back-link caption-1" href="/">
          ← Back to Graphia
        </Link>

        <article className="legal-card">
          <p className="eyebrow caption-3">Graphia / Privacy</p>
          <h1 className="heading-2">Privacy</h1>
          <p className="body-2">
            Graphia stores the email and display name from your Zitadel account or a
            disposable guest identity, a server session, and a job record for each
            conversion.
          </p>

          <h2 className="heading-5">Files</h2>
          <p className="body-3">
            Uploaded files and converted results live in private object storage. They are
            reachable only through signed links issued to the account that created the job,
            and those links are short lived. Files expire after the locker period shown on
            the run ticket.
          </p>

          <h2 className="heading-5">Authentication</h2>
          <p className="body-3">
            Sign in and account creation are handled by Elysiaa SSO through Zitadel. Graphia
            does not receive or store your password. A guest session is a disposable local
            identity with no email, password, or external account attached.
          </p>

          <h2 className="heading-5">Guest runs</h2>
          <p className="body-3">
            Guest sessions expire with the locker. If a guest signs in, the runs from that
            session move to the signed-in account so the ticket and its download can be
            collected. Guest identities that are never claimed are removed in cleanup.
          </p>

          <h2 className="heading-5">Deletion</h2>
          <p className="body-3">
            You can delete a run from its ticket to remove the stored input and output.
            Account deletion is handled by the Graphia owner.
          </p>
        </article>

        <p className="legal-foot caption-5">
          <span>Graphia / Document atelier</span>
          <span>
            <Link href="/terms">Terms</Link>
            <span aria-hidden="true"> / </span>
            <Link href="/">Home</Link>
          </span>
        </p>
      </div>
    </main>
  );
}
