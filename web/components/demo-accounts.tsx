"use client";

import { useState } from "react";
import type { ApiError } from "@/lib/api";
import { type DEMO_GROUPS, initials } from "@/lib/demo";
import { type Session, signInDemo } from "@/lib/session";
import { ArrowRightIcon } from "./icons";
import { Notice } from "./notice";

type Group = (typeof DEMO_GROUPS)[number];

/** Demo accounts as cards; one click signs in (app/api/demo-signin). `onOff` fires when the server
 * has no demo password, so the page can show its password form instead. */
export function DemoAccounts({
  groups,
  highlight,
  onSignedIn,
  onOff,
}: {
  groups: readonly Group[];
  highlight?: string | null;
  onSignedIn: (session: Session) => void;
  onOff?: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  async function pick(username: string) {
    setBusy(username);
    setError(null);
    const result = await signInDemo(username);
    setBusy(null);
    if (result.ok) {
      onSignedIn(result.data);
      return;
    }
    if (result.status === 501) onOff?.();
    setError(result.error);
  }

  return (
    <div className="accounts" role="group" aria-label="Demo accounts">
      {groups.map((group) => (
        <div key={group.role} className="accounts__group">
          <div className="accounts__role">
            <img src={`/art/${group.art}.webp`} alt="" width={32} height={32} />
            <span className="label">{group.role}</span>
          </div>
          <div className="accounts__cards">
            {group.accounts.map((account) => (
              <button
                key={account.username}
                type="button"
                className="account-card"
                aria-current={highlight === account.username || undefined}
                aria-busy={busy === account.username || undefined}
                disabled={busy !== null}
                onClick={() => pick(account.username)}
              >
                <span className="account-card__avatar" aria-hidden="true">
                  {initials(account.name)}
                </span>
                <span className="account-card__text">
                  <strong>{account.name}</strong>
                  <Detail text={account.detail} />
                  <span className="mono">{account.username}</span>
                </span>
                <span className="account-card__go" aria-hidden="true">
                  {busy === account.username ? <span className="account-card__spinner" /> : <ArrowRightIcon size={18} />}
                </span>
              </button>
            ))}
          </div>
        </div>
      ))}
      {error ? <Notice error={error} title="Could not sign in." /> : null}
    </div>
  );
}

/** "Admin, Unit Pelatihan Contoh · ISS-001": the trailing ID never breaks at its hyphen. */
function Detail({ text }: { text: string }) {
  const cut = text.lastIndexOf(" · ");
  const id = cut >= 0 ? text.slice(cut + 3) : "";
  return (
    <span className="account-card__detail">
      {id && /\d/.test(id) ? (
        <>
          {text.slice(0, cut)} · <span className="account-card__id">{id}</span>
        </>
      ) : (
        text
      )}
    </span>
  );
}
