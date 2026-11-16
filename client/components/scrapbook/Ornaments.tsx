"use client";

import { useId } from "react";

import { BoatIcon } from "@/components/scrapbook/icons";

type TapeProps = {
  className?: string;
  rotate?: number;
};

export function TapeStrip({ className = "", rotate = -3 }: TapeProps) {
  return (
    <span
      className={`tape-strip ${className}`}
      style={{ transform: `rotate(${rotate}deg)` }}
      aria-hidden="true"
    />
  );
}

export function MeanderRule({ className = "" }: { className?: string }) {
  const patternId = `meander-${useId().replace(/:/g, "")}`;
  return (
    <svg
      className={`meander-rule ${className}`}
      viewBox="0 0 600 18"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <pattern id={patternId} width="40" height="18" patternUnits="userSpaceOnUse">
          <path
            d="M0 15h10V5h10v10h10V5h10v10H0"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.4"
          />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${patternId})`} />
    </svg>
  );
}

export type SealStatus = "queued" | "processing" | "complete" | "failed" | "expired";

export function WaxSeal({
  status,
  label,
  className = "",
}: {
  status: SealStatus;
  label: string;
  className?: string;
}) {
  return (
    <span className={`wax-seal wax-seal--${status} ${className}`} aria-hidden="true">
      <span className="wax-seal__inner">
        <span className="wax-seal__mark">G</span>
        <span className="wax-seal__label">{label}</span>
      </span>
    </span>
  );
}

export function PaperNote({
  children,
  className = "",
  rotate = -1.5,
}: {
  children: React.ReactNode;
  className?: string;
  rotate?: number;
}) {
  return (
    <aside
      className={`paper-note ${className}`}
      style={{ transform: `rotate(${rotate}deg)` }}
    >
      {children}
    </aside>
  );
}

export function RouteMap({
  stage = 0,
  compact = false,
}: {
  stage?: 0 | 1 | 2;
  compact?: boolean;
}) {
  return (
    <div className={`route-map ${compact ? "route-map--compact" : ""}`} aria-hidden="true">
      <svg className="route-map__svg" viewBox="0 0 440 128" preserveAspectRatio="none">
        <path
          className="route-map__sea"
          d="M20 92C92 28 152 112 220 66S338 28 420 82"
        />
        <path
          className="route-map__segment route-map__segment--one"
          data-active={stage >= 1 || undefined}
          pathLength="1"
          d="M20 92C92 28 152 112 220 66"
        />
        <path
          className="route-map__segment route-map__segment--two"
          data-active={stage >= 2 || undefined}
          pathLength="1"
          d="M220 66C292 20 338 28 420 82"
        />
        <g className="route-map__stop" data-active={stage >= 0 || undefined}>
          <circle cx="20" cy="92" r="5" />
          <circle cx="20" cy="92" r="10" className="route-map__ring" />
          <text x="20" y="116">α</text>
        </g>
        <g className="route-map__stop" data-active={stage >= 1 || undefined}>
          <circle cx="220" cy="66" r="5" />
          <circle cx="220" cy="66" r="10" className="route-map__ring" />
          <text x="220" y="90">β</text>
        </g>
        <g className="route-map__stop" data-active={stage >= 2 || undefined}>
          <circle cx="420" cy="82" r="5" />
          <circle cx="420" cy="82" r="10" className="route-map__ring" />
          <text x="420" y="106">γ</text>
        </g>
        <path className="route-map__wave" d="M8 29c8 0 8-5 16-5s8 5 16 5" />
        <path className="route-map__wave route-map__wave--two" d="M352 105c8 0 8-5 16-5s8 5 16 5" />
      </svg>
      <span className="route-map__boat" data-stage={stage}>
        <BoatIcon />
      </span>
      <div className="route-map__labels">
        <span>Dispatch</span>
        <span>Passage</span>
        <span>Homecoming</span>
      </div>
    </div>
  );
}
