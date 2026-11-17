export type RunStatus = "queued" | "running" | "complete" | "failed" | "expired";

export function StatusChip({ status, label }: { status: RunStatus; label: string }) {
  const live = status === "queued" || status === "running";
  return (
    <span
      className={`status-chip status-chip--${status} caption-3`}
      data-live={live || undefined}
    >
      {live ? <span className="status-chip__dot" aria-hidden="true" /> : null}
      {label}
    </span>
  );
}

export function TicketProgress({
  stage,
  status = "running",
}: {
  stage: 0 | 1 | 2;
  status?: RunStatus;
}) {
  const percent = stage === 0 ? 6 : stage === 1 ? 56 : 100;
  const labels = ["Received", "Converting", "Ready"];

  return (
    <div className="ticket-progress" data-status={status}>
      <div
        className="ticket-progress__track"
        role="progressbar"
        aria-label="Run progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <span style={{ transform: `scaleX(${percent / 100})` }} />
      </div>
      <div className="ticket-progress__stops">
        {labels.map((label, index) => (
          <span
            key={label}
            className="caption-5"
            data-reached={stage >= index || undefined}
            aria-current={stage === index ? "step" : undefined}
          >
            <span className="ticket-progress__dot" aria-hidden="true" />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
