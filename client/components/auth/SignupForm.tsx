"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiJson, messageForError } from "@/lib/api-client";
import type { AuthConfig, User } from "@/lib/types";

export default function SignupForm() {
  const router = useRouter();
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiJson<AuthConfig>("/api/auth/config")
      .then(setConfig)
      .catch((caught) => setError(messageForError(caught)));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiJson<User>(
        "/api/auth/signup",
        {
          method: "POST",
          body: JSON.stringify({
            name: name.trim() || null,
            email,
            password,
            inviteCode: inviteCode.trim() || null,
          }),
        },
        { redirectOn401: false },
      );
      router.replace("/");
      router.refresh();
    } catch (caught) {
      setError(messageForError(caught));
      setSubmitting(false);
    }
  }

  if (config && !config.signupEnabled) {
    return (
      <section className="auth-layout">
        <aside className="auth-copy">
          <Link className="brand" href="/">
            <span className="brand-mark">G</span>
            <span className="brand-word">Graphia</span>
          </Link>
          <p className="eyebrow">Private desk</p>
          <h1 className="auth-display">Registration is closed.</h1>
          <p className="lede">
            This Graphia desk is invite-only right now. If you already have an account, sign in.
          </p>
          <Link className="btn btn-primary" href="/login">
            Go to sign in
          </Link>
        </aside>
        <div className="auth-card card">
          <p className="eyebrow">Access</p>
          <h2 className="card-title">Ask the owner for an account.</h2>
          <p className="muted">
            The owner can enable signup or create a user with the server script.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="auth-layout">
      <aside className="auth-copy">
        <Link className="brand" href="/">
          <span className="brand-mark">G</span>
          <span className="brand-word">Graphia</span>
        </Link>
        <p className="eyebrow">New account</p>
        <h1 className="auth-display">
          A small desk
          <br />
          for heavy files.
        </h1>
        <p className="lede">
          Graphia converts one document at a time, keeps a ticket for each job, and deletes
          stored files when they expire.
        </p>
        <div className="auth-note">
          <span className="mono">25 MB / FILE</span>
          <span className="mono">ASYNC JOBS</span>
          <span className="mono">PRIVATE R2</span>
        </div>
      </aside>

      <div className="auth-card card">
        <div className="card-head">
          <div>
            <p className="eyebrow">Create account</p>
            <h2 className="card-title">Claim a seat.</h2>
          </div>
          <span className="card-index mono">A2</span>
        </div>

        <form className="form" onSubmit={submit}>
          <label className="field">
            <span>Name <em>optional</em></span>
            <input
              type="text"
              autoComplete="name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={120}
            />
          </label>
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
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              maxLength={128}
              required
            />
            <small className="field-hint">At least 8 characters.</small>
          </label>
          {config?.signupRequiresCode ? (
            <label className="field">
              <span>Invite code</span>
              <input
                type="text"
                value={inviteCode}
                onChange={(event) => setInviteCode(event.target.value)}
                required
              />
            </label>
          ) : null}

          {error ? (
            <p className="error-banner" role="alert">
              {error}
            </p>
          ) : null}

          <button className="btn btn-primary btn-wide" type="submit" disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="auth-switch">
          Already have a seat? <Link href="/login">Sign in</Link>
        </p>
      </div>
    </section>
  );
}
