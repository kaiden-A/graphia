"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import JobTicket from "@/components/converter/JobTicket";
import { CompassIcon, ScrollIcon } from "@/components/scrapbook/icons";
import { PaperNote, TapeStrip } from "@/components/scrapbook/Ornaments";
import { apiJson, messageForError } from "@/lib/api-client";
import type { DownloadTicket } from "@/lib/types";
import { useConversionPolling } from "@/lib/useConversionPolling";

export default function ConversionPage({ id }: { id: string }) {
  const router = useRouter();
  const { job, error, notFound, loading } = useConversionPolling(id);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function download() {
    if (!job) return;
    setDownloadError(null);
    setDownloading(true);
    try {
      const ticket = await apiJson<DownloadTicket>(`/api/conversions/${job.id}/download`);
      window.location.assign(ticket.url);
    } catch (caught) {
      setDownloadError(messageForError(caught));
      setDownloading(false);
    }
  }

  async function remove() {
    if (!job) return;
    if (!window.confirm("Delete this conversion and its stored files?")) return;
    setDeleting(true);
    try {
      await apiJson<null>(`/api/conversions/${job.id}`, { method: "DELETE" });
      router.replace("/");
    } catch (caught) {
      setDownloadError(messageForError(caught));
      setDeleting(false);
    }
  }

  if (notFound) {
    return (
      <section className="center-card card">
        <p className="eyebrow">Not found</p>
        <h1 className="card-title">This ticket is not in your stack.</h1>
        <p className="muted">
          It may have been deleted, expired, or created under another account.
        </p>
        <Link className="btn btn-primary" href="/">
          Start a conversion
        </Link>
      </section>
    );
  }

  if (loading && !job) {
    return (
      <section className="center-card card" aria-live="polite">
        <p className="eyebrow">Loading ticket</p>
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-line" />
        <div className="skeleton skeleton-line short" />
      </section>
    );
  }

  if (!job) {
    return (
      <section className="center-card card">
        <p className="eyebrow">Something went wrong</p>
        <h1 className="card-title">The ticket could not be loaded.</h1>
        <p className="error-banner">{error ?? "Try refreshing the page."}</p>
        <Link className="btn btn-primary" href="/">
          Back to converter
        </Link>
      </section>
    );
  }

  return (
    <section className="job-page">
      <div className="page-lead">
        <Link className="back-link" href="/">
          ← Back to the desk
        </Link>
        <p className="eyebrow">The expedition desk</p>
      </div>

      <div className="job-layout">
        <JobTicket job={job} />

        <aside className="job-actions card">
          <TapeStrip className="action-tape" rotate={-5} />
          <p className="eyebrow">Next step</p>
          {job.status === "COMPLETED" && job.downloadAvailable ? (
            <>
              <h2 className="card-title">Bring it home.</h2>
              <p className="muted">
                The download link is temporary. Request it when you are ready to take the
                file.
              </p>
              <button
                className="btn btn-primary btn-wide"
                onClick={download}
                disabled={downloading}
              >
                <ScrollIcon className="btn-icon" />
                {downloading ? "Preparing the scroll…" : "Download result"}
              </button>
            </>
          ) : null}

          {job.status === "PENDING" || job.status === "PROCESSING" ? (
            <>
              <h2 className="card-title">The passage is underway.</h2>
              <p className="muted">
                You can leave this page and return to the ticket. The processor keeps
                working in the background.
              </p>
              <div className="passage-motion" aria-hidden="true">
                <CompassIcon />
                <span>following the route</span>
              </div>
            </>
          ) : null}

          {job.status === "FAILED" ? (
            <>
              <h2 className="card-title">A storm on the passage.</h2>
              <p className="muted">
                Read the note on the ticket, then try a different file or method.
              </p>
              <Link className="btn btn-primary btn-wide" href="/">
                Try another file
              </Link>
            </>
          ) : null}

          {job.status === "COMPLETED" && !job.downloadAvailable ? (
            <>
              <h2 className="card-title">The rest time is over.</h2>
              <p className="muted">
                Stored files are removed after their expiry. Send the document again to make
                a new ticket.
              </p>
              <Link className="btn btn-primary btn-wide" href="/">
                Send it again
              </Link>
            </>
          ) : null}

          <PaperNote className="action-note" rotate={1.4}>
            One ticket. One result. The download link is short-lived on purpose.
          </PaperNote>

          {downloadError ? (
            <p className="error-banner" role="alert">
              {downloadError}
            </p>
          ) : null}

          <div className="action-divider" />

          <button
            className="btn btn-ghost btn-small"
            onClick={remove}
            disabled={deleting || job.status === "PROCESSING"}
          >
            {deleting ? "Discarding…" : "Discard ticket"}
          </button>
          <p className="fine-print">
            {job.status === "PROCESSING"
              ? "A running passage cannot be discarded."
              : "Discarding removes the input and output objects from storage."}
          </p>
        </aside>
      </div>
    </section>
  );
}
