import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Graphia — document conversion desk",
  description:
    "A small private desk for converting DOCX, PDF, Markdown, text, and images.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
