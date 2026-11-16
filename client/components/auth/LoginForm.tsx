"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { apiJson, messageForError } from "@/lib/api-client";
import type { User } from "@/lib/types";

function safeNext(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/";
  return value;
}

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiJson<User>(
        "/api/auth/login",
        { method: "POST", body: JSON.stringify({ email, password }) },
        { redirectOn401: false },
      );
      router.replace(safeNext(searchParams.get("next")));
      router.refresh();
    } catch (caught) {
      setError(messageForError(caught));
      setSubmitting(false);
    }
  }

  return (
    <section className="auth-layout">
      <aside className="auth-copy">
        <Link className="brand" href="/">
          <span className="brand-mark">G</span>
          <span className="brand-word">Graphia</span>
        </Link>
        <p className="eyebrow">Private desk</p>
        <h1 className="auth-display">
          Your documents,
          <br />
          not a public drop box.
        </h1>
        <p className="lede">
          Sign in to queue conversions, follow the job ticket, and collect the result. The
          processor does the heavy lifting in the background.
        </p>
        <div className="auth-note">
          <span className="mono">DOCX → PDF</span>
          <span className="mono">PDF → MD</span>
          <span className="mono">IMG → PDF</span>
        </div>
      </aside>

      <div className="auth-card card">
        <div className="card-head">
          <div>
            <p className="eyebrow">Sign in</p>
            <h2 className="card-title">Back to the desk.</h2>
          </div>
          <span className="card-index mono">A1</span>
        </div>

        <form className="form" onSubmit={submit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error ? (
            <p className="error-banner" role="alert">
              {error}
            </p>
          ) : null}

          <button className="btn btn-primary btn-wide" type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="auth-switch">
          No account yet? <Link href="/signup">Create one</Link>
        </p>
      </div>
    </section>
  );
}
