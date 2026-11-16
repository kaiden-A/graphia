import type { Metadata } from "next";
import { Geist_Mono, Poppins } from "next/font/google";

import "./globals.css";

const body = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

const mono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "Graphia — document arcade",
  description:
    "A poolside arcade for converting DOCX, PDF, Markdown, text, and images.",
  robots: {
    index: false,
    follow: false,
  },
  openGraph: {
    title: "Graphia — document arcade",
    description:
      "Drop a document. Pick a mode. Take a different file.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${body.variable} ${mono.variable}`}>{children}</body>
    </html>
  );
}
