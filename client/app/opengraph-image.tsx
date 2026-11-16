import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          background: "#131209",
          color: "#F6FBF7",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div
            style={{
              width: 56,
              height: 56,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "#1FAAC4",
              borderRadius: 999,
              color: "#131209",
              fontSize: 30,
              fontWeight: 700,
            }}
          >
            G
          </div>
          <div style={{ fontSize: 24, fontWeight: 700 }}>Graphia</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ color: "#F06BB1", fontSize: 24, letterSpacing: 3 }}>
            DOCUMENT ARCADE
          </div>
          <div style={{ maxWidth: 900, fontSize: 72, lineHeight: 1, fontWeight: 700 }}>
            Make a splash
          </div>
          <div style={{ maxWidth: 760, color: "#9BB0B5", fontSize: 30, lineHeight: 1.4 }}>
            Drop a document. Pick a mode. Take a different file.
          </div>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ height: 10, width: 180, background: "#1FAAC4", borderRadius: 999 }} />
          <div style={{ height: 10, width: 80, background: "#F06BB1", borderRadius: 999 }} />
        </div>
      </div>
    ),
    size,
  );
}
