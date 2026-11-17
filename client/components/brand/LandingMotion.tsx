"use client";

import { useEffect } from "react";

/**
 * Arms the landing page for scroll reveals without hiding content when
 * JavaScript or IntersectionObserver is unavailable.
 */
export default function LandingMotion() {
  useEffect(() => {
    if (!("IntersectionObserver" in window)) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const targets = Array.from(
      document.querySelectorAll<HTMLElement>("[data-reveal], [data-reveal-stagger]"),
    );
    if (targets.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );

    const viewportEdge = window.innerHeight * 0.92;

    for (const target of targets) {
      const rect = target.getBoundingClientRect();
      const alreadyVisible = rect.top < viewportEdge && rect.bottom > 0;

      if (alreadyVisible) {
        target.classList.add("is-revealed");
        continue;
      }

      target.classList.add("is-armed");
      observer.observe(target);
    }

    return () => observer.disconnect();
  }, []);

  return null;
}
