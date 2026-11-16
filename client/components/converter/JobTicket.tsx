"use client";

import { formatBytes, formatDate } from "@/lib/files";
import type { Conversion } from "@/lib/types";

const STATUS_COPY = {
  PENDING: {
    label: "Queued",
    note: "The processor will pick this up shortly.",
    stamp: "queued",
  },
  PROCESSING: {
    label: "Processing",
    note: "The conversion is running. This page updates automatically.",
    stamp: "processing",
  },
  COMPLETED: {
    label: "Complete",
    note: "Your converted file is ready to download.",
    stamp: "complete",
  },
  FAILED: {
    label: "Failed",
    note: "The conversion did not finish.",
    stamp: "failed",
  },
} as const;

export default function JobTicket({ job }: { job: Conversion }) {
  const isExpired = job.status === "COMPLETED" && !job.downloadAvailable;
  const copy = isExpired
    ? {
        label: "Expired",
        note: "The stored file has passed its expiry time.",
        stamp: "failed" as const,
      }
    : STATUS_COPY[job.status];
  const steps = [
    { key: "queued", label: "Queued", done: true },
    {
      key: "processing",
      label: "Processing",
      done: job.status === "PROCESSING" || job.status === "COMPLETED",
      active: job.status === "PROCESSING",
    },
    {
      key: "ready",
      label: "Ready",
      done: job.status === "COMPLETED",
      active: job.status === "COMPLETED",
    },
  ];

  return (
    <article className="ticket card">
      <div className="ticket-top">
        <div>
          <p className="eyebrow">Job ticket</p>
          <h1 className="ticket-title">{job.originalFilename}</h1>
          <p className="ticket-sub">
            {job.operationLabel} <span className="muted">·</span>{" "}
            <span className="mono">{job.id.slice(0, 8)}</span>
          </p>
        </div>
        <span className={`stamp stamp-${copy.stamp}`} aria-label={`Status: ${copy.label}`}>
          {copy.label}
        </span>
      </div>

      <div className="ticket-rule" />

      <div className="ticket-meta">
        <div>
          <span className="meta-label">Input</span>
          <span className="meta-value">{formatBytes(job.fileSize)}</span>
        </div>
        <div>
          <span className="meta-label">Output</span>
          <span className="meta-value">
            {job.outputFilename ? `${job.outputFilename}` : `—`}
          </span>
        </div>
        <div>
          <span className="meta-label">Started</span>
          <span className="meta-value">{formatDate(job.startedAt)}</span>
        </div>
        <div>
          <span className="meta-label">Ready</span>
          <span className="meta-value">{formatDate(job.completedAt)}</span>
        </div>
      </div>

      <div className="ticket-status" aria-live="polite">
        <div className={`status-orb status-orb-${copy.stamp}`} aria-hidden="true" />
        <div>
          <strong>{copy.label}</strong>
          <p className="muted small">{copy.note}</p>
        </div>
      </div>

      {job.status !== "FAILED" ? (
        <ol className="timeline" aria-label="Conversion progress">
          {steps.map((step) => (
            <li
              key={step.key}
              className="timeline-step"
              data-done={step.done || undefined}
              data-active={step.active || undefined}
            >
              <span className="timeline-dot" aria-hidden="true" />
              <span>{step.label}</span>
            </li>
          ))}
        </ol>
      ) : null}

      {job.status === "FAILED" && job.errorMessage ? (
        <div className="error-banner" role="alert">
          <strong>What happened:</strong> {job.errorMessage}
        </div>
      ) : null}

      <div className="ticket-footer mono">
        <span>Expires {formatDate(job.expiresAt)}</span>
        <span>{job.attempts > 1 ? `${job.attempts} attempts` : "Single pass"}</span>
      </div>
    </article>
  );
}
