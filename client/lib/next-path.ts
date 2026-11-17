export function safeNextPath(value: string | undefined, fallback = "/convert"): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return fallback;
  return value;
}
