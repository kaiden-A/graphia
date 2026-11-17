"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ArrowsClockwise, WarningCircle } from "@phosphor-icons/react";

import JobTicket from "@/components/converter/JobTicket";
import { apiJson, messageForError } from "@/lib/api-client";
import { formatDate } from "@/lib/files";
import type { DownloadTicket } from "@/lib/types";
import { useConversionPolling } from "@/lib/useConversionPolling";

export default function ConversionPage({ id }: { id: string }) {
  const router = useRouter();
  const { job, error, notFound, loading } = useConversionPolling(id);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const keepRef = useRef<HTMLButtonElement>(null);
  const deleteRef = useRef<HTMLButtonElement>(null);
  const wasConfirming = useRef(false);

  useEffect(() => {
    if (confirmingDelete) {
      keepRef.current?.focus();
    } else if (wasConfirming.current) {
      deleteRef.current?.focus();
    }
    wasConfirming.current = confirmingDelete;
  }, [confirmingDelete]);

  async function download() {
    if (!job) return;
    setDownloadError(null);
    setDownloading(true);
    try {
      const ticket = await apiJson<DownloadTicket>(`/api/conversions/${job.id}/download`);
      window.location.assign(ticket.url);
    } catch (caught) {
      setDownloadError(messageForError(caught));
    } finally {
      setDownloading(false);
    }
  }

  async function remove() {
    if (!job) return;
    setDeleting(true);
    setDownloadError(null);
    try {
      await apiJson<null>(`/api/conversions/${job.id}`, { method: "DELETE" });
      router.replace("/convert");
      router.refresh();
    } catch (caught) {
      setDownloadError(messageForError(caught));
      setDeleting(false);
      setConfirmingDelete(false);
    }
  }

  if (notFound) {
    return (
      <section className="center-page">
        <p className="eyebrow caption-3">Not found</p>
        <h1 className="heading-3">This ticket is not here.</h1>
        <p className="body-2">
          It may have been deleted, expired, or opened under another account.
        </p>
        <Link className="btn btn-primary" href="/convert">
          Start a run
        </Link>
      </section>
    );
  }

  if (loading && !job) {
    return (
      <section className="job-page" aria-live="polite" aria-busy="true">
        <span className="visually-hidden" role="status">
          Loading the run ticket.
        </span>

        <div className="page-lead">
          <span className="skeleton skeleton-back" />
        </div>

        <div className="job-layout">
          <div className="ticket ticket--skeleton">
            <div className="ticket-head">
              <span className="skeleton skeleton-line skeleton-line--short" />
              <span className="skeleton skeleton-chip" />
            </div>
            <span className="skeleton skeleton-line skeleton-line--short" />
            <span className="skeleton skeleton-title" />
            <span className="skeleton skeleton-line skeleton-line--short" />
            <div className="ticket-grid ticket-grid--skeleton">
              {[0, 1, 2, 3, 4, 5].map((item) => (
                <div key={item}>
                  <span className="skeleton skeleton-line skeleton-line--short" />
                  <span className="skeleton skeleton-line" />
                </div>
              ))}
            </div>
            <span className="skeleton skeleton-track" />
            <span className="skeleton skeleton-line" />
            <span className="skeleton skeleton-line skeleton-line--short" />
          </div>

          <div className="action-panel action-panel--skeleton">
            <span className="skeleton skeleton-line skeleton-line--short" />
            <span className="skeleton skeleton-title" />
            <span className="skeleton skeleton-line" />
            <span className="skeleton skeleton-line skeleton-line--short" />
            <span className="skeleton skeleton-button" />
          </div>
        </div>
      </section>
    );
  }

  if (!job) {
    return (
      <section className="center-page">
        <p className="eyebrow caption-3">Unavailable</p>
        <h1 className="heading-3">The ticket could not be loaded.</h1>
        <p className="alert" role="alert">
          <WarningCircle size={18} weight="bold" aria-hidden="true" />
          <span>{error ?? "Try refreshing the page."}</span>
        </p>
        <Link className="btn btn-primary" href="/convert">
          Back to the converter
        </Link>
      </section>
    );
  }

  const finished = job.status === "COMPLETED" && job.downloadAvailable;
  const gated = finished && job.downloadRequiresAccount;
  const jobPath = `/conversions/${job.id}`;

  return (
    <section className="job-page">
      <div className="page-lead">
        <Link className="back-link caption-1" href="/convert">
          ← Back to the converter
        </Link>
        <p className="eyebrow caption-3">Run desk</p>
      </div>

      {error ? (
        <p className="notice" role="status">
          <ArrowsClockwise size={16} weight="bold" aria-hidden="true" />
          <span>
            Live updates paused. {error} The page is retrying on its own.
          </span>
        </p>
      ) : null}

      <div className="job-layout">
        <JobTicket job={job} />

        <aside className="action-panel">
          <p className="eyebrow caption-3">Collect</p>

          {finished && !gated ? (
            <>
              <h2 className="heading-5">Take the file.</h2>
              <p className="body-5">
                The download link is signed and short lived. Request it when you are ready.
              </p>
              <button
                className="btn btn-primary btn-large btn-wide"
                onClick={download}
                disabled={downloading}
                aria-busy={downloading}
              >
                {downloading ? "Requesting the link…" : "Download result"}
              </button>
            </>
          ) : null}

          {gated ? (
            <>
              <h2 className="heading-5">Ready. Sign in to collect it.</h2>
              <p className="body-5">
                The conversion finished, and the file stays in the locker until{" "}
                {formatDate(job.expiresAt)}. Guest downloads need an account. Signing in
                moves this ticket to your account.
              </p>
              <Link
                className="btn btn-primary btn-large btn-wide"
                href={`/login?next=${encodeURIComponent(jobPath)}`}
              >
                Sign in to download
              </Link>
              <Link
                className="btn btn-ghost btn-wide"
                href={`/signup?next=${encodeURIComponent(jobPath)}`}
              >
                Create an account
              </Link>
            </>
          ) : null}

          {job.status === "PENDING" || job.status === "PROCESSING" ? (
            <>
              <h2 className="heading-5">The run is still going.</h2>
              <p className="body-5">
                You can leave this page and come back. The processor keeps working in the
                background.
              </p>
              <p className="live-note caption-4">
                <span className="live-dot" aria-hidden="true" />
                {job.status === "PENDING" ? "Waiting for the processor" : "Converting now"}
              </p>
            </>
          ) : null}

          {job.status === "FAILED" ? (
            <>
              <h2 className="heading-5">Stopped before the result.</h2>
              <p className="body-5">
                Read the reason on the ticket, then try another file or mode.
              </p>
              <Link className="btn btn-primary btn-large btn-wide" href="/convert">
                Try another file
              </Link>
            </>
          ) : null}

          {job.status === "COMPLETED" && !job.downloadAvailable ? (
            <>
              <h2 className="heading-5">The locker is empty.</h2>
              <p className="body-5">
                Files leave when the clock runs out. Send the document again for a new run.
              </p>
              <Link className="btn btn-primary btn-large btn-wide" href="/convert">
                Send it again
              </Link>
            </>
          ) : null}

          {job.downloadRequiresAccount && !finished ? (
            <p className="guest-note caption-5">
              Guest run. Signing in moves this ticket to your account before you collect it.
            </p>
          ) : null}

          <p className="locker-note caption-4">
            One run, one output. The download key expires quickly on purpose.
          </p>

          {downloadError ? (
            <p className="alert" role="alert">
              <WarningCircle size={18} weight="bold" aria-hidden="true" />
              <span>{downloadError}</span>
            </p>
          ) : null}

          <div className="action-divider" />

          {confirmingDelete ? (
            <div className="danger-zone">
              <p className="caption-5">Delete this run and its stored files?</p>
              <div className="danger-actions">
                <button
                  className="btn btn-danger btn-small"
                  onClick={remove}
                  disabled={deleting}
                >
                  {deleting ? "Deleting…" : "Delete run"}
                </button>
                <button
                  className="btn btn-ghost btn-small"
                  onClick={() => setConfirmingDelete(false)}
                  disabled={deleting}
                  ref={keepRef}
                >
                  Keep it
                </button>
              </div>
            </div>
          ) : (
            <>
              <button
                className="btn btn-ghost btn-small"
                onClick={() => setConfirmingDelete(true)}
                disabled={job.status === "PROCESSING"}
                ref={deleteRef}
              >
                Delete run
              </button>
              <p className="fine-print caption-5">
                {job.status === "PROCESSING"
                  ? "A running job cannot be deleted."
                  : "Deleting removes the input and output objects from storage."}
              </p>
            </>
          )}
        </aside>
      </div>
    </section>
  );
}
