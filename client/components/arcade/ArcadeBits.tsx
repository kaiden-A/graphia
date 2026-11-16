"use client";

import { Drop } from "@phosphor-icons/react";

export type RunStatus = "queued" | "running" | "complete" | "failed" | "expired";

export function StatusChip({ status, label }: { status: RunStatus; label: string }) {
  return <span className={`status-chip status-chip--${status}`}>{label}</span>;
}

export function PoolProgress({
  stage,
  status = "running",
}: {
  stage: 0 | 1 | 2;
  status?: RunStatus;
}) {
  const percent = stage === 0 ? 8 : stage === 1 ? 56 : 100;
  return (
    <div className="pool-progress" data-status={status}>
      <div className="pool-progress__track" aria-hidden="true">
        <div className="pool-progress__fill" style={{ width: `${percent}%` }} />
        <span className="pool-progress__swimmer">
          <Drop size={18} weight="fill" aria-hidden="true" />
        </span>
      </div>
      <div className="pool-progress__stops">
        <span data-reached={stage >= 0 || undefined}>Queue</span>
        <span data-reached={stage >= 1 || undefined}>Run</span>
        <span data-reached={stage >= 2 || undefined}>Dry</span>
      </div>
    </div>
  );
}

export function PoolBubbles() {
  const bubbles = [
    { left: "8%", size: 10, delay: "0s", duration: "7s" },
    { left: "18%", size: 5, delay: "2.2s", duration: "6s" },
    { left: "31%", size: 14, delay: "1.1s", duration: "9s" },
    { left: "48%", size: 7, delay: "3.4s", duration: "7.5s" },
    { left: "63%", size: 11, delay: "0.7s", duration: "8.5s" },
    { left: "76%", size: 6, delay: "2.8s", duration: "6.5s" },
    { left: "88%", size: 16, delay: "1.8s", duration: "10s" },
  ];
  return (
    <div className="pool-bubbles" aria-hidden="true">
      {bubbles.map((bubble) => (
        <span
          key={bubble.left}
          style={{
            left: bubble.left,
            width: bubble.size,
            height: bubble.size,
            animationDelay: bubble.delay,
            animationDuration: bubble.duration,
          }}
        />
      ))}
    </div>
  );
}

export function MarqueeBulbs() {
  return (
    <span className="marquee-bulbs" aria-hidden="true">
      {Array.from({ length: 12 }, (_, index) => (
        <i key={index} />
      ))}
    </span>
  );
}
