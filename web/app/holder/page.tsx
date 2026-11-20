"use client";

import Link from "next/link";
import { Notice } from "@/components/notice";
import { PageHead, PortalShell } from "@/components/portal-shell";
import { StatusState } from "@/components/status-state";
import { api, type CredentialSummary, type Page } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Session } from "@/lib/session";
import { useApi } from "@/lib/use-api";

function MyCredentials({ session }: { session: Session }) {
  const { result } = useApi(() => api<Page<CredentialSummary>>("/holders/me/credentials?limit=200", { token: session.token }), session.token);
  return (
    <>
      <PageHead
        title="My credentials"
        art="holder"
        lede="Credentials issued to you. Open one to share it with a link or QR code; you choose what a verifier sees and for how long."
      />
      {result.state === "loading" ? <div className="skeleton" style={{ height: 200 }} aria-busy="true" /> : null}
      {result.state === "error" ? <Notice error={result.error} title="Your credentials could not load." /> : null}
      {result.state === "ok" && result.data.items.length === 0 ? (
        <div className="empty">
          <img src="/art/empty.webp" alt="" width={132} height={121} />
          <h2 className="title">Nothing issued to you yet</h2>
          <p className="muted prose">When a training organizer issues you a credential, it appears here and you get an email.</p>
        </div>
      ) : null}
      {result.state === "ok" && result.data.items.length > 0 ? (
        <ul className="cards" style={{ listStyle: "none" }}>
          {result.data.items.map((item) => (
            <li key={item.credentialId} style={{ display: "grid" }}>
              <Link className="card-link" href={`/holder/credentials/${item.credentialId}`}>
                <div className="card-link__top">
                  <span className="mono muted">{item.credentialId}</span>
                  <StatusState status={item.status} />
                </div>
                <h2>{item.program.title}</h2>
                <p className="small muted">
                  {item.issuer.name} <span className="mono">{item.issuer.issuerId}</span>
                </p>
                <div className="card-link__foot">
                  <span>Completed {formatDate(item.program.completedAt)}</span>
                  <span>{item.status === "active" ? "Open to share" : "View"}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </>
  );
}

export default function HolderHome() {
  return <PortalShell portal="holder">{(session) => <MyCredentials session={session} />}</PortalShell>;
}
