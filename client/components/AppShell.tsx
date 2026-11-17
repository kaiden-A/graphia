"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";

import Logo from "@/components/brand/Logo";
import { ApiError, apiJson } from "@/lib/api-client";
import type { LogoutResponse, User } from "@/lib/types";

const CurrentUserContext = createContext<User | null>(null);

export function useCurrentUser(): User | null {
  return useContext(CurrentUserContext);
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [authFailed, setAuthFailed] = useState(false);
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
          return;
        }
        setAuthFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  function goToSignIn() {
    const next = `${window.location.pathname}${window.location.search}`;
    router.push(`/login?next=${encodeURIComponent(next)}`);
  }

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
    <CurrentUserContext.Provider value={user}>
      <div className="app">
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>

        <header className="app-nav">
          <div className="app-nav-inner">
            <Link className="brand-link" href="/convert" aria-label="Graphia converter">
              <Logo size={30} />
            </Link>

            <nav className="app-nav-links" aria-label="Primary">
              <Link
                className={
                  pathname === "/convert" || pathname.startsWith("/conversions")
                    ? "nav-link is-active"
                    : "nav-link"
                }
                href="/convert"
              >
                Converter
              </Link>
              <Link
                className={pathname === "/library" ? "nav-link is-active" : "nav-link"}
                href="/library"
              >
                Library
              </Link>
              <Link className="nav-link" href="/">
                About
              </Link>
            </nav>

            <div className="app-nav-user">
              {user ? (
                user.isGuest ? (
                  <div className="guest-session">
                    <span className="guest-session__badge caption-4">
                      <span className="guest-session__dot" aria-hidden="true" />
                      Guest session
                    </span>
                    <button
                      className="btn btn-primary btn-small"
                      onClick={goToSignIn}
                      aria-label="Sign in to keep files and download results"
                    >
                      Sign in
                    </button>
                  </div>
                ) : (
                  <>
                    <span className="nav-user caption-4" title={user.email}>
                      {user.name || user.email}
                    </span>
                    <button
                      className="btn btn-ghost btn-small"
                      onClick={logout}
                      disabled={loggingOut}
                    >
                      {loggingOut ? "Signing out…" : "Sign out"}
                    </button>
                  </>
                )
              ) : authFailed ? (
                <button className="btn btn-ghost btn-small" onClick={goToSignIn}>
                  Sign in
                </button>
              ) : (
                <span className="nav-user caption-4" aria-live="polite">
                  Checking session…
                </span>
              )}
            </div>
          </div>
        </header>

        <main className="app-main" id="main-content">
          {children}
        </main>

        <footer className="app-footer">
          <div className="app-footer-inner caption-5">
            <span>Graphia / Document atelier</span>
            <span className="app-footer-links">
              <Link href="/privacy">Privacy</Link>
              <Link href="/terms">Terms</Link>
            </span>
            <span>Files expire in 24 hours</span>
          </div>
        </footer>
      </div>
    </CurrentUserContext.Provider>
  );
}
