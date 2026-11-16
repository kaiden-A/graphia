import type { Metadata, Viewport } from "next";
import { Geist_Mono, Manrope } from "next/font/google";

import "./globals.css";

const body = Manrope({
  subsets: ["latin"],
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
  title: "Graphia — document conversion, privately run",
  description:
    "Turn DOCX, PDF, Markdown, text, and images into the file you need. Uploads go straight to private storage, and every run returns a ticket you can read.",
  robots: {
    index: false,
    follow: false,
  },
  openGraph: {
    title: "Graphia — document conversion, privately run",
    description:
      "A private press for everyday documents. Five modes, direct uploads, and a ticket you can read.",
    type: "website",
  },
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#F4ECDF",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${body.variable} ${mono.variable}`}>{children}</body>
    </html>
  );
}
