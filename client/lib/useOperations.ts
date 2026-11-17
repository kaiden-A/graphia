"use client";

import { useCallback, useEffect, useState } from "react";

import { apiJson, messageForError } from "@/lib/api-client";
import type { Operation } from "@/lib/types";

export function useOperations() {
  const [operations, setOperations] = useState<Operation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    apiJson<Operation[]>("/api/operations")
      .then((data) => {
        if (cancelled) return;
        setOperations(data);
        setLoading(false);
      })
      .catch((caught) => {
        if (cancelled) return;
        setError(messageForError(caught));
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const reload = useCallback(() => {
    setAttempt((value) => value + 1);
  }, []);

  return { operations, error, loading, reload };
}
