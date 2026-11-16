"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import JobTicket from "@/components/converter/JobTicket";
import { apiJson, messageForError } from "@/lib/api-client";
import type { DownloadTicket } from "@/lib/types";
import { useConversionPolling } from "@/lib/useConversionPolling";

export default function ConversionPage({ id }: { id: string }) {
  const router = useRouter();
  const { job, error, notFound, loading } = useConversionPolling(id);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

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
      <section className="center-page" aria-live="polite" aria-busy="true">
        <p className="eyebrow caption-3">Loading</p>
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-line" />
        <div className="skeleton skeleton-line skeleton-line--short" />
      </section>
    );
  }

  if (!job) {
    return (
      <section className="center-page">
        <p className="eyebrow caption-3">Unavailable</p>
        <h1 className="heading-3">The ticket could not be loaded.</h1>
        <p className="alert">{error ?? "Try refreshing the page."}</p>
        <Link className="btn btn-primary" href="/convert">
          Back to the converter
        </Link>
      </section>
    );
  }

  const finished = job.status === "COMPLETED" && job.downloadAvailable;

  return (
    <section className="job-page">
      <div className="page-lead">
        <Link className="back-link caption-1" href="/convert">
          ← Back to the converter
        </Link>
        <p className="eyebrow caption-3">Run desk</p>
      </div>

      <div className="job-layout">
        <JobTicket job={job} />

        <aside className="action-panel">
          <p className="eyebrow caption-3">Collect</p>

          {finished ? (
            <>
              <h2 className="heading-5">Take the file.</h2>
              <p className="body-5">
                The download link is signed and short lived. Request it when you are ready.
              </p>
              <button
                className="btn btn-primary btn-large btn-wide"
                onClick={download}
                disabled={downloading}
              >
                {downloading ? "Requesting the link…" : "Download result"}
              </button>
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

          <p className="locker-note caption-4">
            One run, one output. The download key expires quickly on purpose.
          </p>

          {downloadError ? (
            <p className="alert" role="alert">
              {downloadError}
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
