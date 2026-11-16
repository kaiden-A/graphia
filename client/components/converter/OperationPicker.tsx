"use client";

import {
  AmphoraIcon,
  QuillIcon,
  ScrollIcon,
  TabletIcon,
  TempleIcon,
} from "@/components/scrapbook/icons";
import type { Operation, OperationId } from "@/lib/types";

const GLYPHS = {
  docx_to_pdf: ScrollIcon,
  pdf_to_markdown: TabletIcon,
  txt_to_markdown: QuillIcon,
  markdown_to_pdf: TempleIcon,
  images_to_pdf: AmphoraIcon,
} as const;

interface Props {
  operations: Operation[];
  value: OperationId | null;
  extension: string | null;
  onChange: (value: OperationId) => void;
}

export default function OperationPicker({ operations, value, extension, onChange }: Props) {
  return (
    <div className="operation-grid" role="radiogroup" aria-label="Conversion operation">
      {operations.map((operation) => {
        const compatible = !extension || operation.inputExtensions.includes(extension);
        const selected = value === operation.id;
        const Glyph = GLYPHS[operation.id];
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
              <Glyph className="operation-icon" />
              <span className="operation-name">{operation.label}</span>
            </span>
            <span className="operation-meta">
              {operation.inputExtensions.map((item) => `.${item}`).join(" · ")}
              <span className="operation-arrow" aria-hidden="true">
                →
              </span>
              <span className="mono">.{operation.outputExtension}</span>
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
