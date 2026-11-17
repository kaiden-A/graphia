import type { Metadata } from "next";

import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Graphia — document atelier",
  description:
    "Convert documents, read PDFs, and browse every mode. Uploads go straight to private storage.",
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
