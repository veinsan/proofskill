"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, Suspense, useState } from "react";
import { FieldError, Notice } from "@/components/notice";
import { TopBar } from "@/components/portal-shell";
import type { ApiError } from "@/lib/api";
import { HOME_BY_ROLE, signIn, useSession } from "@/lib/session";

// Seeded synthetic accounts (api/app/seed.py), listed so a demo can switch roles quickly.
const DEMO_ACCOUNTS = [
  { username: "admin.iss001", role: "Issuer admin, ISS-001" },
  { username: "admin.iss002", role: "Issuer admin, ISS-002" },
  { username: "holder.a", role: "Holder, HLD-2026-0007" },
  { username: "holder.b", role: "Holder, HLD-2026-0008" },
  { username: "verifier.a", role: "Verifier" },
  { username: "verifier.b", role: "Verifier" },
];

function SignIn() {
  const router = useRouter();
  const next = useSearchParams().get("next");
  const session = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const result = await signIn(username.trim(), password);
    setBusy(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    const home = HOME_BY_ROLE[result.data.role];
    router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : home);
  }

  const invalid = error?.code === "INVALID_CREDENTIALS";
  return (
    <>
      <TopBar session={session} />
      <main className="page">
        <div className="signin">
          <section className="stack">
            <h1 className="signin__lead">Check a training credential at the gate.</h1>
            <p className="prose muted">
              Issuers anchor each credential on a blockchain registry on the Base Sepolia testnet. Holders share a scoped link. Verifiers confirm integrity,
              issuer, and status without contacting an admin, then read a skill-fit recommendation for the position they are filling.
            </p>
            <div>
              <h2 className="label" style={{ marginBottom: 10 }}>
                Demo accounts, all synthetic
              </h2>
              <div className="accounts">
                {DEMO_ACCOUNTS.map((account) => (
                  <button key={account.username} type="button" onClick={() => setUsername(account.username)}>
                    <span className="mono">{account.username}</span>
                    <span className="small muted">{account.role}</span>
                  </button>
                ))}
              </div>
              <p className="small muted" style={{ marginTop: 10 }}>
                Every demo account shares one password, which the ProofSkill team gives out for demos.
              </p>
            </div>
          </section>

          <section className="panel" aria-labelledby="signin-title">
            <div className="panel__head">
              <h2 className="title" id="signin-title">
                Sign in
              </h2>
              <p className="small muted">Your role decides which portal opens.</p>
            </div>
            {session?.role === "platform_admin" ? (
              <p className="small">
                <span className="mono">platform_admin</span> has no portal. It registers issuers through API-01 in the{" "}
                <a href="/api/v1/docs">API docs</a>.
              </p>
            ) : null}
            <form className="stack" onSubmit={submit} noValidate>
              <label className="field">
                <span className="label">Username</span>
                <input
                  className="input"
                  name="username"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  aria-invalid={invalid || undefined}
                  required
                />
              </label>
              <label className="field">
                <span className="label">Password</span>
                <input
                  className="input"
                  type="password"
                  name="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  aria-invalid={invalid || undefined}
                  aria-describedby={invalid ? "signin-error" : undefined}
                  required
                />
              </label>
              {invalid ? (
                <FieldError id="signin-error" message="The username or password is wrong." code="INVALID_CREDENTIALS" />
              ) : error ? (
                <Notice error={error} />
              ) : null}
              <button className="btn btn--primary btn--block" type="submit" disabled={busy || !username || !password}>
                {busy ? "Signing in" : "Sign in"}
              </button>
            </form>
          </section>
        </div>
      </main>
    </>
  );
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SignIn />
    </Suspense>
  );
}
