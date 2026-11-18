import type { Metadata } from "next";
import Link from "next/link";

import CliApproval from "@/components/auth/CliApproval";
import Logo from "@/components/brand/Logo";

export const metadata: Metadata = {
  title: "Approve CLI — Graphia",
  description: "Approve a Graphia terminal sign-in request.",
  robots: { index: false, follow: false },
};

const FACTS = [
  { label: "Access", value: "Member session" },
  { label: "Window", value: "10 minutes" },
  { label: "Approval", value: "One request" },
  { label: "Revoke", value: "graphia logout" },
];

export default async function CliPage({
  searchParams,
}: {
  searchParams: Promise<{ code?: string }>;
}) {
  const params = await searchParams;
  const code = typeof params.code === "string" ? params.code : "";

  return (
    <main className="auth-page">
      <aside className="auth-aside on-dark">
        <Link className="brand-link" href="/" aria-label="Graphia home">
          <Logo tone="light" />
        </Link>

        <div className="auth-aside-copy">
          <p className="eyebrow caption-3">Terminal access</p>
          <h1 className="auth-display heading-2">Approve the press.</h1>
          <p className="body-5">
            The Graphia CLI signs in through this page. No password is typed in the
            terminal, and no token is shown in the browser.
          </p>
        </div>

        <ul className="fact-list">
          {FACTS.map((fact) => (
            <li key={fact.label}>
              <span className="caption-4">{fact.label}</span>
              <span className="title-3">{fact.value}</span>
            </li>
          ))}
        </ul>

        <p className="auth-aside-foot caption-5">Graphia / Document atelier</p>
      </aside>

      <div className="auth-main">
        <CliApproval code={code} />
      </div>
    </main>
  );
}
