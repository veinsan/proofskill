"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { PortalShell } from "@/components/portal-shell";
import { FieldError } from "@/components/notice";

/** Accepts a whole share link (…/v/sk_…) or just the token. */
function tokenFrom(input: string): string | null {
  const value = input.trim();
  const match = value.match(/\/v\/([^/?#\s]+)/) ?? value.match(/^(sk_[A-Za-z0-9]+)$/);
  return match ? match[1] : null;
}

function CheckLink() {
  const router = useRouter();
  const [link, setLink] = useState("");
  const [invalid, setInvalid] = useState(false);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = tokenFrom(link);
    if (!token) {
      setInvalid(true);
      return;
    }
    router.push(`/v/${encodeURIComponent(token)}`);
  }

  return (
    <div className="workspace">
      <section className="stack">
        <h1 className="title">Check a credential</h1>
        <p className="prose muted">
          Open the link a holder sent you, or paste it here. Verification checks integrity, issuer, and status against the registry.
          It never needs the issuer&apos;s help, and you see only what the holder chose to share.
        </p>
      </section>
      <form className="panel" onSubmit={submit} noValidate>
        <label className="field">
          <span className="label">Share link</span>
          <input
            className="input mono"
            placeholder="http://localhost:3000/v/sk_…"
            value={link}
            onChange={(e) => {
              setLink(e.target.value);
              setInvalid(false);
            }}
            aria-invalid={invalid || undefined}
            aria-describedby={invalid ? "link-error" : undefined}
          />
          {invalid ? <FieldError id="link-error" message="This is not a ProofSkill share link. It contains /v/sk_…" /> : null}
        </label>
        <button className="btn btn--primary btn--block" type="submit" disabled={!link.trim()}>
          Check credential
        </button>
      </form>
    </div>
  );
}

export default function VerifierHome() {
  return <PortalShell portal="verifier">{() => <CheckLink />}</PortalShell>;
}
