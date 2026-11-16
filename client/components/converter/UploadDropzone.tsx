"use client";

import { useRef, useState } from "react";

import { ScrollIcon } from "@/components/scrapbook/icons";

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
      <ScrollIcon className="dropzone-icon" />
      <span className="dropzone-title">
        {dragging ? "Set it down here" : "Drop a document here"}
      </span>
      <span className="dropzone-sub">or choose a file · 25 MB maximum</span>
    </div>
  );
}
