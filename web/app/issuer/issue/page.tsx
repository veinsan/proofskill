"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";
import { FieldError, Notice } from "@/components/notice";
import { PageHead, PortalShell } from "@/components/portal-shell";
import { api, type ApiError, type CredentialIssued, type Page, type Skill } from "@/lib/api";
import { DEMO_HOLDERS } from "@/lib/demo";
import type { Session } from "@/lib/session";

function SkillPicker({ token, selected, onToggle }: { token: string; selected: Skill[]; onToggle: (skill: Skill) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Skill[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    let live = true;
    const timer = window.setTimeout(async () => {
      const response = await api<Page<Skill>>(`/skills?limit=50&query=${encodeURIComponent(query.trim())}`, { token });
      if (!live) return;
      if (response.ok) {
        setResults(response.data.items);
        setError(null);
      } else setError(response.error);
    }, 200);
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [query, token]);

  const chosen = new Set(selected.map((s) => s.skillId));
  return (
    <fieldset className="stack">
      <legend className="label">Skills, from the catalog</legend>
      <input
        className="input"
        type="search"
        placeholder="Filter the catalog by name or alias"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Filter the skill catalog"
      />
      {error ? <Notice error={error} /> : null}
      {results === null ? <div className="skeleton" style={{ height: 120 }} aria-busy="true" /> : null}
      {results && results.length === 0 ? <p className="small muted">No catalog skill matches “{query}”.</p> : null}
      {results && results.length > 0 ? (
        <div className="checks-list" style={{ maxHeight: 260, overflowY: "auto", paddingRight: 4 }}>
          {results.map((skill) => (
            <label key={skill.skillId} className="check-option">
              <input type="checkbox" checked={chosen.has(skill.skillId)} onChange={() => onToggle(skill)} />
              <span>
                {skill.label} <span className="mono muted">{skill.skillId}</span>
              </span>
            </label>
          ))}
        </div>
      ) : null}
    </fieldset>
  );
}

function IssueForm({ session }: { session: Session }) {
  const router = useRouter();
  const [holderRef, setHolderRef] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [title, setTitle] = useState("");
  const [completedAt, setCompletedAt] = useState("");
  const [criteria, setCriteria] = useState("");
  const [skills, setSkills] = useState<Skill[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  const ready = holderRef && displayName && title && completedAt && criteria && skills.length > 0;
  const holderError = error?.code === "MALFORMED_REQUEST" && /holderRef/i.test(error.message);

  function toggle(skill: Skill) {
    setSkills((current) => (current.some((s) => s.skillId === skill.skillId) ? current.filter((s) => s.skillId !== skill.skillId) : [...current, skill]));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const response = await api<CredentialIssued>("/credentials", {
      method: "POST",
      token: session.token,
      body: {
        holderRef: holderRef.trim(),
        holderDisplayName: displayName.trim(),
        program: { title: title.trim(), completedAt, criteria: criteria.trim() },
        skills: skills.map((s) => s.skillId),
      },
    });
    setBusy(false);
    if (response.ok) router.push(`/issuer/credentials/${response.data.credentialId}?issued=1`);
    else setError(response.error);
  }

  return (
    <form onSubmit={submit} noValidate>
      <PageHead title="Issue a credential" art="issuer" lede="For a participant whose graduation you have already validated (T01)." />
      <div className="workspace">
        <section className="panel">
          <div className="cells" style={{ gap: "var(--s-lg) var(--s-xl)" }}>
            <label className="field">
              <span className="label">Holder reference</span>
              <input
                className="input mono"
                placeholder="HLD-2026-0007"
                value={holderRef}
                onChange={(e) => setHolderRef(e.target.value)}
                aria-invalid={holderError || undefined}
                aria-describedby={holderError ? "holder-error" : "holder-help"}
              />
              {holderError ? (
                <FieldError id="holder-error" message="No holder account has this reference." code={error?.code} />
              ) : (
                <span className="small muted" id="holder-help">
                  The participant&apos;s pseudonymous reference. It is hashed; their name is not.
                </span>
              )}
              <span className="hint-chips" aria-label="Demo holders">
                {DEMO_HOLDERS.map((holder) => (
                  <button
                    key={holder.holderRef}
                    type="button"
                    className="hint-chip"
                    onClick={() => {
                      setHolderRef(holder.holderRef);
                      if (!displayName) setDisplayName(holder.name);
                    }}
                  >
                    {holder.holderRef}
                  </button>
                ))}
              </span>
            </label>
            <label className="field">
              <span className="label">Holder display name</span>
              <input className="input" placeholder="Peserta Contoh A" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
              <span className="small muted">Stored off-chain only and never hashed.</span>
            </label>
          </div>
          <label className="field">
            <span className="label">Program</span>
            <input className="input" placeholder="Pelatihan Keamanan Aplikasi Web Dasar" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <div className="cells" style={{ gap: "var(--s-lg) var(--s-xl)" }}>
            <label className="field">
              <span className="label">Completed</span>
              <input className="input" type="date" value={completedAt} onChange={(e) => setCompletedAt(e.target.value)} />
            </label>
            <label className="field">
              <span className="label">Pass criteria</span>
              <input
                className="input"
                placeholder="Kehadiran minimal 80 persen dan lulus proyek akhir"
                value={criteria}
                onChange={(e) => setCriteria(e.target.value)}
              />
            </label>
          </div>
          <hr className="panel__divider" />
          <SkillPicker token={session.token} selected={skills} onToggle={toggle} />
        </section>

        <aside className="panel">
          <img src="/art/chain.webp" alt="" width={96} height={69} style={{ width: 96 }} />
          <h2 className="title">What the registry records</h2>
          <p className="small">
            The registry receives only a SHA-256 commitment of the credential plus a random nonce, the issuer, the status, and the
            time. The holder&apos;s name, the program text, and the skills stay off-chain.
          </p>
          <div>
            <div className="label">Selected skills</div>
            {skills.length ? (
              <div className="skills">
                {skills.map((skill) => (
                  <button key={skill.skillId} type="button" className="skill-chip" onClick={() => toggle(skill)} aria-label={`Remove ${skill.label}`}>
                    {skill.label}
                    <span className="mono">{skill.skillId}</span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="small muted" style={{ marginTop: 4 }}>
                Pick at least one skill from the catalog.
              </p>
            )}
          </div>
          {error && !holderError ? <Notice error={error} title="Not issued." /> : null}
          <button className="btn btn--primary btn--block" type="submit" disabled={!ready || busy}>
            {busy ? "Anchoring on the registry" : "Issue credential"}
          </button>
        </aside>
      </div>
    </form>
  );
}

export default function IssuePage() {
  return <PortalShell portal="issuer">{(session) => <IssueForm session={session} />}</PortalShell>;
}
