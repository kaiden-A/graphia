"use client";

import { useRef, useState } from "react";

interface Props {
  accept: string;
  disabled?: boolean;
  onFile: (file: File) => void;
}

export default function UploadDropzone({ accept, disabled, onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function openPicker() {
    if (!disabled) inputRef.current?.click();
  }

  function pick(fileList: FileList | null) {
    const file = fileList?.[0];
    if (file) onFile(file);
  }

  return (
    <div
      className="dropzone"
      data-dragging={dragging || undefined}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onClick={openPicker}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openPicker();
        }
      }}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        if (!disabled) pick(event.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        className="visually-hidden"
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={(event) => {
          pick(event.target.files);
          event.target.value = "";
        }}
      />
      <span className="dropzone-icon" aria-hidden="true">
        <svg viewBox="0 0 32 32" fill="none">
          <path d="M8 4h10l6 6v18H8V4Z" stroke="currentColor" strokeWidth="1.5" />
          <path d="M18 4v6h6" stroke="currentColor" strokeWidth="1.5" />
          <path d="M16 14v8m0-8-3 3m3-3 3 3" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </span>
      <span className="dropzone-title">
        {dragging ? "Drop it here" : "Drop a document here"}
      </span>
      <span className="dropzone-sub">or click to browse · 25 MB maximum</span>
    </div>
  );
}
