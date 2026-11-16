"use client";

import { useEffect, useRef } from "react";

const DEFAULT_WORDS = [
  "Drop",
  "a",
  "document.",
  "Pick",
  "a",
  "mode.",
  "Take",
  "a",
  "different",
  "file.",
];

export default function TaglineReveal({
  words = DEFAULT_WORDS,
  className = "",
}: {
  words?: string[];
  className?: string;
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

  return (
    <section className={`tagline-reveal ${className}`} aria-label="How Graphia works">
      <p>
        {words.map((word, index) => (
          <span
            key={`${word}-${index}`}
            ref={(node) => {
              wordRefs.current[index] = node;
            }}
          >
            {word}{" "}
          </span>
        ))}
      </p>
    </section>
  );
}
