"use client";

import { Check, Joystick, Ticket, X } from "@phosphor-icons/react";

import {
  PoolProgress,
  StatusChip,
  type RunStatus,
} from "@/components/arcade/ArcadeBits";
import { formatBytes, formatDate } from "@/lib/files";
import type { Conversion } from "@/lib/types";

const STATUS_COPY = {
  PENDING: {
    label: "Queued",
    chip: "QUEUED",
    note: "Waiting for a free lane. The processor will claim it shortly.",
    status: "queued" as RunStatus,
    stage: 0 as const,
  },
  PROCESSING: {
    label: "Running",
    chip: "RUNNING",
    note: "The conversion is in the water. The lane meter updates automatically.",
    status: "running" as RunStatus,
    stage: 1 as const,
  },
  COMPLETED: {
    label: "Complete",
    chip: "COMPLETE",
    note: "Your file is out of the pool. Collect it from the locker below.",
    status: "complete" as RunStatus,
    stage: 2 as const,
  },
  FAILED: {
    label: "Fault",
    chip: "FAULT",
    note: "The run stopped. Read the fault note, then try another mode.",
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
          ? Joystick
          : Ticket;

  return (
    <article className="pass-card" data-status={copy.status}>
      <div className="pass-top">
        <div className="pass-label">
          <Ticket size={20} weight="bold" aria-hidden="true" />
          Run ticket
        </div>
        <StatusChip status={copy.status} label={copy.chip} />
      </div>

      <p className="pass-number">No. {job.id.slice(0, 8).toUpperCase()}</p>
      <h1 className="pass-title">{job.originalFilename}</h1>
      <p className="pass-mode">
        {job.operationLabel} <span aria-hidden="true">/</span>{" "}
        <span className="mono">{job.id.slice(0, 4)}</span>
      </p>

      <div className="pass-grid">
        <div>
          <span className="meta-label">Input</span>
          <span className="meta-value">{formatBytes(job.fileSize)}</span>
        </div>
        <div>
          <span className="meta-label">Output</span>
          <span className="meta-value">{job.outputFilename ?? "—"}</span>
        </div>
        <div>
          <span className="meta-label">Started</span>
          <span className="meta-value">{formatDate(job.startedAt)}</span>
        </div>
        <div>
          <span className="meta-label">Finished</span>
          <span className="meta-value">{formatDate(job.completedAt)}</span>
        </div>
      </div>

      <PoolProgress stage={copy.stage} status={copy.status} />

      <div className={`run-state run-state--${copy.status}`} aria-live="polite">
        <StatusIcon className="run-state__icon" size={40} weight="bold" aria-hidden="true" />
        <div>
          <strong>{copy.label}</strong>
          <p className="muted small">{copy.note}</p>
        </div>
      </div>

      {job.status === "FAILED" && job.errorMessage ? (
        <div className="alert alert--fault" role="alert">
          <strong>Fault:</strong> {job.errorMessage}
        </div>
      ) : null}

      <div className="pass-footer">
        <span className="mono">Locker expires {formatDate(job.expiresAt)}</span>
        <span className="mono">
          {job.attempts > 1 ? `${job.attempts} runs` : "Single run"}
        </span>
      </div>
    </article>
  );
}
