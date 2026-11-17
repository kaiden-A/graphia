"use client";

import Link from "next/link";
import { useMemo } from "react";
import { ArrowRight, ArrowUp } from "@phosphor-icons/react";

import type { Operation } from "@/lib/types";
import { useOperations } from "@/lib/useOperations";

const GROUP_NOTES: Record<string, string> = {
  "Make a PDF": "Send a document, deck, workbook, or image and collect a PDF.",
  "Read a PDF": "Pull the selectable text out of a PDF.",
  "PDF tools": "Change a PDF without changing what it says.",
  "Make Markdown": "Turn a document into text you can edit anywhere.",
};

function formatPair(operation: Operation): [string, string] {
  const source =
    operation.id === "images_to_pdf"
      ? "IMG"
      : operation.inputExtensions[0]?.toUpperCase() ?? "";
  return [source, operation.outputExtension.toUpperCase()];
}

function LibrarySkeleton() {
  return (
    <div className="library-skeleton" aria-hidden="true">
      {[0, 1, 2].map((group) => (
        <div className="library-skeleton__group" key={group}>
          <div className="skeleton skeleton-line skeleton-line--short" />
          {[0, 1].map((row) => (
            <div className="library-row library-row--skeleton" key={row}>
              <span className="skeleton skeleton-chip" />
              <span className="library-main">
                <span className="skeleton skeleton-line skeleton-line--short" />
                <span className="skeleton skeleton-line" />
              </span>
              <span className="skeleton skeleton-line skeleton-line--short" />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function LibraryBrowser() {
  const { operations, error, loading, reload } = useOperations();

  const groups = useMemo(() => {
    const map = new Map<string, Operation[]>();
    for (const operation of operations) {
      const bucket = map.get(operation.group) ?? [];
      bucket.push(operation);
      map.set(operation.group, bucket);
    }
    return Array.from(map, ([group, items]) => ({ group, items }));
  }, [operations]);

  return (
    <>
      <section className="library-intro" aria-labelledby="library-title">
        <div className="library-intro__copy">
          <p className="eyebrow caption-3">Library</p>
          <h1 id="library-title" className="heading-2">
            Every mode in one place.
          </h1>
          <p className="body-2">
            Pick a mode to open the converter with it selected. If you are not sure, drop a
            file on the converter and the matching mode is chosen for its extension.
          </p>
          <p className="library-count caption-4" aria-live="polite">
            {loading
              ? "Loading the mode list."
              : error
                ? "The mode list is unavailable."
                : `${operations.length} modes in ${groups.length} ${
                    groups.length === 1 ? "group" : "groups"
                  }.`}
          </p>
          <p className="library-guest-note caption-5">
            Guest runs can convert. Sign in when you are ready to download.
          </p>
        </div>

        <div className="library-intro__actions">
          <Link className="btn btn-primary btn-large" href="/convert#upload-panel">
            Drop a file instead
            <ArrowUp size={18} weight="bold" aria-hidden="true" />
          </Link>
          <Link className="text-link caption-5" href="/convert">
            Open the converter
          </Link>
        </div>
      </section>

      <div className="library-sections" aria-busy={loading}>
        {loading ? (
          <div>
            <span className="visually-hidden" role="status">
              Loading the mode library.
            </span>
            <LibrarySkeleton />
          </div>
        ) : null}

        {!loading && error ? (
          <div className="library-state" role="alert">
            <h2 className="heading-5">The modes did not load.</h2>
            <p className="body-5">{error}</p>
            <button type="button" className="btn btn-ghost" onClick={reload}>
              Try again
            </button>
          </div>
        ) : null}

        {!loading && !error && groups.length === 0 ? (
          <div className="library-state">
            <h2 className="heading-5">No modes are available right now.</h2>
            <p className="body-5">Try again in a moment, or open the converter directly.</p>
            <button type="button" className="btn btn-ghost" onClick={reload}>
              Try again
            </button>
          </div>
        ) : null}

        {!loading && !error
          ? groups.map(({ group, items }, groupIndex) => (
              <section
                className="library-group"
                key={group}
                aria-labelledby={`library-group-${groupIndex}`}
              >
                <div className="library-group__head">
                  <div>
                    <h2 className="heading-5" id={`library-group-${groupIndex}`}>
                      {group}
                    </h2>
                    <p className="body-5">
                      {GROUP_NOTES[group] ?? "One job per mode."}
                    </p>
                  </div>
                  <span className="caption-5">
                    {items.length} {items.length === 1 ? "mode" : "modes"}
                  </span>
                </div>

                <div className="library-list">
                  {items.map((operation, index) => {
                    const [source, target] = formatPair(operation);
                    return (
                      <Link
                        className="library-row"
                        href={`/convert?operation=${operation.id}#upload-panel`}
                        key={operation.id}
                        style={{ animationDelay: `${Math.min(index * 28, 168)}ms` }}
                      >
                        <span className="library-pair">
                          <span className="format-code caption-3">{source}</span>
                          <span className="format-arrow" aria-hidden="true">
                            →
                          </span>
                          <span className="format-code format-code--out caption-3">
                            {target}
                          </span>
                        </span>

                        <span className="library-main">
                          <span className="library-name title-2">{operation.label}</span>
                          <span className="library-note body-5">
                            {operation.description}
                          </span>
                        </span>

                        <span className="library-inputs caption-5">
                          {operation.inputExtensions.map((ext) => `.${ext}`).join(" ")}
                        </span>

                        <span className="library-go caption-1">
                          Use this mode
                          <ArrowRight size={16} weight="bold" aria-hidden="true" />
                        </span>
                      </Link>
                    );
                  })}
                </div>
              </section>
            ))
          : null}
      </div>
    </>
  );
}
