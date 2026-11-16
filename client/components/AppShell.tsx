"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { MarqueeBulbs } from "@/components/arcade/ArcadeBits";
import { ApiError, apiJson } from "@/lib/api-client";
import type { LogoutResponse, User } from "@/lib/types";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiJson<User>("/api/auth/me")
      .then((data) => {
        if (!cancelled) setUser(data);
      })
      .catch((error) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 401) {
          const next = `${window.location.pathname}${window.location.search}`;
          router.replace(`/login?next=${encodeURIComponent(next)}`);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function logout() {
    setLoggingOut(true);
    try {
      const result = await apiJson<LogoutResponse>("/api/auth/logout", {
        method: "POST",
      });
      if (result.logoutUrl) {
        window.location.assign(result.logoutUrl);
        return;
      }
    } catch {
      // The local session may already be gone; still move to the sign-in page.
    }
    router.replace("/login");
    router.refresh();
  }

  return (
    <div className="arcade-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <div className="cabinet">
        <header className="marquee-bar">
          <Link className="brand" href="/convert" aria-label="Graphia converter">
            <span className="brand-badge">G</span>
            <span className="brand-lockup">
              <span className="brand-name">Graphia</span>
              <span className="brand-tag">Document arcade</span>
            </span>
          </Link>

          <nav className="topnav" aria-label="Primary">
            <Link
              className={
                pathname === "/convert" || pathname.startsWith("/conversions")
                  ? "nav-link is-active"
                  : "nav-link"
              }
              href="/convert"
            >
              The floor
            </Link>
            <span className="nav-divider" aria-hidden="true" />
            {user ? (
              <>
                <span className="nav-user" title={user.email}>
                  {user.name || user.email}
                </span>
                <button className="btn btn-ghost btn-small" onClick={logout} disabled={loggingOut}>
                  {loggingOut ? "Signing out…" : "Sign out"}
                </button>
              </>
            ) : (
              <span className="nav-user muted">…</span>
            )}
          </nav>
          <MarqueeBulbs />
        </header>

        <main className="page" id="main-content">
          {children}
        </main>

        <footer className="cabinet-footer">
          <span className="footer-brand">Graphia</span>
          <span className="footer-separator" aria-hidden="true">
            /
          </span>
          <span>Open all night. Files leave at closing.</span>
          <span className="footer-legal">
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
          </span>
          <span className="footer-leds" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
        </footer>
      </div>
    </div>
  );
}
