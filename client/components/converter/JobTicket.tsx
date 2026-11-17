"use client";

import { useEffect, useState } from "react";
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
    note: "The processor will claim this run in a moment. You can leave this page.",
    status: "queued" as RunStatus,
    stage: 0 as const,
  },
  PROCESSING: {
    label: "Running",
    chip: "RUNNING",
    note: "The conversion is running. This ticket refreshes on its own.",
    status: "running" as RunStatus,
    stage: 1 as const,
  },
  COMPLETED: {
    label: "Ready",
    chip: "READY",
    note: "The result is ready in the collect panel. The download link is issued when you ask for it.",
    status: "complete" as RunStatus,
    stage: 2 as const,
  },
  FAILED: {
    label: "Stopped",
    chip: "FAILED",
    note: "The run stopped before it finished. The reason is on this ticket.",
    status: "failed" as RunStatus,
    stage: 1 as const,
  },
} as const;

function elapsedSeconds(job: Conversion, now: number): number | null {
  if (job.status === "COMPLETED" || job.status === "FAILED") {
    if (!job.startedAt || !job.completedAt) return null;
    return Math.max(1, Math.round((job.completedAt - job.startedAt) / 1000));
  }
  const anchor = job.status === "PROCESSING" ? job.startedAt : job.createdAt;
  if (!anchor) return null;
  return Math.max(1, Math.floor((now - anchor) / 1000));
}

function formatElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest ? `${minutes}m ${rest}s` : `${minutes}m`;
}

function elapsedCopy(job: Conversion, seconds: number | null): string | null {
  if (seconds === null) return null;
  if (job.status === "COMPLETED") return `Finished in ${formatElapsed(seconds)}`;
  if (job.status === "FAILED") return `Stopped after ${formatElapsed(seconds)}`;
  if (job.status === "PROCESSING") return `Running ${formatElapsed(seconds)}`;
  if (job.status === "PENDING") return `Waiting ${formatElapsed(seconds)}`;
  return null;
}

function remainingCopy(expiresAt: number | null, now: number): string | null {
  if (!expiresAt) return null;
  const remaining = expiresAt - now;
  if (remaining <= 0) return "Locker cleared";

  const minutes = Math.max(1, Math.ceil(remaining / 60_000));
  if (minutes < 60) return `Locker closes in ${minutes} min`;

  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `Locker closes in ${hours}h ${rest}m` : `Locker closes in ${hours}h`;
}

export default function JobTicket({ job }: { job: Conversion }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    setNow(Date.now());
    const interval = job.status === "PENDING" || job.status === "PROCESSING" ? 1000 : 60_000;
    const timer = window.setInterval(() => setNow(Date.now()), interval);
    return () => window.clearInterval(timer);
  }, [job.status]);

  const isExpired = job.status === "COMPLETED" && !job.downloadAvailable;
  const copy = isExpired
    ? {
        label: "Expired",
        chip: "EXPIRED",
        note: "The locker has been cleared. Start a new run to convert the file again.",
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

  const elapsed = elapsedCopy(job, elapsedSeconds(job, now));
  const remaining = remainingCopy(job.expiresAt, now);

  return (
    <article className="ticket" data-status={copy.status}>
      <div className="ticket-head">
        <span className="eyebrow caption-3">Run ticket</span>
        <StatusChip key={copy.status} status={copy.status} label={copy.chip} />
      </div>

      <p className="ticket-number mono caption-4">
        No. {job.id.slice(0, 8).toUpperCase()}
      </p>
      <h1 className="ticket-title heading-4">{job.originalFilename}</h1>
      <p className="ticket-mode caption-1">{job.operationLabel}</p>
      {job.downloadRequiresAccount ? (
        <p className="ticket-guest caption-5">Guest run · sign in to download</p>
      ) : null}

      <div className="perforation" aria-hidden="true" />

      <dl className="ticket-grid">
        <div>
          <dt className="caption-4">Input size</dt>
          <dd className="title-3">{formatBytes(job.fileSize)}</dd>
        </div>
        <div>
          <dt className="caption-4">Output file</dt>
          <dd className="title-3" title={job.outputFilename ?? undefined}>
            {job.outputFilename ?? (job.status === "FAILED" ? "Not produced" : "Pending")}
          </dd>
        </div>
        <div>
          <dt className="caption-4">Output size</dt>
          <dd className="title-3">
            {job.outputSize ? formatBytes(job.outputSize) : "—"}
          </dd>
        </div>
        <div>
          <dt className="caption-4">Started</dt>
          <dd className="title-3">{formatDate(job.startedAt)}</dd>
        </div>
        <div>
          <dt className="caption-4">Finished</dt>
          <dd className="title-3">{formatDate(job.completedAt)}</dd>
        </div>
        <div>
          <dt className="caption-4">Locker</dt>
          <dd className="title-3" title={job.expiresAt ? formatDate(job.expiresAt) : undefined}>
            {remaining ?? "—"}
          </dd>
        </div>
      </dl>

      <TicketProgress stage={copy.stage} status={copy.status} />

      <div
        className={`run-state run-state--${copy.status}`}
        aria-live="polite"
        aria-atomic="true"
      >
        <span className="run-state__icon" aria-hidden="true" key={`icon-${copy.status}`}>
          <StatusIcon size={20} weight="bold" />
        </span>
        <div className="run-state__body" key={`body-${copy.status}`}>
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
        <span title={job.expiresAt ? formatDate(job.expiresAt) : undefined}>
          Expires {formatDate(job.expiresAt)}
        </span>
        {elapsed ? <span>{elapsed}</span> : null}
        <span>{job.attempts > 1 ? `${job.attempts} attempts` : "Single attempt"}</span>
      </div>
    </article>
  );
}
