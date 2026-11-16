import type { Metadata } from "next";
import { Caveat, GFS_Didot, Karla } from "next/font/google";

import "./globals.css";

const display = GFS_Didot({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-display",
  display: "swap",
});

const body = Karla({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const hand = Caveat({
  subsets: ["latin"],
  variable: "--font-hand",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Graphia — an expedition for documents",
  description:
    "A small private field desk for converting DOCX, PDF, Markdown, text, and images.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable} ${hand.variable}`}>
        {children}
      </body>
    </html>
  );
}
