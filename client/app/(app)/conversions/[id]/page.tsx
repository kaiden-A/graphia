import ConversionPage from "@/components/converter/ConversionPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ConversionPage id={id} />;
}
