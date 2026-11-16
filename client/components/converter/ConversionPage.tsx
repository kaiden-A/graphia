"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Drop, Joystick, Lightning } from "@phosphor-icons/react";

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
      <section className="center-card">
        <Drop className="center-glyph" size={56} weight="bold" aria-hidden="true" />
        <p className="panel-label">Empty lane</p>
        <h1 className="panel-title">This ticket is not in the pool.</h1>
        <p className="muted">
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
      <section className="center-card" aria-live="polite">
        <p className="panel-label">Loading lane</p>
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-line" />
        <div className="skeleton skeleton-line short" />
      </section>
    );
  }

  if (!job) {
    return (
      <section className="center-card">
        <Drop className="center-glyph" size={56} weight="bold" aria-hidden="true" />
        <p className="panel-label">Lane closed</p>
        <h1 className="panel-title">The ticket could not be loaded.</h1>
        <p className="alert">{error ?? "Try refreshing the page."}</p>
        <Link className="btn btn-primary" href="/convert">
          Back to the arcade
        </Link>
      </section>
    );
  }

  return (
    <section className="job-page">
      <div className="page-lead">
        <Link className="back-link" href="/convert">
          ← Back to the floor
        </Link>
        <p className="panel-label">Run desk</p>
      </div>

      <div className="job-layout">
        <JobTicket job={job} />

        <aside className="action-deck">
          <p className="panel-label">Locker</p>
          {job.status === "COMPLETED" && job.downloadAvailable ? (
            <>
              <h2 className="panel-title">Take the file.</h2>
              <p className="muted">
                This link is a temporary locker key. Request it only when you are ready to
                collect.
              </p>
              <button
                className="btn btn-primary btn-wide"
                onClick={download}
                disabled={downloading}
              >
                <Lightning className="btn-icon" size={20} weight="bold" aria-hidden="true" />
                {downloading ? "Opening the locker…" : "Download result"}
              </button>
            </>
          ) : null}

          {job.status === "PENDING" || job.status === "PROCESSING" ? (
            <>
              <h2 className="panel-title">The run is in the water.</h2>
              <p className="muted">
                You can leave this page and return to the ticket. The processor keeps the
                lane moving in the background.
              </p>
              <div className="joystick-motion" aria-hidden="true">
                <Joystick size={32} weight="bold" />
                <span>lane active</span>
              </div>
            </>
          ) : null}

          {job.status === "FAILED" ? (
            <>
              <h2 className="panel-title">Fault on the run.</h2>
              <p className="muted">
                Read the fault note on the ticket, then try another file or mode.
              </p>
              <Link className="btn btn-primary btn-wide" href="/convert">
                Try another file
              </Link>
            </>
          ) : null}

          {job.status === "COMPLETED" && !job.downloadAvailable ? (
            <>
              <h2 className="panel-title">Locker cleared.</h2>
              <p className="muted">
                Files leave when the clock runs out. Send the document again for a new run.
              </p>
              <Link className="btn btn-primary btn-wide" href="/convert">
                Send it again
              </Link>
            </>
          ) : null}

          <div className="locker-note">
            <Drop size={24} weight="bold" aria-hidden="true" />
            <span>One run. One output. The download key expires quickly on purpose.</span>
          </div>

          {downloadError ? (
            <p className="alert" role="alert">
              {downloadError}
            </p>
          ) : null}

          <div className="action-divider" />

          <button
            className="btn btn-ghost btn-small"
            onClick={remove}
            disabled={deleting || job.status === "PROCESSING"}
          >
            {deleting ? "Ejecting…" : "Eject job"}
          </button>
          <p className="fine-print">
            {job.status === "PROCESSING"
              ? "A running job cannot be ejected."
              : "Ejecting removes the input and output objects from storage."}
          </p>
        </aside>
      </div>
    </section>
  );
}
