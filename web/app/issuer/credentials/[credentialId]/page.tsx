"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CredentialPass } from "@/components/credential-pass";
import { ArrowLeftIcon, DotIcon } from "@/components/icons";
import { Notice } from "@/components/notice";
import { PortalShell } from "@/components/portal-shell";
import { api, type ApiError, type CredentialView, type RevocationResult } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { Session } from "@/lib/session";
import { useApi } from "@/lib/use-api";

function RevokePanel({ view, session, onRevoked }: { view: CredentialView; session: Session; onRevoked: () => void }) {
  const [reason, setReason] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  async function revoke() {
    setBusy(true);
    setError(null);
    const response = await api<RevocationResult>(`/credentials/${view.credentialId}/revocations`, {
      method: "POST",
      token: session.token,
      body: { reason: reason.trim() },
    });
    setBusy(false);
    if (response.ok) onRevoked();
    else setError(response.error);
  }

  if (view.status === "revoked") {
    return (
      <aside className="panel">
        <div className="panel__head">
          <h2 className="title">Revoked</h2>
          <p className="small muted">{view.revokedAt ? formatDateTime(view.revokedAt) : null}</p>
        </div>
        <p>
          Reason: <b>{view.revocationReason}</b>
        </p>
        <p className="small muted">
          The revocation is a new registry transaction, so the issuance stays in the history. Every later verification reads
          REVOKED, even if the database row is changed.
        </p>
      </aside>
    );
  }

  return (
    <aside className="panel" aria-labelledby="revoke-title">
      <div className="panel__head">
        <h2 className="title" id="revoke-title">
          Revoke this credential
        </h2>
        <p className="small muted">Only {view.issuer.issuerId}, the original issuer, can do this. The holder is notified.</p>
      </div>
      <label className="field">
        <span className="label">Reason, shown to verifiers</span>
        <textarea
          className="textarea"
          maxLength={200}
          placeholder="Data kelulusan keliru"
          value={reason}
          onChange={(e) => {
            setReason(e.target.value);
            setConfirming(false);
          }}
        />
        <span className="small muted">{reason.length}/200</span>
      </label>
      {!confirming ? (
        <button className="btn btn--secondary btn--block" type="button" disabled={!reason.trim()} onClick={() => setConfirming(true)}>
          Review revocation
        </button>
      ) : (
        <div className="confirm stack" role="region" aria-label="Confirm revocation">
          <p>
            The next verification of <span className="mono">{view.credentialId}</span> will read <b>REVOKED</b>. This cannot be undone.
          </p>
          <p className="small">
            Reason: <b>{reason.trim()}</b>
          </p>
          {error ? <Notice error={error} title="Not revoked." /> : null}
          <div className="row">
            <button className="btn btn--primary" type="button" onClick={revoke} disabled={busy}>
              {busy ? "Writing to the registry" : "Revoke credential"}
            </button>
            <button className="btn btn--secondary" type="button" onClick={() => setConfirming(false)} disabled={busy}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}

function CredentialDetail({ session }: { session: Session }) {
  const { credentialId } = useParams<{ credentialId: string }>();
  const justIssued = useSearchParams().get("issued") === "1";
  const { result, reload } = useApi(() => api<CredentialView>(`/credentials/${credentialId}`, { token: session.token }), `${credentialId}`);
  return (
    <>
      <nav className="crumb" aria-label="Breadcrumb">
        <Link href="/issuer">
          <ArrowLeftIcon />
          Issued credentials
        </Link>
        <b className="mono">{credentialId}</b>
      </nav>
      {justIssued && result.state === "ok" && result.data.status === "active" ? (
        <p className="notice notice--good" role="status" style={{ marginBottom: "var(--s-lg)" }}>
          <DotIcon />
          <span>Issued and anchored on the registry. The holder was notified by (simulated) email.</span>
        </p>
      ) : null}
      {result.state === "loading" ? <div className="skeleton" style={{ height: 520 }} aria-busy="true" /> : null}
      {result.state === "error" ? <Notice error={result.error} title="This credential could not load." /> : null}
      {result.state === "ok" ? (
        <div className="workspace">
          <CredentialPass view={result.data} />
          <RevokePanel view={result.data} session={session} onRevoked={reload} />
        </div>
      ) : null}
    </>
  );
}

export default function IssuerCredentialPage() {
  return (
    <PortalShell portal="issuer">
      {(session) => (
        <Suspense fallback={null}>
          <CredentialDetail session={session} />
        </Suspense>
      )}
    </PortalShell>
  );
}
