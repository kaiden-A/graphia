"use client";

import { Lightning } from "@phosphor-icons/react";

import type { Operation, OperationId } from "@/lib/types";

const FORMATS: Record<OperationId, [string, string]> = {
  docx_to_pdf: ["DOCX", "PDF"],
  pdf_to_markdown: ["PDF", "MD"],
  txt_to_markdown: ["TXT", "MD"],
  markdown_to_pdf: ["MD", "PDF"],
  images_to_pdf: ["IMG", "PDF"],
};

interface Props {
  operations: Operation[];
  value: OperationId | null;
  extension: string | null;
  onChange: (value: OperationId) => void;
}

export default function OperationPicker({ operations, value, extension, onChange }: Props) {
  return (
    <div className="operation-grid" role="radiogroup" aria-label="Conversion mode">
      {operations.map((operation) => {
        const compatible = !extension || operation.inputExtensions.includes(extension);
        const selected = value === operation.id;
        const [source, target] = FORMATS[operation.id];
        return (
          <button
            key={operation.id}
            type="button"
            role="radio"
            aria-checked={selected}
            className="operation-card"
            data-selected={selected || undefined}
            data-disabled={!compatible || undefined}
            disabled={!compatible}
            onClick={() => onChange(operation.id)}
            title={compatible ? operation.description : `Not available for .${extension}`}
          >
            <span className="operation-top">
              <span className="format-pair">
                <span className="format-chip">{source}</span>
                <Lightning className="format-arrow" size={16} weight="bold" aria-hidden="true" />
                <span className="format-chip format-chip--target">{target}</span>
              </span>
              <span className="operation-name">{operation.label}</span>
            </span>
            <span className="operation-meta">
              {operation.inputExtensions.map((item) => `.${item}`).join(" · ")}
            </span>
            {!compatible ? (
              <span className="operation-note">Not for .{extension}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
