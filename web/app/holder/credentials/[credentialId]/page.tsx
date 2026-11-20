"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { CopyButton } from "@/components/copy-button";
import { CredentialPass } from "@/components/credential-pass";
import { ArrowLeftIcon } from "@/components/icons";
import { Notice } from "@/components/notice";
import { PortalShell } from "@/components/portal-shell";
import { ShareQr } from "@/components/share-qr";
import { api, type ApiError, type CredentialView, SCOPE_FIELDS, type ScopeField, type ShareLink, type ShareLinkSummary } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { Session } from "@/lib/session";
import { useApi } from "@/lib/use-api";

const EXPIRY = [
  { hours: 24, label: "1 day" },
  { hours: 72, label: "3 days" },
  { hours: 168, label: "7 days" },
  { hours: 720, label: "30 days (maximum)" },
];

const SCOPE_LABEL = Object.fromEntries(SCOPE_FIELDS.map((s) => [s.field, s.label])) as Record<ScopeField, string>;

function linkState(link: ShareLinkSummary): string {
  if (link.revokedAt) return `Revoked ${formatDateTime(link.revokedAt)}`;
  if (new Date(link.expiresAt) <= new Date()) return `Expired ${formatDateTime(link.expiresAt)}`;
  return `Expires ${formatDateTime(link.expiresAt)}`;
}

function SharePanel({ view, session, onChange }: { view: CredentialView; session: Session; onChange: () => void }) {
  const [scope, setScope] = useState<ScopeField[]>(["program.title", "completedAt", "skills"]);
  const [hours, setHours] = useState(72);
  const [created, setCreated] = useState<ShareLink | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const createdRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (created) createdRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [created]);

  function toggle(field: ScopeField) {
    setScope((current) => (current.includes(field) ? current.filter((f) => f !== field) : [...current, field]));
  }

  async function create() {
    setBusy(true);
    setError(null);
    const response = await api<ShareLink>(`/credentials/${view.credentialId}/share-links`, {
      method: "POST",
      token: session.token,
      body: { scope, expiresInHours: hours },
    });
    setBusy(false);
    if (response.ok) {
      setCreated(response.data);
      onChange();
    } else setError(response.error);
  }

  async function revoke(linkId: string) {
    const response = await api<void>(`/share-links/${linkId}`, { method: "DELETE", token: session.token });
    if (response.ok) {
      if (created?.linkId === linkId) setCreated(null);
      onChange();
    } else setError(response.error);
  }

  const links = view.shareLinks ?? [];
  return (
    <aside className="panel" aria-labelledby="share-title">
      <div className="panel__head">
        <h2 className="title" id="share-title">
          Share with a verifier
        </h2>
        <p className="small muted">The verifier sees only what you tick, until the link expires. The scope stays on the server.</p>
      </div>
      {view.status === "revoked" ? (
        <p className="small">This credential is revoked. A verifier who opens a link will see REVOKED with the issuer&apos;s reason.</p>
      ) : null}
      <fieldset className="checks-list">
        <legend className="label" style={{ marginBottom: 8 }}>
          Fields to share
        </legend>
        {SCOPE_FIELDS.map(({ field, label }) => (
          <label key={field} className="check-option">
            <input type="checkbox" checked={scope.includes(field)} onChange={() => toggle(field)} />
            <span>
              {label} <span className="mono muted">{field}</span>
            </span>
          </label>
        ))}
      </fieldset>
      <label className="field">
        <span className="label">Link lifetime</span>
        <select className="select" value={hours} onChange={(e) => setHours(Number(e.target.value))}>
          {EXPIRY.map((option) => (
            <option key={option.hours} value={option.hours}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      {error ? <Notice error={error} title="Not shared." /> : null}
      <button className="btn btn--primary btn--block" type="button" onClick={create} disabled={busy || scope.length === 0}>
        {busy ? "Creating link" : created ? "Create another link" : "Create share link"}
      </button>

      {created ? (
        <div ref={createdRef} className="share-result" aria-live="polite">
          <ShareQr url={created.url} linkId={created.linkId} />
          <div className="stack" style={{ gap: "var(--s-sm)" }}>
            <div className="label">
              {created.linkId} · expires {formatDateTime(created.expiresAt)}
            </div>
            <div className="url-box">{created.url}</div>
            <div className="row">
              <CopyButton value={created.url} label="Copy link" />
            </div>
            <p className="small muted">Fits LinkedIn&apos;s Credential URL field. Shares: {created.scope.map((f) => SCOPE_LABEL[f]).join(", ")}.</p>
          </div>
        </div>
      ) : null}

      {links.length > 0 ? (
        <div>
          <div className="label">Your links</div>
          {links.map((link) => {
            const open = !link.revokedAt && new Date(link.expiresAt) > new Date();
            return (
              <div key={link.linkId} className="link-row">
                <div>
                  <span className="mono">{link.linkId}</span>
                  <div className="small muted">
                    {link.scope.map((f) => SCOPE_LABEL[f]).join(", ")}. {linkState(link)}.
                  </div>
                </div>
                {open ? (
                  <div className="row">
                    <CopyButton value={link.url} label="Copy" className="btn btn--quiet" />
                    <button className="btn btn--quiet" type="button" onClick={() => revoke(link.linkId)}>
                      Revoke
                    </button>
                  </div>
                ) : (
                  <span className="state">closed</span>
                )}
              </div>
            );
          })}
        </div>
      ) : null}
    </aside>
  );
}

function HolderCredential({ session }: { session: Session }) {
  const { credentialId } = useParams<{ credentialId: string }>();
  const { result, reload } = useApi(() => api<CredentialView>(`/credentials/${credentialId}`, { token: session.token }), credentialId);
  return (
    <>
      <nav className="crumb" aria-label="Breadcrumb">
        <Link href="/holder">
          <ArrowLeftIcon />
          My credentials
        </Link>
        <b className="mono">{credentialId}</b>
      </nav>
      {result.state === "loading" ? <div className="skeleton" style={{ height: 520 }} aria-busy="true" /> : null}
      {result.state === "error" ? <Notice error={result.error} title="This credential could not load." /> : null}
      {result.state === "ok" ? (
        <div className="workspace">
          <CredentialPass view={result.data} />
          <SharePanel view={result.data} session={session} onChange={reload} />
        </div>
      ) : null}
    </>
  );
}

export default function HolderCredentialPage() {
  return <PortalShell portal="holder">{(session) => <HolderCredential session={session} />}</PortalShell>;
}
