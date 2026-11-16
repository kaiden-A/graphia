"use client";

import { useEffect, useRef } from "react";

type Token =
  | { type: "word"; word: string; index: number }
  | { type: "break" };

export default function TaglineReveal({
  lines,
  className = "",
  label = "Graphia in one line",
}: {
  lines: string[];
  className?: string;
  label?: string;
}) {
  const wordRefs = useRef<Array<HTMLSpanElement | null>>([]);

  useEffect(() => {
    const nodes = wordRefs.current.filter((node): node is HTMLSpanElement => node !== null);
    if (!nodes.length) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      nodes.forEach((node) => node.classList.add("is-lit"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-lit");
            observer.unobserve(entry.target);
          }
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.8 },
    );

    nodes.forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, []);

  const tokens: Token[] = [];
  let index = 0;
  lines.forEach((line, lineIndex) => {
    for (const word of line.split(" ")) {
      tokens.push({ type: "word", word, index: index++ });
    }
    if (lineIndex < lines.length - 1) tokens.push({ type: "break" });
  });

  return (
    <section className={`tagline-reveal ${className}`} aria-label={label}>
      <p>
        {tokens.map((token, tokenIndex) =>
          token.type === "break" ? (
            <br key={`break-${tokenIndex}`} />
          ) : (
            <span
              key={`${token.word}-${token.index}`}
              ref={(node) => {
                wordRefs.current[token.index] = node;
              }}
            >
              {token.word}{" "}
            </span>
          ),
        )}
      </p>
    </section>
  );
}
