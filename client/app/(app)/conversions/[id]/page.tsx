import type { Metadata } from "next";

import ConversionPage from "@/components/converter/ConversionPage";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Run ${id.slice(0, 8).toUpperCase()} — Graphia`,
    description: "Status, sizes, expiry, and the result of one Graphia run.",
  };
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ConversionPage id={id} />;
}
