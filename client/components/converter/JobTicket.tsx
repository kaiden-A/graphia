"use client";

import { Check, Clock, Hourglass, X } from "@phosphor-icons/react";

import {
  StatusChip,
  TicketProgress,
  type RunStatus,
} from "@/components/converter/StatusBits";
import { formatBytes, formatDate } from "@/lib/files";
import type { Conversion } from "@/lib/types";

const STATUS_COPY = {
  PENDING: {
    label: "Queued",
    chip: "QUEUED",
    note: "The processor will claim this run shortly. You can leave the page.",
    status: "queued" as RunStatus,
    stage: 0 as const,
  },
  PROCESSING: {
    label: "Running",
    chip: "RUNNING",
    note: "The conversion is in progress. This ticket updates on its own.",
    status: "running" as RunStatus,
    stage: 1 as const,
  },
  COMPLETED: {
    label: "Ready",
    chip: "READY",
    note: "The result is in the locker below. The download link is issued on request.",
    status: "complete" as RunStatus,
    stage: 2 as const,
  },
  FAILED: {
    label: "Stopped",
    chip: "FAILED",
    note: "The run stopped before it finished. The reason is below.",
    status: "failed" as RunStatus,
    stage: 1 as const,
  },
} as const;

export default function JobTicket({ job }: { job: Conversion }) {
  const isExpired = job.status === "COMPLETED" && !job.downloadAvailable;
  const copy = isExpired
    ? {
        label: "Expired",
        chip: "EXPIRED",
        note: "The locker has been cleared. Send the file again to start a new run.",
        status: "expired" as RunStatus,
        stage: 2 as const,
      }
    : STATUS_COPY[job.status];

  const StatusIcon =
    copy.status === "complete"
      ? Check
      : copy.status === "failed" || copy.status === "expired"
        ? X
        : copy.status === "running"
          ? Hourglass
          : Clock;

  return (
    <article className="ticket" data-status={copy.status}>
      <div className="ticket-head">
        <span className="eyebrow caption-3">Run ticket</span>
        <StatusChip status={copy.status} label={copy.chip} />
      </div>

      <p className="ticket-number mono caption-4">
        No. {job.id.slice(0, 8).toUpperCase()}
      </p>
      <h1 className="ticket-title heading-4">{job.originalFilename}</h1>
      <p className="ticket-mode caption-1">{job.operationLabel}</p>

      <div className="perforation" aria-hidden="true" />

      <dl className="ticket-grid">
        <div>
          <dt className="caption-4">Input</dt>
          <dd className="title-3">{formatBytes(job.fileSize)}</dd>
        </div>
        <div>
          <dt className="caption-4">Output</dt>
          <dd className="title-3">{job.outputFilename ?? "—"}</dd>
        </div>
        <div>
          <dt className="caption-4">Started</dt>
          <dd className="title-3">{formatDate(job.startedAt)}</dd>
        </div>
        <div>
          <dt className="caption-4">Finished</dt>
          <dd className="title-3">{formatDate(job.completedAt)}</dd>
        </div>
      </dl>

      <TicketProgress stage={copy.stage} status={copy.status} />

      <div className={`run-state run-state--${copy.status}`} aria-live="polite">
        <span className="run-state__icon" aria-hidden="true">
          <StatusIcon size={20} weight="bold" />
        </span>
        <div>
          <strong className="title-3">{copy.label}</strong>
          <p className="body-5">{copy.note}</p>
        </div>
      </div>

      {job.status === "FAILED" && job.errorMessage ? (
        <div className="alert alert--fault" role="alert">
          <strong>Reason:</strong> {job.errorMessage}
        </div>
      ) : null}

      <div className="ticket-foot caption-5">
        <span>Locker expires {formatDate(job.expiresAt)}</span>
        <span>{job.attempts > 1 ? `${job.attempts} attempts` : "Single attempt"}</span>
      </div>
    </article>
  );
}
