import type { Metadata } from "next";

import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Converter — Graphia",
  description:
    "Convert DOCX, PDF, Markdown, text, and images. Uploads go straight to private storage.",
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
