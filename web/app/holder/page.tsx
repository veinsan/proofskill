"use client";

import Link from "next/link";
import { Notice } from "@/components/notice";
import { PortalShell } from "@/components/portal-shell";
import { StatusState } from "@/components/status-state";
import { api, type CredentialSummary, type Page } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Session } from "@/lib/session";
import { useApi } from "@/lib/use-api";

function MyCredentials({ session }: { session: Session }) {
  const { result } = useApi(() => api<Page<CredentialSummary>>("/holders/me/credentials?limit=200", { token: session.token }), session.token);
  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="title">My credentials</h1>
          <p className="small muted prose">
            Credentials issued to you. Open one to share it with a scoped link or QR code; you choose what a verifier sees and for how
            long.
          </p>
        </div>
      </div>
      {result.state === "loading" ? <div className="skeleton" style={{ height: 200 }} aria-busy="true" /> : null}
      {result.state === "error" ? <Notice error={result.error} title="Your credentials could not load." /> : null}
      {result.state === "ok" && result.data.items.length === 0 ? (
        <div className="empty">
          <p className="title">Nothing issued to you yet</p>
          <p className="muted prose">When a training organizer issues you a credential, it appears here and you get an email.</p>
        </div>
      ) : null}
      {result.state === "ok" && result.data.items.length > 0 ? (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th className="label">Credential</th>
                <th className="label">Program</th>
                <th className="label">Issuer</th>
                <th className="label">Completed</th>
                <th className="label">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.data.items.map((item) => (
                <tr key={item.credentialId}>
                  <td>
                    <Link className="mono" href={`/holder/credentials/${item.credentialId}`}>
                      {item.credentialId}
                    </Link>
                  </td>
                  <td>{item.program.title}</td>
                  <td>
                    {item.issuer.name}
                    <div className="mono muted">{item.issuer.issuerId}</div>
                  </td>
                  <td>{formatDate(item.program.completedAt)}</td>
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

export default function HolderHome() {
  return <PortalShell portal="holder">{(session) => <MyCredentials session={session} />}</PortalShell>;
}
