"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, Suspense, useEffect, useRef, useState } from "react";
import { FieldError, Notice } from "@/components/notice";
import { TopBar } from "@/components/portal-shell";
import type { ApiError } from "@/lib/api";
import { DEMO_GROUPS } from "@/lib/demo";
import { HOME_BY_ROLE, signIn, useSession } from "@/lib/session";

function SignIn() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next");
  const session = useSession();
  const [username, setUsername] = useState(params.get("u") ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const passwordRef = useRef<HTMLInputElement>(null);

  // A demo account picked on the landing page arrives as ?u=…: only the password is left to type.
  useEffect(() => {
    if (params.get("u")) passwordRef.current?.focus();
  }, [params]);

  function pick(name: string) {
    setUsername(name);
    setError(null);
    passwordRef.current?.focus();
  }

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
    // Next keeps a visited route's state alive in a hidden tree, so never leave the password in it.
    setPassword("");
    const home = HOME_BY_ROLE[result.data.role];
    router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : home);
  }

  const invalid = error?.code === "INVALID_CREDENTIALS";
  return (
    <>
      <TopBar session={session} />
      <main className="page">
        <div className="signin">
          <section className="signin__panel" aria-labelledby="signin-lead">
            <div className="stack">
              <h1 className="signin__lead" id="signin-lead">
                One sign-in.
                <br />
                Your role opens the right door.
              </h1>
              <p>Issuers issue and revoke. Holders share. Verifiers check, then read skill fit. Every account here is synthetic.</p>
            </div>
            <img className="signin__art" src="/art/certificate.webp" alt="" width={340} height={347} />
          </section>

          <section className="panel signin__form" aria-labelledby="signin-title">
            <div className="panel__head">
              <h2 className="title" id="signin-title">
                Sign in
              </h2>
              <p className="small muted">Pick a demo account, then enter the shared demo password.</p>
            </div>

            {session && session.role !== "platform_admin" ? (
              <p className="notice notice--good" role="status">
                <span>
                  You are already signed in as <b>{session.username}</b>.{" "}
                  <Link href={HOME_BY_ROLE[session.role]}>Open your portal</Link>
                </span>
              </p>
            ) : null}
            {session?.role === "platform_admin" ? (
              <p className="small">
                <span className="mono">platform_admin</span> has no portal. It registers issuers through API-01 in the{" "}
                <a href="/api/v1/docs">API docs</a>.
              </p>
            ) : null}

            <div className="accounts" role="group" aria-label="Demo accounts">
              {DEMO_GROUPS.map((group) => (
                <div key={group.role} className="accounts__group">
                  <img src={`/art/${group.art}.webp`} alt="" width={40} height={40} />
                  <div>
                    <div className="label" style={{ marginBottom: 6 }}>
                      {group.role}
                    </div>
                    <div className="accounts__chips">
                      {group.accounts.map((account) => (
                        <button
                          key={account.username}
                          type="button"
                          className="account-chip"
                          aria-pressed={username === account.username}
                          onClick={() => pick(account.username)}
                        >
                          <span className="mono">{account.username}</span>
                          <span className="small">{account.note}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <hr className="panel__divider" />

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
                  ref={passwordRef}
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

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignIn />
    </Suspense>
  );
}
