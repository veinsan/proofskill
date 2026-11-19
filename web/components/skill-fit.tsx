"use client";

import { type CSSProperties, type FormEvent, useState } from "react";
import { api, type ApiError, type MatchingResult, type VerificationResult } from "@/lib/api";
import { FieldError, Notice } from "./notice";

// Synthetic sample positions (api/app/seed.py POSITIONS), to speed up a demo.
const SAMPLES = [
  {
    title: "Junior Security Analyst",
    description:
      "Menganalisis kerentanan aplikasi web, memahami OWASP Top 10, melakukan pengujian keamanan dasar, dan memantau log dengan SIEM.",
  },
  {
    title: "Data Analyst Intern",
    description: "Mengolah data dengan SQL dan Python, membuat dashboard visualisasi data, dan menyajikan temuan kepada tim bisnis.",
  },
  {
    title: "Frontend Developer Intern",
    description: "Membangun antarmuka web dengan React dan JavaScript, menulis HTML dan CSS yang rapi, dan bekerja dengan desainer UI.",
  },
];

const MAX_DESCRIPTION = 2000;

/** API-07: a labeled recommendation, available only after this verifier's VALID verification. */
export function SkillFitPanel({ verification, token }: { verification: VerificationResult; token: string }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<MatchingResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  if (verification.result !== "VALID") {
    return (
      <aside className="panel">
        <h2 className="title">Skill fit for a position</h2>
        <p className="prose">
          Skill fit is offered only for a credential that verified as VALID. This one is <b>{verification.result}</b>, so its skills
          are not read.
        </p>
      </aside>
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const response = await api<MatchingResult>("/matchings", {
      method: "POST",
      token,
      body: { verificationId: verification.verificationId, position: { title, description } },
    });
    setBusy(false);
    if (response.ok) setResult(response.data);
    else {
      setResult(null);
      setError(response.error);
    }
  }

  const textError = error?.code === "INVALID_POSITION_TEXT";
  return (
    <aside className="panel" aria-labelledby="fit-title">
      <h2 className="title" id="fit-title">
        Skill fit for a position
      </h2>
      <form className="stack" onSubmit={submit} noValidate>
        <label className="field">
          <span className="label">Sample position, synthetic</span>
          <select
            className="select"
            defaultValue=""
            onChange={(e) => {
              const sample = SAMPLES[Number(e.target.value)];
              if (sample) {
                setTitle(sample.title);
                setDescription(sample.description);
              }
            }}
          >
            <option value="" disabled>
              Choose a sample, or write your own below
            </option>
            {SAMPLES.map((sample, i) => (
              <option key={sample.title} value={i}>
                {sample.title}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="label">Position title</span>
          <input className="input" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} aria-invalid={textError || undefined} />
        </label>
        <label className="field">
          <span className="label">Position description</span>
          <textarea
            className="textarea"
            rows={4}
            value={description}
            maxLength={MAX_DESCRIPTION}
            onChange={(e) => setDescription(e.target.value)}
            aria-invalid={textError || undefined}
            aria-describedby={textError ? "fit-error" : "fit-help"}
          />
          {textError ? (
            <FieldError id="fit-error" message={error.message} code={error.code} />
          ) : (
            <span className="small muted" id="fit-help">
              Requirements are split at commas, sentence ends, and “dan” or “and”. {description.length}/{MAX_DESCRIPTION}
            </span>
          )}
        </label>
        {error && !textError ? (
          <Notice
            error={error}
            title={error.code === "AI_UNAVAILABLE" ? "The AI service is down. The verification above still stands." : "No recommendation."}
          />
        ) : null}
        <button className="btn btn--primary btn--block" type="submit" disabled={busy || !title.trim() || !description.trim()}>
          {busy ? "Comparing skills" : "Check skill fit"}
        </button>
      </form>

      {result ? (
        <section aria-label="Recommendation" aria-live="polite">
          <div className="rek">
            <span className="tag">{result.label}</span>
            <span className="tag">AI · embedding model</span>
            <span className="small muted">A recommendation, not a decision. No total score.</span>
          </div>
          {result.matchedSkills.map((match) => (
            <div key={`${match.skill}-${match.requirement}`} className="match">
              <div>
                {match.skill}
                <i>“{match.requirement}”</i>
                <span className="match__reason">{match.reason}</span>
              </div>
              <div className="sim" role="img" aria-label={`similarity ${match.similarity.toFixed(2)}`}>
                <span style={{ width: `${Math.round(match.similarity * 100)}%` } as CSSProperties} />
              </div>
              <span className="mono">{match.similarity.toFixed(2)}</span>
            </div>
          ))}
          {result.matchedSkills.length === 0 ? <p className="small" style={{ marginTop: 10 }}>No requirement is close to a verified skill.</p> : null}
          {result.missingRequirements.map((missing) => (
            <p key={missing.requirement} className="callout-missing" style={{ marginTop: 10 }}>
              <b>Not covered:</b> “{missing.requirement}”. {missing.note}
            </p>
          ))}
          <ul className="small muted" style={{ marginTop: 14, paddingLeft: 18, display: "grid", gap: 4 }}>
            {result.limitations.map((limit) => (
              <li key={limit}>{limit}</li>
            ))}
          </ul>
          <p className="mono muted" style={{ marginTop: 8 }}>
            {result.matchingId} · {result.modelVersion}
          </p>
        </section>
      ) : null}
    </aside>
  );
}
