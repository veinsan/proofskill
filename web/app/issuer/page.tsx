"use client";

import Link from "next/link";
import { Notice } from "@/components/notice";
import { PortalShell } from "@/components/portal-shell";
import { StatusState } from "@/components/status-state";
import { api, type CredentialSummary, type Page } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/format";
import type { Session } from "@/lib/session";
import { useApi } from "@/lib/use-api";

function IssuedCredentials({ session }: { session: Session }) {
  const { result } = useApi(() => api<Page<CredentialSummary>>("/issuers/me/credentials?limit=200", { token: session.token }), session.token);
  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="title">Issued credentials</h1>
          <p className="small muted">Every credential your organizer issued, newest first. Open one to see its pass or revoke it.</p>
        </div>
        <Link className="btn btn--primary" href="/issuer/issue">
          Issue credential
        </Link>
      </div>
      {result.state === "loading" ? <div className="skeleton" style={{ height: 240 }} aria-busy="true" /> : null}
      {result.state === "error" ? <Notice error={result.error} title="The list could not load." /> : null}
      {result.state === "ok" && result.data.items.length === 0 ? (
        <div className="empty">
          <p className="title">No credentials yet</p>
          <p className="muted prose">
            After a participant passes, issue their credential. Its commitment is anchored on the registry and the holder is notified.
          </p>
        </div>
      ) : null}
      {result.state === "ok" && result.data.items.length > 0 ? (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th className="label">Credential</th>
                <th className="label">Holder</th>
                <th className="label">Program</th>
                <th className="label">Completed</th>
                <th className="label">Issued</th>
                <th className="label">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.data.items.map((item) => (
                <tr key={item.credentialId}>
                  <td>
                    <Link className="mono" href={`/issuer/credentials/${item.credentialId}`}>
                      {item.credentialId}
                    </Link>
                  </td>
                  <td>
                    {item.holderDisplayName}
                    <div className="mono muted">{item.holderRef}</div>
                  </td>
                  <td>{item.program.title}</td>
                  <td>{formatDate(item.program.completedAt)}</td>
                  <td className="mono">{formatDateTime(item.issuedAt)}</td>
                  <td>
                    <StatusState status={item.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </>
  );
}

export default function IssuerHome() {
  return <PortalShell portal="issuer">{(session) => <IssuedCredentials session={session} />}</PortalShell>;
}
