"use client";

import {
  BoatIcon,
  CompassIcon,
  LaurelIcon,
  StormIcon,
} from "@/components/scrapbook/icons";
import {
  RouteMap,
  TapeStrip,
  WaxSeal,
  type SealStatus,
} from "@/components/scrapbook/Ornaments";
import { formatBytes, formatDate } from "@/lib/files";
import type { Conversion } from "@/lib/types";

const STATUS_COPY = {
  PENDING: {
    label: "Queued",
    stamp: "QUEUED",
    note: "The expedition is waiting at the dock. The processor will claim it shortly.",
    seal: "queued" as SealStatus,
    stage: 0 as const,
  },
  PROCESSING: {
    label: "Underway",
    stamp: "UNDERWAY",
    note: "The method is running. The route updates automatically.",
    seal: "processing" as SealStatus,
    stage: 1 as const,
  },
  COMPLETED: {
    label: "Complete",
    stamp: "COMPLETE",
    note: "The result has arrived. The download ticket is ready below.",
    seal: "complete" as SealStatus,
    stage: 2 as const,
  },
  FAILED: {
    label: "Failed",
    stamp: "STORM",
    note: "The passage did not finish. The note below says what happened.",
    seal: "failed" as SealStatus,
    stage: 1 as const,
  },
} as const;

export default function JobTicket({ job }: { job: Conversion }) {
  const isExpired = job.status === "COMPLETED" && !job.downloadAvailable;
  const copy = isExpired
    ? {
        label: "Expired",
        stamp: "EXPIRED",
        note: "The stored file has passed its rest time. Start a new expedition.",
        seal: "expired" as SealStatus,
        stage: 2 as const,
      }
    : STATUS_COPY[job.status];

  const StatusIcon =
    copy.seal === "complete"
      ? LaurelIcon
      : copy.seal === "failed"
        ? StormIcon
        : copy.seal === "processing"
          ? CompassIcon
          : BoatIcon;

  return (
    <article className="ticket card">
      <TapeStrip className="ticket-tape" rotate={4} />
      <div className="ticket-top">
        <div>
          <p className="eyebrow">Expedition ticket</p>
          <p className="folio-number">No. {job.id.slice(0, 8).toUpperCase()}</p>
        </div>
        <WaxSeal key={job.status} status={copy.seal} label={copy.stamp} />
      </div>

      <h1 className="ticket-title">{job.originalFilename}</h1>
      <p className="ticket-sub">
        {job.operationLabel} <span className="muted">·</span>{" "}
        <span className="mono">{job.id.slice(0, 4)}</span>
      </p>

      <div className="ticket-perf" />

      <div className="ticket-meta">
        <div>
          <span className="meta-label">Input</span>
          <span className="meta-value">{formatBytes(job.fileSize)}</span>
        </div>
        <div>
          <span className="meta-label">Result</span>
          <span className="meta-value">{job.outputFilename ?? "—"}</span>
        </div>
        <div>
          <span className="meta-label">Departed</span>
          <span className="meta-value">{formatDate(job.startedAt)}</span>
        </div>
        <div>
          <span className="meta-label">Arrived</span>
          <span className="meta-value">{formatDate(job.completedAt)}</span>
        </div>
      </div>

      <RouteMap stage={copy.stage} compact />

      <div className={`ticket-status ticket-status--${copy.seal}`} aria-live="polite">
        <StatusIcon className="status-icon" />
        <div>
          <strong>{copy.label}</strong>
          <p className="muted small">{copy.note}</p>
        </div>
      </div>

      {job.status === "FAILED" && job.errorMessage ? (
        <div className="error-banner" role="alert">
          <strong>What happened:</strong> {job.errorMessage}
        </div>
      ) : null}

      <div className="ticket-footer">
        <span className="mono">Expires {formatDate(job.expiresAt)}</span>
        <span className="mono">
          {job.attempts > 1 ? `${job.attempts} attempts` : "Single passage"}
        </span>
      </div>
    </article>
  );
}
