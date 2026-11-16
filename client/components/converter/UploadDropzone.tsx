"use client";

import { useRef, useState } from "react";

import { Drop } from "@phosphor-icons/react";

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
      <Drop className="dropzone-icon" size={44} weight="bold" aria-hidden="true" />
      <span className="dropzone-title">
        {dragging ? "Let it drop" : "Drop a file into the pool"}
      </span>
      <span className="dropzone-sub">or choose from the locker · 25 MB maximum</span>
    </div>
  );
}
