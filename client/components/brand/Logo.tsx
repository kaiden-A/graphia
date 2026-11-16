const FILE_GRAPH =
  "M9,10h1a1,1,0,0,0,0-2H9a1,1,0,0,0,0,2Zm5.21045,2.38623-1.67334,2.15186-.86816-.78125a.9997.9997,0,0,0-1.44971.11865l-2,2.5a.9998.9998,0,1,0,1.56152,1.249l1.33789-1.67236.87891.791a.99989.99989,0,0,0,1.45849-.12939l2.3335-3a1.00005,1.00005,0,0,0-1.5791-1.22754Zm5.7771-3.44794a1.0088,1.0088,0,0,0-.27936-.64373l-.00146-.0019L13.70734,2.29327l-.00183-.00146a.99022.99022,0,0,0-.28608-.19281c-.0299-.014-.061-.02191-.09246-.033a.98253.98253,0,0,0-.26667-.05383C13.03925,2.01086,13.02136,2,13,2H7A3.00328,3.00328,0,0,0,4,5V19a3.00328,3.00328,0,0,0,3,3H17a3.00328,3.00328,0,0,0,3-3V9C20,8.97809,19.989,8.95984,19.98755,8.93829ZM14,5.41406,16.58594,8H15a1.0013,1.0013,0,0,1-1-1ZM18,19a1.0013,1.0013,0,0,1-1,1H7a1.0013,1.0013,0,0,1-1-1V5A1.0013,1.0013,0,0,1,7,4h5V7a3.00328,3.00328,0,0,0,3,3h3Z";

export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg
      className="brand-mark"
      width={size}
      height={size}
      viewBox="0 0 36 36"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <rect x="0" y="4" width="32" height="32" rx="8" className="brand-mark__tile" />
      <g transform="translate(4 8)">
        <path d={FILE_GRAPH} className="brand-mark__glyph" />
      </g>
      <rect x="30" y="0" width="6" height="6" className="brand-mark__reg" />
    </svg>
  );
}

export default function Logo({
  tone = "dark",
  size = 32,
}: {
  tone?: "dark" | "light";
  size?: number;
}) {
  return (
    <span className="brand" data-tone={tone}>
      <LogoMark size={size} />
      <span className="brand-lockup">
        <span className="brand-name">Graphia</span>
        <span className="brand-tag">Document atelier</span>
      </span>
    </span>
  );
}
