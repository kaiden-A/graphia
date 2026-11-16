import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const base = {
  viewBox: "0 0 48 48",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
} as const;

export function ScrollIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M14 9h18a5 5 0 0 1 5 5v22a3 3 0 0 1-3 3H16a5 5 0 0 1-5-5V12" />
      <path d="M14 9a3 3 0 0 0-3 3v3h6v-3a3 3 0 0 0-3-3Z" />
      <path d="M23 20h10M23 26h10M23 32h6" />
    </svg>
  );
}

export function CompassIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="24" cy="24" r="16" />
      <path d="M24 8v3M24 37v3M8 24h3M37 24h3" />
      <path className="icon-needle" d="m29 18-3 9-9 3 3-9 9-3Z" />
      <circle cx="24" cy="24" r="1.5" />
    </svg>
  );
}

export function BoatIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M9 29h30l-4 8H13l-4-8Z" />
      <path d="M24 29V12M24 13l11 10H24M24 16 15 23h9" />
      <path d="M6 40c3 0 3-2 6-2s3 2 6 2 3-2 6-2 3 2 6 2 3-2 6-2 3 2 6 2" />
    </svg>
  );
}

export function LaurelIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M17 40c-8-7-10-19-3-30" />
      <path d="M31 40c8-7 10-19 3-30" />
      <path d="M14 34c-3 0-5-2-5-5 3 0 5 2 5 5ZM12 27c-3 0-5-2-5-5 3 0 5 2 5 5ZM13 20c-2-1-3-4-2-7 3 1 4 4 2 7ZM17 14c-1-3 1-6 4-7 1 3-1 6-4 7Z" />
      <path d="M34 34c3 0 5-2 5-5-3 0-5 2-5 5ZM36 27c3 0 5-2 5-5-3 0-5 2-5 5ZM35 20c2-1 3-4 2-7-3 1-4 4-2 7ZM31 14c1-3-1-6-4-7-1 3 1 6 4 7Z" />
    </svg>
  );
}

export function AmphoraIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M18 9h12M20 9v5c0 4-7 7-7 14 0 7 5 11 11 11s11-4 11-11c0-7-7-10-7-14V9" />
      <path d="M17 17c-5 1-7 4-6 8 1 3 4 4 7 4M31 17c5 1 7 4 6 8-1 3-4 4-7 4" />
      <path d="M18 39h12" />
      <path d="M20 24c2 2 6 2 8 0M20 29c2 2 6 2 8 0" />
    </svg>
  );
}

export function TempleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 17 24 7l17 10H7Z" />
      <path d="M11 17v18M18 17v18M24 17v18M30 17v18M37 17v18" />
      <path d="M8 35h32M6 40h36" />
      <path d="M24 11v3" />
    </svg>
  );
}

export function QuillIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M39 8c-8 2-15 7-18 14l-3 7 7-3c7-3 12-10 14-18Z" />
      <path d="M39 8 22 25M20 27l-4 10 10-4" />
      <path d="M8 40h12" />
    </svg>
  );
}

export function TabletIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M11 9h26a3 3 0 0 1 3 3v24a3 3 0 0 1-3 3H11a3 3 0 0 1-3-3V12a3 3 0 0 1 3-3Z" />
      <path d="M14 14h20M14 20h20M14 26h12" />
      <path d="M31 31 39 23l3 3-8 8-4 1 1-4Z" />
    </svg>
  );
}

export function StormIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M13 27a8 8 0 0 1 2-15 10 10 0 0 1 19 3 7 7 0 0 1 1 14" />
      <path d="M27 28 21 38h7l-3 7 9-12h-6l3-5" />
    </svg>
  );
}

export function WaveIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 26c4 0 4-4 8-4s4 4 8 4 4-4 8-4 4 4 8 4 4-4 8-4" />
      <path d="M4 34c4 0 4-4 8-4s4 4 8 4 4-4 8-4 4 4 8 4 4-4 8-4" />
    </svg>
  );
}
