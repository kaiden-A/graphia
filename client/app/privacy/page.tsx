import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy — Graphia",
  description: "How Graphia handles account data, uploaded files, and conversion results.",
};

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <Link className="back-link" href="/">
        ← Back to the arcade
      </Link>
      <article className="legal-card">
        <p className="panel-label">Graphia / privacy</p>
        <h1>Privacy</h1>
        <p>
          Graphia stores the email and display name from your Zitadel account, a server
          session, and a job record for each conversion.
        </p>
        <h2>Files</h2>
        <p>
          Uploaded files and converted results live in private object storage. They are
          reachable only through short lived signed links issued to the account that created
          the job. Files expire after the locker period shown on the job ticket.
        </p>
        <h2>Authentication</h2>
        <p>
          Sign in and account creation are handled by Elysiaa SSO through Zitadel. Graphia
          does not receive or store your password.
        </p>
        <h2>Deletion</h2>
        <p>
          You can eject a job from its ticket to remove its stored input and output. Account
          deletion is handled by the Graphia owner.
        </p>
      </article>
    </main>
  );
}
