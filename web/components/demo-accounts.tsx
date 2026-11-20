"use client";

import { useEffect, useState } from "react";
import type { ApiError } from "@/lib/api";
import type { DemoGroup } from "@/lib/demo";
import { type Session, signInDemo } from "@/lib/session";
import { Notice } from "./notice";

/** Demo sign-in, as simple as SafeTrip's: pick a role, keep or change the account, press one button
 * (app/api/demo-signin holds the password). With one group (a share link's verifiers) the role
 * picker is left out. `onOff` fires when the server has no demo password, so the page can show its
 * password form instead. */
export function DemoSignIn({
  groups,
  initial,
  action,
  onSignedIn,
  onOff,
}: {
  groups: readonly DemoGroup[];
  initial?: string | null;
  action?: string;
  onSignedIn: (session: Session) => void;
  onOff?: () => void;
}) {
  const start = Math.max(
    groups.findIndex((group) => group.accounts.some((account) => account.username === initial)),
    0,
  );
  const [roleIndex, setRoleIndex] = useState(start);
  const [username, setUsername] = useState<string>(
    groups[start].accounts.find((a) => a.username === initial)?.username ?? groups[start].accounts[0].username,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const group = groups[roleIndex];
  const account = group.accounts.find((a) => a.username === username) ?? group.accounts[0];

  function choose(index: number) {
    setRoleIndex(index);
    setUsername(groups[index].accounts[0].username);
    setError(null);
  }

  // Quick pick from the keyboard, like SafeTrip: Alt+I issuer, Alt+H holder, Alt+V verifier.
  useEffect(() => {
    if (groups.length < 2) return;
    const onKey = (event: KeyboardEvent) => {
      if (!event.altKey || event.ctrlKey || event.metaKey) return;
      const index = groups.findIndex((g) => g.key === event.code);
      if (index < 0) return;
      event.preventDefault();
      setRoleIndex(index);
      setUsername(groups[index].accounts[0].username);
      setError(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [groups]);

  async function enter() {
    setBusy(true);
    setError(null);
    const result = await signInDemo(account.username);
    setBusy(false);
    if (result.ok) {
      onSignedIn(result.data);
      return;
    }
    if (result.status === 501) onOff?.();
    setError(result.error);
  }

  return (
    <div className="demo-signin">
      {groups.length > 1 ? (
        <fieldset className="role-picker">
          <legend className="label">Role</legend>
          <div className="role-picker__options">
            {groups.map((g, index) => (
              <button key={g.role} type="button" className="role-option" aria-pressed={index === roleIndex} onClick={() => choose(index)}>
                <img src={`/art/${g.art}.webp`} alt="" width={36} height={36} />
                <span className="role-option__name">{g.short}</span>
                <span className="role-option__blurb">{g.blurb}</span>
              </button>
            ))}
          </div>
        </fieldset>
      ) : null}

      <label className="field">
        <span className="label">Account</span>
        <select className="select" value={account.username} onChange={(e) => setUsername(e.target.value)}>
          {group.accounts.map((a) => (
            <option key={a.username} value={a.username}>
              {a.name} ({a.username})
            </option>
          ))}
        </select>
        <span className="small muted">{account.detail}</span>
      </label>

      <button className="btn btn--primary btn--block" type="button" onClick={enter} disabled={busy}>
        {busy ? "Signing in" : (action ?? `Enter ${group.portal}`)}
      </button>
      {error ? <Notice error={error} title="Could not sign in." /> : null}

      {groups.length > 1 ? (
        <p className="quick-pick small muted">
          Quick pick:{" "}
          {groups.map((g) => (
            <kbd key={g.role}>
              Alt+{g.key.slice(3)} · {g.short}
            </kbd>
          ))}
        </p>
      ) : null}
    </div>
  );
}
