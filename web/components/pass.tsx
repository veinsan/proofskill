import { Fragment, type CSSProperties, type ReactNode } from "react";
import type { CredentialStatus, SkillRef, VerificationResult } from "@/lib/api";
import { formatDateTime, middle } from "@/lib/format";
import { ArrowRightIcon, DotIcon, RingIcon } from "./icons";

export interface PassCell {
  label: string;
  value?: ReactNode;
  /** Shown in Muted Ink instead of a value: never an empty cell (DESIGN.md Pass). */
  absent?: "Withheld" | "Not shared";
  full?: boolean;
}

interface PassProps {
  issuerId: string;
  issuerName: string;
  credentialId: string;
  credentialSub: string;
  cells: PassCell[];
  cleared: boolean;
  stub: ReactNode;
}

/** The credential as one object at one fixed scale in all three portals: body, perforation, stub. */
export function Pass({ issuerId, issuerName, credentialId, credentialSub, cells, cleared, stub }: PassProps) {
  return (
    <article className="pass" aria-label={`Credential ${credentialId}`}>
      <div className="pass__body">
        <div className="pass__route">
          <div>
            <div className="label">Issuer</div>
            <div className="pass__code">{issuerId}</div>
            <div className="pass__sub">{issuerName}</div>
          </div>
          <div className="pass__arrow">
            <ArrowRightIcon label="issued" />
          </div>
          <div>
            <div className="label">Credential</div>
            <div className="pass__code">{credentialId}</div>
            <div className="pass__sub">{credentialSub}</div>
          </div>
        </div>
        <div className="cells">
          {cells.map((cell) => (
            <div key={cell.label} className={cell.full ? "cell cell--full" : "cell"}>
              <div className="label">{cell.label}</div>
              {cell.absent ? <div className="value value--absent">{cell.absent}</div> : <div className="value">{cell.value}</div>}
            </div>
          ))}
        </div>
      </div>
      <aside className={cleared ? "stub stub--cleared" : "stub stub--held"}>{stub}</aside>
    </article>
  );
}

export function SkillChips({ skills }: { skills: SkillRef[] }) {
  return (
    <div className="skills">
      {skills.map((skill) => (
        <span key={skill.skillId} className="skill-chip">
          {skill.label}
          <span className="mono">{skill.skillId}</span>
        </span>
      ))}
    </div>
  );
}

// Approximate advance widths (em) of Plus Jakarta Sans 800 capitals for the enum letters, with slack.
const NARROW = new Set(["I", "1", ":"]);
const ROUND = new Set(["O", "Q", "D", "C", "G"]);
const WIDE = new Set(["M", "W"]);
function ems(word: string): number {
  let total = 0;
  for (const ch of word) total += NARROW.has(ch) ? 0.35 : ch === "_" ? 0.6 : WIDE.has(ch) ? 1.05 : ROUND.has(ch) ? 0.9 : 0.8;
  return total * 0.98;
}

/** A verbatim enum word sized to fit the stub: it may break after "_", and the widest part sets the size. */
function StubWord({ text, className }: { text: string; className: string }) {
  const parts = text.split("_");
  const units = Math.max(...parts.map((part, i) => ems(i < parts.length - 1 ? `${part}_` : part)));
  return (
    <div className={className} style={{ "--ems": units.toFixed(2) } as CSSProperties}>
      {parts.map((part, i) => (
        <Fragment key={part}>
          {part}
          {i < parts.length - 1 ? (
            <>
              _<wbr />
            </>
          ) : null}
        </Fragment>
      ))}
    </div>
  );
}

function ChainRef({ lines }: { lines: string[] }) {
  return (
    <div className="stub__chain mono">
      {lines.map((line) => (
        <span key={line}>{line}</span>
      ))}
    </div>
  );
}

/** Issuer and holder views: the status the registry holds, with the chain reference. */
export function RegistryStub({
  status,
  issuerId,
  revokedAt,
  reason,
  txHash,
  commitment,
}: {
  status: CredentialStatus;
  issuerId: string;
  revokedAt: string | null;
  reason: string | null;
  txHash: string | null;
  commitment: string;
}) {
  return (
    <>
      <div className="label">Blockchain registry status</div>
      <StubWord className="status-word" text={status === "active" ? "ACTIVE" : "REVOKED"} />
      <p className="stub__say">
        {status === "active"
          ? "Anchored on the registry and still active. Verifiers can check it without contacting the issuer."
          : `Revoked by ${issuerId}${revokedAt ? ` on ${formatDateTime(revokedAt)}` : ""}. Reason: ${reason ?? "none recorded"}.`}
      </p>
      <ChainRef lines={[`commit ${middle(commitment)}`, txHash ? `tx ${middle(txHash)}` : "tx pending"]} />
    </>
  );
}

const VERDICT_SENTENCE: Record<VerificationResult["result"], (reason?: string) => string> = {
  VALID: () => "Issued by an authorized issuer, unchanged since issuance, and still active. You can rely on it and check skill fit.",
  REVOKED: (reason) => `The issuer revoked this credential. Reason: ${reason ?? "none recorded"}. Do not rely on it for this application.`,
  TAMPERED: () =>
    "The credential data no longer matches what the issuer recorded, so its details are withheld. Ask the holder for a new link.",
  ISSUER_UNAUTHORIZED: () => "The issuer of this credential is not authorized on the registry, so it cannot be relied on.",
};

/** Verifier view: the verdict, its plain-English sentence, and the three checks (NFR-04). */
export function VerificationStub({ verification }: { verification: VerificationResult }) {
  const { checks, result } = verification;
  const issuerId = verification.credential?.issuer.issuerId ?? "The issuer";
  const rows: { name: string; pass: boolean; text: string; state: string }[] = [
    {
      name: "Integrity",
      pass: checks.integrity === "PASS",
      text: checks.integrity === "PASS" ? "Recomputed hash matches the registry commitment" : "The data no longer matches the registry commitment",
      state: checks.integrity,
    },
    {
      name: "Issuer",
      pass: checks.issuerAuthorized === "PASS",
      text: checks.issuerAuthorized === "PASS" ? `${issuerId} is an authorized issuer on the registry` : "The issuer is not authorized on the registry",
      state: checks.issuerAuthorized,
    },
    {
      name: "Status",
      pass: checks.status === "ACTIVE",
      text: checks.status === "ACTIVE" ? "Not revoked by its issuer" : "Revoked by its issuer",
      state: checks.status,
    },
  ];
  return (
    <>
      <div className="label">
        Blockchain registry · checked <span style={{ whiteSpace: "nowrap" }}>{formatDateTime(verification.verifiedAt)}</span>
      </div>
      <StubWord className="verdict" text={result} />
      <p className="stub__say">{VERDICT_SENTENCE[result](verification.reason)}</p>
      <div role="list" aria-label="Checks">
        {rows.map((row) => (
          <div key={row.name} className="check" role="listitem">
            {row.pass ? <DotIcon label="passed" /> : <RingIcon label="failed" />}
            <div>
              <b>{row.name}</b>
              <span>{row.text}</span>
            </div>
            <span className="check__state">{row.state}</span>
          </div>
        ))}
      </div>
      <ChainRef
        lines={[verification.chainRef.txHash ? `tx ${middle(verification.chainRef.txHash)}` : "tx unavailable", verification.verificationId]}
      />
    </>
  );
}
