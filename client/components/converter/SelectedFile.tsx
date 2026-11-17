"use client";

import { fileExtension, formatBytes } from "@/lib/files";

interface Props {
  file: File;
  disabled?: boolean;
  onRemove: () => void;
}

export default function SelectedFile({ file, disabled, onRemove }: Props) {
  const extension = fileExtension(file.name).toUpperCase() || "FILE";
  return (
    <div className="file-row">
      <span className="file-badge" aria-hidden="true">
        {extension.slice(0, 4)}
      </span>
      <span className="file-main">
        <span className="file-name" title={file.name}>
          {file.name}
        </span>
        <span className="file-meta">
          {formatBytes(file.size)} · {extension}
        </span>
      </span>
      <button
        type="button"
        className="btn btn-ghost btn-small"
        onClick={onRemove}
        disabled={disabled}
        aria-label={`Remove ${file.name}`}
      >
        Remove
      </button>
    </div>
  );
}
