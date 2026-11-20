"use client";

import { useParams } from "next/navigation";
import { type FormEvent, useState } from "react";
import { DemoSignIn } from "@/components/demo-accounts";
import { Notice } from "@/components/notice";
import { Pass, type PassCell, SkillChips, VerificationStub } from "@/components/pass";
import { Canopy, TopBar } from "@/components/portal-shell";
import { SkillFitPanel } from "@/components/skill-fit";
import { api, type ApiError, type ApiResult, type VerificationResult } from "@/lib/api";
import { DEMO_GROUPS } from "@/lib/demo";
import { formatDate, middle } from "@/lib/format";
import { type Session, signIn, signOut, useSession } from "@/lib/session";
import { useApi } from "@/lib/use-api";

const VERIFIERS = DEMO_GROUPS.filter((group) => group.role === "Verifier");

const LINK_ERRORS: Record<string, { title: string; body: string }> = {
  SHARE_LINK_NOT_FOUND: {
    title: "This link is not known",
    body: "Check that the whole link was copied. If it was, ask the holder to send a new one.",
  },
  SHARE_LINK_EXPIRED: {
    title: "This link has closed",
    body: "It expired or the holder revoked it. Links are time-limited by design; ask the holder for a new link.",
  },
  REGISTRY_UNAVAILABLE: {
    title: "The registry cannot be read right now",
    body: "Without the registry no result can be given, so none is shown. Try again in a moment.",
  },
};

function verifierCells(verification: VerificationResult): PassCell[] {
  const credential = verification.credential;
  if (!credential) {
    const withheld = { absent: "Withheld" as const };
    return [
      { label: "Program", full: true, ...withheld },
      { label: "Completed", ...withheld },
      { label: "Holder", ...withheld },
      { label: "Pass criteria", full: true, ...withheld },
      { label: "Skills", full: true, ...withheld },
    ];
  }
  const notShared = { absent: "Not shared" as const };
  const shared = [
    credential.program?.title !== undefined && "program.title",
    credential.program?.completedAt !== undefined && "completedAt",
    credential.skills !== undefined && "skills",
    credential.program?.criteria !== undefined && "program.criteria",
    credential.holderDisplayName !== undefined && "holderDisplayName",
  ].filter(Boolean);
  return [
    credential.program?.title ? { label: "Program", value: credential.program.title, full: true } : { label: "Program", full: true, ...notShared },
    credential.program?.completedAt ? { label: "Completed", value: formatDate(credential.program.completedAt) } : { label: "Completed", ...notShared },
    credential.holderDisplayName ? { label: "Holder", value: credential.holderDisplayName } : { label: "Holder", ...notShared },
    credential.program?.criteria
      ? { label: "Pass criteria", value: credential.program.criteria, full: true }
      : { label: "Pass criteria", full: true, ...notShared },
    credential.skills
      ? { label: "Skills, from the issuer's catalog", value: <SkillChips skills={credential.skills} />, full: true }
      : { label: "Skills, from the issuer's catalog", full: true, ...notShared },
    { label: "Shared by the holder", value: <span className="mono">{shared.join(" · ")}</span>, full: true },
  ];
}

function VerifierSignIn({ shareToken, session }: { shareToken: string; session: Session | null }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [withPassword, setWithPassword] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const result = await signIn(username.trim(), password);
    setBusy(false);
    if (!result.ok) setError(result.error);
    else if (result.data.role !== "verifier") {
      signOut();
      setError({ code: "FORBIDDEN_ROLE", message: "Only a verifier account can check a credential.", requestId: "" });
    }
  }

  return (
    <div className="signin">
      <section className="signin__panel" aria-labelledby="verify-lead">
        <div className="stack">
          <h1 className="signin__lead" id="verify-lead">
            A holder shared a credential with you.
          </h1>
          <p>
            Sign in with a free verifier account to check it against the blockchain registry: integrity, issuer, and status, without
            contacting the issuer. You will see only the fields the holder chose to share.
          </p>
          <p className="mono">Link {middle(shareToken, 7, 4)}</p>
        </div>
        <img className="signin__art" src="/art/verifier.webp" alt="" width={340} height={306} />
      </section>
      <section className="panel signin__form" aria-labelledby="verifier-signin">
        <div className="panel__head">
          <h2 className="title" id="verifier-signin">
            Sign in as a verifier
          </h2>
          {session ? (
            <p className="small muted">You are signed in as {session.username}, which is not a verifier account.</p>
          ) : (
            <p className="small muted">Pick a demo verifier. One press signs you in and runs the check.</p>
          )}
        </div>
        {/* Only verifier accounts are listed, so a one-click sign-in always lands on the check. */}
        <DemoSignIn groups={VERIFIERS} action="Sign in and verify" onSignedIn={() => undefined} onOff={() => setWithPassword(true)} />
        <details className="password-signin" open={withPassword} onToggle={(e) => setWithPassword(e.currentTarget.open)}>
          <summary>Sign in with a password</summary>
          <form className="stack" onSubmit={submit} noValidate>
            <label className="field">
              <span className="label">Username</span>
              <input className="input" autoComplete="username" placeholder="verifier.a" value={username} onChange={(e) => setUsername(e.target.value)} />
            </label>
            <label className="field">
              <span className="label">Password</span>
              <input className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </label>
            {error ? <Notice error={error} /> : null}
            <button className="btn btn--secondary btn--block" type="submit" disabled={busy || !username || !password}>
              {busy ? "Signing in" : "Sign in and verify"}
            </button>
          </form>
        </details>
      </section>
    </div>
  );
}

// Each POST creates a verification record, so one page view sends it once even when React runs
// the effect twice (StrictMode); "Try again" clears the entry to send a new one.
const runs = new Map<string, Promise<ApiResult<VerificationResult>>>();

function Verification({ shareToken, session }: { shareToken: string; session: Session }) {
  const key = `${shareToken}:${session.token}`;
  const { result, reload } = useApi(() => {
    const pending = runs.get(key) ?? api<VerificationResult>("/verifications", { method: "POST", token: session.token, body: { shareToken } });
    runs.set(key, pending);
    return pending;
  }, key);
  const retry = () => {
    runs.delete(key);
    reload();
  };

  if (result.state === "loading") {
    return (
      <div className="workspace" aria-busy="true">
        <div className="skeleton" style={{ height: 600 }} />
        <div className="skeleton" style={{ height: 600 }} />
      </div>
    );
  }
  if (result.state === "error") {
    const known = LINK_ERRORS[result.error.code];
    return (
      <div className="empty" style={{ maxWidth: 720, marginInline: "auto" }}>
        <img src={`/art/${result.error.code === "REGISTRY_UNAVAILABLE" ? "chain" : "closed"}.webp`} alt="" width={132} height={99} />
        <h1 className="title">{known?.title ?? "The credential could not be checked"}</h1>
        <p className="prose">{known?.body ?? result.error.message}</p>
        <p className="mono muted">
          {result.error.code}
          {result.error.requestId ? ` · ${result.error.requestId}` : ""}
        </p>
        {result.error.code === "REGISTRY_UNAVAILABLE" || result.error.code === "NETWORK_ERROR" ? (
          <button className="btn btn--secondary" type="button" onClick={retry}>
            Try again
          </button>
        ) : null}
      </div>
    );
  }

  const verification = result.data;
  const credential = verification.credential;
  return (
    <>
      <p className="crumb">
        <span>
          Verification <b className="mono">{verification.verificationId}</b>, opened from share link{" "}
          <span className="mono">{middle(shareToken, 7, 4)}</span>
        </span>
      </p>
      <div className="workspace">
        <Pass
          issuerId={credential?.issuer.issuerId ?? "Withheld"}
          issuerName={credential?.issuer.name ?? "Issuer details withheld"}
          credentialId={credential?.credentialId ?? "Withheld"}
          credentialSub={`Checked against the registry`}
          cells={verifierCells(verification)}
          cleared={verification.result === "VALID"}
          stub={<VerificationStub verification={verification} />}
        />
        <SkillFitPanel verification={verification} token={session.token} />
      </div>
    </>
  );
}

export default function VerifyPage() {
  const { shareToken } = useParams<{ shareToken: string }>();
  const session = useSession();
  const verifier = session?.role === "verifier";
  return (
    <div className={verifier ? "portal" : undefined}>
      {verifier ? <Canopy /> : null}
      <TopBar portal="verifier" session={session} />
      <main className="page">
        {session === undefined ? <div className="skeleton" style={{ height: 320 }} aria-busy="true" /> : null}
        {session !== undefined && session?.role !== "verifier" ? <VerifierSignIn shareToken={shareToken} session={session} /> : null}
        {session?.role === "verifier" ? <Verification shareToken={shareToken} session={session} /> : null}
      </main>
    </div>
  );
}
