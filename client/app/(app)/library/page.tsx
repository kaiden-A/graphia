import type { Metadata } from "next";

import LibraryBrowser from "@/components/library/LibraryBrowser";

export const metadata: Metadata = {
  title: "Library — Graphia",
  description:
    "Every conversion mode in one place. Pick a mode to open the converter with it selected.",
};

export default function LibraryPage() {
  return (
    <div className="library-page">
      <LibraryBrowser />
    </div>
  );
}
