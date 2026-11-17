"use client";

import { useMemo, type KeyboardEvent } from "react";
import { Check } from "@phosphor-icons/react";

import type { Operation, OperationId } from "@/lib/types";

const FORMATS: Partial<Record<OperationId, [string, string]>> = {
  images_to_pdf: ["IMG", "PDF"],
};

interface Props {
  operations: Operation[];
  value: OperationId | null;
  extension: string | null;
  onChange: (value: OperationId) => void;
}

function formatPair(operation: Operation): [string, string] {
  return (
    FORMATS[operation.id] ?? [
      operation.inputExtensions[0]?.toUpperCase() ?? "",
      operation.outputExtension.toUpperCase(),
    ]
  );
}

export default function OperationPicker({ operations, value, extension, onChange }: Props) {
  const groups = useMemo(() => {
    const visible = extension
      ? operations.filter((operation) => operation.inputExtensions.includes(extension))
      : operations;
    const map = new Map<string, Operation[]>();
    for (const operation of visible) {
      const bucket = map.get(operation.group) ?? [];
      bucket.push(operation);
      map.set(operation.group, bucket);
    }
    return Array.from(map, ([group, items]) => ({ group, items }));
  }, [operations, extension]);

  function moveSelection(event: KeyboardEvent<HTMLButtonElement>) {
    const direction =
      event.key === "ArrowDown" || event.key === "ArrowRight"
        ? 1
        : event.key === "ArrowUp" || event.key === "ArrowLeft"
          ? -1
          : 0;
    if (!direction) return;

    event.preventDefault();
    const root = event.currentTarget.closest(".operation-groups");
    const rows = Array.from(
      root?.querySelectorAll<HTMLButtonElement>(".operation-row:not(:disabled)") ?? [],
    );
    if (rows.length === 0) return;

    const index = rows.indexOf(event.currentTarget);
    const next = rows[(index + direction + rows.length) % rows.length];
    next.focus();
    next.click();
  }

  return (
    <div className="operation-groups" role="radiogroup" aria-label="Conversion mode">
      {groups.map(({ group, items }, groupIndex) => (
        <div
          className="operation-group"
          role="group"
          aria-labelledby={`mode-group-${groupIndex}`}
          key={group}
        >
          <p className="operation-group__label caption-4" id={`mode-group-${groupIndex}`}>
            {group}
          </p>

          <div className="operation-list">
            {items.map((operation, index) => {
              const compatible = !extension || operation.inputExtensions.includes(extension);
              const selected = value === operation.id;
              const [source, target] = formatPair(operation);
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
                  onKeyDown={moveSelection}
                  title={
                    compatible ? operation.description : `Not available for .${extension}`
                  }
                  style={{ animationDelay: `${Math.min(index * 24, 120)}ms` }}
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
        </div>
      ))}
    </div>
  );
}

export function OperationPickerSkeleton() {
  return (
    <div className="operation-skeleton" aria-hidden="true">
      {Array.from({ length: 4 }, (_, index) => (
        <div className="operation-row operation-row--skeleton" key={index}>
          <span className="skeleton skeleton-chip" />
          <span className="operation-main">
            <span className="skeleton skeleton-line skeleton-line--short" />
            <span className="skeleton skeleton-line" />
          </span>
          <span className="skeleton skeleton-dot" />
        </div>
      ))}
    </div>
  );
}
