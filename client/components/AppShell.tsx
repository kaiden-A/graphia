"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { MeanderRule } from "@/components/scrapbook/Ornaments";
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
    <div className="site-shell">
      <div className="folio">
        <header className="topbar">
          <Link className="brand" href="/" aria-label="Graphia home">
            <span className="brand-mark">G</span>
            <span className="brand-lockup">
              <span className="brand-word">Graphia</span>
              <span className="brand-sub">document expeditions</span>
            </span>
          </Link>

          <nav className="topnav" aria-label="Primary">
            <Link className={pathname === "/" ? "nav-link is-active" : "nav-link"} href="/">
              The desk
            </Link>
            <span className="nav-sep" aria-hidden="true" />
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
        </header>

        <MeanderRule className="folio-meander" />
        <main className="page">{children}</main>

        <footer className="footer">
          <span className="footer-mark">Graphia</span>
          <span className="footer-rule" aria-hidden="true" />
          <span className="muted">Documents out, a little further than they came.</span>
        </footer>
      </div>
    </div>
  );
}
