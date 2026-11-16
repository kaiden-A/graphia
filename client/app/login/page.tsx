import { Suspense } from "react";

import LoginForm from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <section className="auth-layout">
          <div className="auth-copy">
            <p className="eyebrow">Loading</p>
            <h1 className="auth-display">Opening the desk…</h1>
          </div>
        </section>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
