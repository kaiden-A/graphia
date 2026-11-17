"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Check, WarningCircle } from "@phosphor-icons/react";

import OperationPicker, {
  OperationPickerSkeleton,
} from "@/components/converter/OperationPicker";
import SelectedFile from "@/components/converter/SelectedFile";
import UploadDropzone from "@/components/converter/UploadDropzone";
import { useCurrentUser } from "@/components/AppShell";

import { ApiError, apiJson, messageForError } from "@/lib/api-client";
import {
  MAX_UPLOAD_BYTES,
  contentTypeFor,
  fileExtension,
  fileStem,
  formatBytes,
} from "@/lib/files";
import type {
  CreateConversionResponse,
  Operation,
  OperationId,
  UploadTicket,
} from "@/lib/types";
import { useOperations } from "@/lib/useOperations";

type Phase = "idle" | "creating" | "uploading" | "confirming";

const FLOW = ["Create the run", "Upload the file", "Start the processor"];

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

function actionLabel(operation: Operation | null): string {
  if (!operation) return "Start the run";
  switch (operation.id) {
    case "docx_to_pdf":
    case "pptx_to_pdf":
    case "xlsx_to_pdf":
    case "images_to_pdf":
    case "markdown_to_pdf":
      return "Convert to PDF";
    case "pdf_to_markdown":
      return "Extract Markdown";
    case "pdf_to_text":
      return "Extract text";
    case "compress_pdf":
      return "Compress the PDF";
    case "docx_to_markdown":
    case "txt_to_markdown":
      return "Convert to Markdown";
    default:
      return "Start the run";
  }
}

function phaseLabel(phase: Phase, progress: number): string {
  switch (phase) {
    case "creating":
      return "Creating the run…";
    case "uploading":
      return `Uploading ${progress}%…`;
    case "confirming":
      return "Starting the processor…";
    default:
      return "";
  }
}

function PhaseRail({ phase }: { phase: Phase }) {
  const active = phase === "creating" ? 0 : phase === "uploading" ? 1 : 2;
  return (
    <>
      <p className="visually-hidden" role="status">
        Step {active + 1} of {FLOW.length}: {FLOW[active]}.
      </p>
      <ol className="phase-rail" aria-label="Run setup">
        {FLOW.map((label, index) => {
          const state = index < active ? "done" : index === active ? "active" : "waiting";
          return (
            <li
              className="phase-rail__step"
              data-state={state}
              key={label}
              aria-current={state === "active" ? "step" : undefined}
            >
              <span className="phase-rail__marker" aria-hidden="true">
                {state === "done" ? <Check size={12} weight="bold" /> : index + 1}
              </span>
              <span className="caption-4">{label}</span>
            </li>
          );
        })}
      </ol>
    </>
  );
}

export default function UploadPanel({
  initialOperation = null,
}: {
  initialOperation?: OperationId | null;
}) {
  const router = useRouter();
  const currentUser = useCurrentUser();
  const {
    operations,
    error: operationsError,
    loading: operationsLoading,
    reload,
  } = useOperations();
  const [file, setFile] = useState<File | null>(null);
  const [operation, setOperation] = useState<OperationId | null>(initialOperation);
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialOperation) setOperation(initialOperation);
  }, [initialOperation]);

  useEffect(() => {
    if (operations.length === 0) return;
    if (operation && !operations.some((item) => item.id === operation)) {
      setOperation(null);
    }
  }, [operation, operations]);

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

  const selectedOperation = useMemo(
    () => operations.find((item) => item.id === operation) ?? null,
    [operations, operation],
  );

  const outputName = useMemo(() => {
    if (!file || !selectedOperation) return null;
    return `${fileStem(file.name)}${selectedOperation.outputSuffix}.${selectedOperation.outputExtension}`;
  }, [file, selectedOperation]);

  const requiredInput = selectedOperation
    ? selectedOperation.inputExtensions.length === 1
      ? `.${selectedOperation.inputExtensions[0]}`
      : selectedOperation.inputExtensions.map((ext) => `.${ext}`).join(", ")
    : null;

  const busy = phase !== "idle";
  const canStart = Boolean(file && selectedOperation && !busy);
  const noMode = Boolean(file) && !operationsLoading && compatible.length === 0;

  const disabledReason = operationsLoading
    ? "Loading the available modes."
    : !operations.length
      ? "The modes are not available right now."
      : !file
        ? "Choose a file to start."
        : noMode
          ? "No mode accepts this file type."
          : !selectedOperation
            ? "Picking the matching mode."
            : "";

  const actionHint = busy
    ? "Keep this tab open while the file is sent."
    : canStart
      ? "Ready. This sends one file and opens its run ticket."
      : disabledReason;

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
    <section
      className="control-panel"
      id="upload-panel"
      aria-labelledby="upload-title"
      aria-busy={busy || undefined}
    >
      <div className="panel-head">
        <div>
          <p className="eyebrow caption-3">Upload</p>
          <h2 id="upload-title" className="heading-5">
            Choose a document.
          </h2>
        </div>
        <span className="panel-note caption-4">25 MB maximum</span>
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

      <div className="section-label">
        <span className="caption-1">
          {extension ? `Modes for .${extension}` : "Mode"}
        </span>
        <span className="section-label__meta">
          {extension ? <span className="format-code caption-5">.{extension}</span> : null}
          <Link className="text-link caption-5" href="/library">
            Browse all modes
          </Link>
        </span>
      </div>

      {operationsLoading ? (
        <div aria-busy="true">
          <span className="visually-hidden" role="status">
            Loading the available modes.
          </span>
          <OperationPickerSkeleton />
        </div>
      ) : null}

      {!operationsLoading && operationsError ? (
        <div className="mode-error" role="alert">
          <p className="caption-1">The modes did not load.</p>
          <p className="caption-5">{operationsError}</p>
          {file ? (
            <p className="caption-5">Your file is still selected. Try again without dropping it.</p>
          ) : null}
          <button type="button" className="text-button caption-1" onClick={reload}>
            Try again
          </button>
        </div>
      ) : null}

      {!operationsLoading && !operationsError && operations.length === 0 ? (
        <div className="mode-error">
          <p className="caption-1">No modes are available right now.</p>
          <button type="button" className="text-button caption-1" onClick={reload}>
            Try again
          </button>
        </div>
      ) : null}

      {!operationsLoading && !operationsError && compatible.length > 0 ? (
        <OperationPicker
          operations={operations}
          value={operation}
          extension={extension}
          onChange={setOperation}
        />
      ) : null}

      {file && selectedOperation ? (
        <div className="run-preview" aria-live="polite">
          <div className="run-preview__head">
            <span className="run-preview__label caption-4">{selectedOperation.label}</span>
            <span className="run-preview__size caption-5">{formatBytes(file.size)}</span>
          </div>
          <div className="run-preview__files">
            <span className="run-preview__name title-3">{file.name}</span>
            <span className="run-preview__arrow" aria-hidden="true">
              →
            </span>
            <span className="run-preview__name run-preview__name--out title-3">
              {outputName}
            </span>
          </div>
          <p className="run-preview__note caption-5">
            The upload goes straight to private storage. The processor starts when it lands.
          </p>
        </div>
      ) : (
        <p className="mode-note caption-5">
          {operationsLoading
            ? "Loading the available modes."
            : noMode
              ? `No mode accepts ${extension ? `.${extension}` : "this file"}. Remove the file and choose another format.`
              : !file && selectedOperation && requiredInput
                ? `Choose ${requiredInput} to use ${selectedOperation.label}.`
                : !selectedOperation && file
                  ? `Picking the matching mode for ${extension ? `.${extension}` : "this file"}.`
                  : "Choose a file first. The matching mode is selected for its extension."}
        </p>
      )}

      {phase !== "idle" ? <PhaseRail phase={phase} /> : null}

      {phase === "uploading" ? (
        <div className="progress-wrap" aria-live="polite">
          <div
            className="progress-track"
            role="progressbar"
            aria-label="Upload progress"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
          >
            <div
              className="progress-fill"
              style={{ transform: `scaleX(${progress / 100})` }}
            />
          </div>
          <span className="progress-label caption-4">{progress}% uploaded</span>
        </div>
      ) : null}

      {error ? (
        <p className="alert" role="alert">
          <WarningCircle size={18} weight="bold" aria-hidden="true" />
          <span>{error}</span>
        </p>
      ) : null}

      {currentUser?.isGuest ? (
        <p className="guest-note upload-guest-note caption-5">
          Guest session. Sign in when you are ready to download the result.
        </p>
      ) : null}

      <div className="upload-actions">
        <button
          type="button"
          className="btn btn-primary btn-large"
          onClick={convert}
          disabled={!canStart}
          aria-busy={busy}
          aria-describedby="convert-hint"
          title={disabledReason || undefined}
        >
          {busy ? <span className="spinner" aria-hidden="true" /> : null}
          {busy ? phaseLabel(phase, progress) : actionLabel(selectedOperation)}
          {!busy && selectedOperation ? (
            <ArrowRight size={18} weight="bold" aria-hidden="true" />
          ) : null}
        </button>
        <div className="upload-actions__copy">
          <p
            className="action-hint caption-5"
            id="convert-hint"
            aria-live="polite"
            data-ready={canStart || undefined}
          >
            {canStart ? <Check size={14} weight="bold" aria-hidden="true" /> : null}
            {actionHint}
          </p>
          <p className="fine-print caption-5">
            One file per run · 25 MB maximum · files expire in 24 hours
          </p>
        </div>
      </div>
    </section>
  );
}
