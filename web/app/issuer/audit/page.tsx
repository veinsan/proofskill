"use client";

import { useState } from "react";
import { Notice } from "@/components/notice";
import { PortalShell } from "@/components/portal-shell";
import { api, type AuditEvent, type Page } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { Session } from "@/lib/session";
import { useApi } from "@/lib/use-api";

const OPERATIONS = ["issueCredential", "createShareLink", "revokeShareLink", "verifyCredential", "matchSkills", "revokeCredential"];

function AuditLog({ session }: { session: Session }) {
  const [operation, setOperation] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const params = new URLSearchParams({ limit: "200" });
  if (operation) params.set("operation", operation);
  if (from) params.set("from", `${from}T00:00:00Z`);
  if (to) params.set("to", `${to}T23:59:59Z`);
  const query = params.toString();
  const { result } = useApi(() => api<Page<AuditEvent>>(`/audit-logs?${query}`, { token: session.token }), query);

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="title">Audit log</h1>
          <p className="small muted prose">
            Operations on your organizer&apos;s credentials: time, actor role, operation, object, and outcome. No payload is ever
            stored here.
          </p>
        </div>
      </div>
      <form className="row" style={{ marginBottom: "var(--s-xl)", alignItems: "end" }} onSubmit={(e) => e.preventDefault()}>
        <label className="field" style={{ minWidth: 220 }}>
          <span className="label">Operation</span>
          <select className="select" value={operation} onChange={(e) => setOperation(e.target.value)}>
            <option value="">All operations</option>
            {OPERATIONS.map((op) => (
              <option key={op} value={op}>
                {op}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="label">From (UTC)</span>
          <input className="input" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label className="field">
          <span className="label">To (UTC)</span>
          <input className="input" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </label>
      </form>
      {result.state === "loading" ? <div className="skeleton" style={{ height: 240 }} aria-busy="true" /> : null}
      {result.state === "error" ? <Notice error={result.error} title="The audit log could not load." /> : null}
      {result.state === "ok" && result.data.items.length === 0 ? (
        <div className="empty">
          <p className="title">No events in this window</p>
          <p className="muted prose">Issuing, sharing, verifying, matching, and revoking each add a row here.</p>
        </div>
      ) : null}
      {result.state === "ok" && result.data.items.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th className="label">Time</th>
                  <th className="label">Actor role</th>
                  <th className="label">Operation</th>
                  <th className="label">Object</th>
                  <th className="label">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {result.data.items.map((event, i) => (
                  <tr key={`${event.time}-${i}`}>
                    <td className="mono">{formatDateTime(event.time)}</td>
                    <td className="mono">{event.actorRole}</td>
                    <td className="mono">{event.operation}</td>
                    <td className="mono">{event.objectId}</td>
                    <td className="mono">{event.outcome}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small muted" style={{ marginTop: "var(--s-md)" }}>
            {result.data.total} event{result.data.total === 1 ? "" : "s"}
          </p>
        </>
      ) : null}
    </>
  );
}

export default function AuditPage() {
  return <PortalShell portal="issuer">{(session) => <AuditLog session={session} />}</PortalShell>;
}
