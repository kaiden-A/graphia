"use client";

import { Check } from "@phosphor-icons/react";

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
    <div className="operation-list" role="radiogroup" aria-label="Conversion mode">
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
            className="operation-row"
            data-selected={selected || undefined}
            data-disabled={!compatible || undefined}
            disabled={!compatible}
            onClick={() => onChange(operation.id)}
            title={compatible ? operation.description : `Not available for .${extension}`}
          >
            <span className="operation-pair">
              <span className="format-code caption-3">{source}</span>
              <span className="operation-arrow" aria-hidden="true">
                →
              </span>
              <span className="format-code format-code--out caption-3">{target}</span>
            </span>

            <span className="operation-main">
              <span className="operation-name title-3">{operation.label}</span>
              <span className="operation-meta caption-5">
                {compatible
                  ? operation.description
                  : `Not available for .${extension} files`}
              </span>
            </span>

            <span className="operation-check" aria-hidden="true">
              {selected ? <Check size={14} weight="bold" /> : null}
            </span>
          </button>
        );
      })}
    </div>
  );
}
