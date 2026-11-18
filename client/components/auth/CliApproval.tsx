"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, apiJson, messageForError } from "@/lib/api-client";
import type { User } from "@/lib/types";

type CliStatus = "pending" | "approved" | "denied" | "claimed" | "expired";

interface CliRequest {
  name: string;
  status: CliStatus;
  expiresAt: number;
}

interface Props {
  code: string;
}

function shortCode(code: string): string {
  if (code.length < 8) return code;
  return `${code.slice(0, 4)}-${code.slice(4, 8)}`;
}

function expiryLabel(ms: number): string {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function CliApproval({ code }: Props) {
  const [user, setUser] = useState<User | null>(null);
  const [request, setRequest] = useState<CliRequest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CliStatus | null>(null);

  const nextPath = `/cli?code=${encodeURIComponent(code)}`;

  const load = useCallback(async () => {
    if (!code) {
      setError("This link is incomplete. Run `graphia login` again.");
      return;
    }

    try {
      const me = await apiJson<User>("/api/auth/me", {}, { redirectOn401: false });
      setUser(me);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        window.location.assign(`/login?next=${encodeURIComponent(nextPath)}`);
        return;
      }
      setError(messageForError(caught));
      return;
    }

    try {
      const current = await apiJson<CliRequest>(
        `/api/cli/requests/${encodeURIComponent(code)}`,
        {},
        { redirectOn401: false },
      );
      setRequest(current);
      if (current.status !== "pending") {
        setResult(current.status);
      }
    } catch (caught) {
      setError(messageForError(caught));
    }
  }, [code, nextPath]);

  useEffect(() => {
    void load();
  }, [load]);

  async function decide(action: "approve" | "deny") {
    setBusy(true);
    setError(null);
    try {
      const updated = await apiJson<CliRequest>(
        `/api/cli/requests/${encodeURIComponent(code)}/${action}`,
        { method: "POST" },
        { redirectOn401: false },
      );
      setResult(updated.status);
    } catch (caught) {
      setError(messageForError(caught));
      if (caught instanceof ApiError && caught.status === 401) {
        window.location.assign(`/login?next=${encodeURIComponent(nextPath)}`);
      }
    } finally {
      setBusy(false);
    }
  }

  if (error && !request) {
    return (
      <div className="auth-card">
        <p className="eyebrow caption-3">CLI sign-in</p>
        <h2 className="heading-4">This request cannot continue.</h2>
        <p className="alert" role="alert">
          {error}
        </p>
        <p className="auth-copyline body-5">
          Run <code>graphia login</code> again to start a fresh request.
        </p>
      </div>
    );
  }

  if (result === "approved") {
    return (
      <div className="auth-card">
        <p className="eyebrow caption-3">Approved</p>
        <h2 className="heading-4">Return to your terminal.</h2>
        <p className="auth-copyline body-5">
          The CLI is finishing sign-in. You can close this tab.
        </p>
      </div>
    );
  }

  if (result === "denied") {
    return (
      <div className="auth-card">
        <p className="eyebrow caption-3">Denied</p>
        <h2 className="heading-4">Access was not granted.</h2>
        <p className="auth-copyline body-5">
          The terminal was told that this request was denied. You can close this tab.
        </p>
      </div>
    );
  }

  if (result === "claimed") {
    return (
      <div className="auth-card">
        <p className="eyebrow caption-3">CLI sign-in</p>
        <h2 className="heading-4">This request was already used.</h2>
        <p className="auth-copyline body-5">
          Run <code>graphia login</code> again if the terminal still needs a session.
        </p>
      </div>
    );
  }

  if (result === "expired") {
    return (
      <div className="auth-card">
        <p className="eyebrow caption-3">Expired</p>
        <h2 className="heading-4">This request timed out.</h2>
        <p className="auth-copyline body-5">
          Run <code>graphia login</code> again to get a fresh link.
        </p>
      </div>
    );
  }

  if (!user || !request) {
    return (
      <div className="auth-card">
        <p className="eyebrow caption-3">CLI sign-in</p>
        <h2 className="heading-4">Checking this request…</h2>
        <p className="auth-copyline body-5">One moment.</p>
      </div>
    );
  }

  if (user.isGuest) {
    return (
      <div className="auth-card">
        <p className="eyebrow caption-3">Member account required</p>
        <h2 className="heading-4">The CLI is for members.</h2>
        <p className="auth-copyline body-5">
          Guests can convert in the browser, but terminal access needs a member account.
        </p>
        <a className="btn btn-primary btn-large btn-wide" href={`/login?next=${encodeURIComponent(nextPath)}`}>
          Sign in with a member account
        </a>
      </div>
    );
  }

  return (
    <div className="auth-card">
      <p className="eyebrow caption-3">CLI sign-in</p>
      <h2 className="heading-4">Approve this terminal.</h2>
      <p className="auth-copyline body-5">
        Only approve if you just ran <code>graphia login</code> and this device name looks
        familiar.
      </p>

      <dl className="cli-details">
        <div>
          <dt className="caption-4">Device</dt>
          <dd className="title-3">{request.name}</dd>
        </div>
        <div>
          <dt className="caption-4">Code</dt>
          <dd className="mono">{shortCode(code)}</dd>
        </div>
        <div>
          <dt className="caption-4">Expires</dt>
          <dd className="mono">{expiryLabel(request.expiresAt)}</dd>
        </div>
        <div>
          <dt className="caption-4">Account</dt>
          <dd className="title-3">{user.email}</dd>
        </div>
      </dl>

      {error ? (
        <p className="alert" role="alert">
          {error}
        </p>
      ) : null}

      <div className="cli-actions">
        <button
          className="btn btn-primary btn-large"
          type="button"
          disabled={busy}
          onClick={() => void decide("approve")}
        >
          {busy ? "Working…" : "Approve"}
        </button>
        <button
          className="btn btn-ghost btn-large"
          type="button"
          disabled={busy}
          onClick={() => void decide("deny")}
        >
          Deny
        </button>
      </div>

      <p className="auth-guest-note caption-5">
        This gives the CLI the same access as your browser session. Sign out with{" "}
        <code>graphia logout</code> to revoke it.
      </p>
    </div>
  );
}
