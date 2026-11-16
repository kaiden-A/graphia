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
          padding: "64px 72px",
          background: "#F4ECDF",
          color: "#241B15",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 12,
              height: 12,
              background: "#0047AB",
              display: "flex",
            }}
          />
          <div style={{ fontSize: 30, fontWeight: 700, letterSpacing: -0.5 }}>
            Graphia
          </div>
          <div
            style={{
              marginLeft: 8,
              fontSize: 18,
              color: "#6A5647",
              letterSpacing: 2,
              textTransform: "uppercase",
            }}
          >
            Document atelier
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ fontSize: 20, color: "#6A5647", letterSpacing: 2 }}>
            DOCUMENT CONVERSION, PRIVATELY RUN
          </div>
          <div
            style={{
              display: "flex",
              maxWidth: 900,
              fontSize: 72,
              lineHeight: 1.05,
              fontWeight: 600,
              letterSpacing: -2.5,
            }}
          >
            A private press for everyday documents.
          </div>
          <div style={{ maxWidth: 780, color: "#6A5647", fontSize: 26, lineHeight: 1.4 }}>
            DOCX, PDF, Markdown, text, and images. Direct uploads and a ticket you can read.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderTop: "1px solid #DCCDB6",
            paddingTop: 20,
            fontSize: 20,
            color: "#6A5647",
          }}
        >
          <div style={{ display: "flex", gap: 32 }}>
            <span>25 MB per file</span>
            <span>5 modes</span>
            <span>Files expire in 24 hours</span>
          </div>
          <div style={{ width: 96, height: 6, background: "#0047AB" }} />
        </div>
      </div>
    ),
    size,
  );
}
