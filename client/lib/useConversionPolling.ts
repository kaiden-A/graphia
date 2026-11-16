"use client";

import { useEffect, useState } from "react";

import { ApiError, apiJson, messageForError } from "@/lib/api-client";
import type { Conversion } from "@/lib/types";

export function useConversionPolling(id: string) {
  const [job, setJob] = useState<Conversion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let delay = 1500;

    async function tick() {
      try {
        const data = await apiJson<Conversion>(`/api/conversions/${id}`);
        if (cancelled) return;
        setJob(data);
        setError(null);
        setLoading(false);
        if (data.status === "COMPLETED" || data.status === "FAILED") {
          return;
        }
        delay = 1500;
      } catch (caught) {
        if (cancelled) return;
        if (caught instanceof ApiError && caught.status === 404) {
          setNotFound(true);
          setLoading(false);
          return;
        }
        setError(messageForError(caught));
        setLoading(false);
        delay = Math.min(delay * 1.7, 10_000);
      }
      timer = setTimeout(tick, delay);
    }

    setLoading(true);
    setNotFound(false);
    void tick();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [id]);

  return { job, error, notFound, loading };
}
