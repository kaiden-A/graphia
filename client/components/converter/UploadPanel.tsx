"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import OperationPicker from "@/components/converter/OperationPicker";
import SelectedFile from "@/components/converter/SelectedFile";
import UploadDropzone from "@/components/converter/UploadDropzone";
import { ApiError, apiJson, messageForError } from "@/lib/api-client";
import {
  MAX_UPLOAD_BYTES,
  contentTypeFor,
  fileExtension,
  formatBytes,
} from "@/lib/files";
import type {
  CreateConversionResponse,
  Operation,
  OperationId,
  UploadTicket,
} from "@/lib/types";

type Phase = "idle" | "creating" | "uploading" | "confirming";

function putToR2(
  ticket: UploadTicket,
  file: File,
  onProgress: (value: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open(ticket.method, ticket.url, true);
    request.timeout = 5 * 60 * 1000;
    for (const [key, value] of Object.entries(ticket.headers)) {
      request.setRequestHeader(key, value);
    }
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    request.onload = () => {
      if (request.status >= 200 && request.status < 300) {
        onProgress(100);
        resolve();
        return;
      }
      reject(
        new Error(
          `Storage rejected the upload (${request.status}). If this repeats, check the R2 bucket CORS policy.`,
        ),
      );
    };
    request.onerror = () => {
      reject(
        new Error(
          "The file could not reach storage. Check the R2 bucket CORS policy and try again.",
        ),
      );
    };
    request.ontimeout = () => reject(new Error("The upload timed out. Try again."));
    request.send(file);
  });
}

export default function UploadPanel() {
  const router = useRouter();
  const [operations, setOperations] = useState<Operation[]>([]);
  const [operationsError, setOperationsError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [operation, setOperation] = useState<OperationId | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiJson<Operation[]>("/api/operations")
      .then((data) => {
        if (!cancelled) setOperations(data);
      })
      .catch((caught) => {
        if (!cancelled) setOperationsError(messageForError(caught));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const extension = file ? fileExtension(file.name) : null;
  const accept = useMemo(
    () => operations.flatMap((item) => item.inputExtensions.map((ext) => `.${ext}`)).join(","),
    [operations],
  );

  const compatible = useMemo(() => {
    if (!extension) return operations;
    return operations.filter((item) => item.inputExtensions.includes(extension));
  }, [operations, extension]);

  useEffect(() => {
    if (!file || !extension) return;
    if (operation && compatible.some((item) => item.id === operation)) return;
    setOperation(compatible[0]?.id ?? null);
  }, [file, extension, compatible, operation]);

  const busy = phase !== "idle";

  function chooseFile(next: File) {
    setError(null);
    if (next.size === 0) {
      setFile(null);
      setOperation(null);
      setError(`“${next.name}” is empty.`);
      return;
    }
    if (next.size > MAX_UPLOAD_BYTES) {
      setFile(null);
      setOperation(null);
      setError(`“${next.name}” is ${formatBytes(next.size)}. The limit is 25 MB.`);
      return;
    }
    setFile(next);
    setProgress(0);
  }

  async function convert() {
    if (!file || !operation) return;
    setError(null);
    setProgress(0);
    let created: CreateConversionResponse | null = null;

    try {
      setPhase("creating");
      created = await apiJson<CreateConversionResponse>("/api/conversions", {
        method: "POST",
        body: JSON.stringify({
          operation,
          originalFilename: file.name,
          fileSize: file.size,
          contentType: contentTypeFor(file),
        }),
      });

      setPhase("uploading");
      await putToR2(created.upload, file, setProgress);

      setPhase("confirming");
      await apiJson(`/api/conversions/${created.job.id}/complete-upload`, {
        method: "POST",
      });

      router.push(`/conversions/${created.job.id}`);
    } catch (caught) {
      setPhase("idle");
      setError(messageForError(caught));
      if (created) {
        try {
          await apiJson(`/api/conversions/${created.job.id}`, { method: "DELETE" });
        } catch (cleanupError) {
          if (!(cleanupError instanceof ApiError) || cleanupError.status !== 409) {
            // The job expires on its own; do not hide the original error.
          }
        }
      }
    }
  }

  return (
    <section className="card upload-card" aria-labelledby="upload-title">
      <div className="card-head">
        <div>
          <p className="eyebrow">New conversion</p>
          <h2 id="upload-title" className="card-title">
            Put a document in.
          </h2>
        </div>
        <span className="card-index mono">01</span>
      </div>

      <UploadDropzone accept={accept} disabled={busy} onFile={chooseFile} />

      {file ? (
        <SelectedFile
          file={file}
          disabled={busy}
          onRemove={() => {
            setFile(null);
            setOperation(null);
            setError(null);
          }}
        />
      ) : null}

      {operationsError ? (
        <p className="error-banner" role="alert">
          {operationsError}
        </p>
      ) : null}

      <div className="section-label">
        <span>Choose the operation</span>
        {extension ? <span className="mono muted">.{extension}</span> : null}
      </div>

      <OperationPicker
        operations={operations}
        value={operation}
        extension={extension}
        onChange={setOperation}
      />

      {error ? (
        <p className="error-banner" role="alert">
          {error}
        </p>
      ) : null}

      {phase === "uploading" ? (
        <div className="progress-wrap" aria-live="polite">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span className="progress-label mono">{progress}% uploaded</span>
        </div>
      ) : null}

      <div className="upload-actions">
        <button
          type="button"
          className="btn btn-primary btn-wide"
          onClick={convert}
          disabled={!file || !operation || busy || operations.length === 0}
        >
          {phase === "creating"
            ? "Creating job…"
            : phase === "uploading"
              ? `Uploading ${progress}%…`
              : phase === "confirming"
                ? "Starting conversion…"
                : "Convert document"}
        </button>
        <p className="fine-print">
          The file uploads straight to private object storage. Max 25 MB.
        </p>
      </div>
    </section>
  );
}
