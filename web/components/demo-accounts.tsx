"use client";

import { type KeyboardEvent as ReactKeyboardEvent, useEffect, useId, useRef, useState } from "react";
import type { ApiError } from "@/lib/api";
import { type DemoAccount, type DemoGroup, initials } from "@/lib/demo";
import { type Session, signInDemo } from "@/lib/session";
import { CheckIcon } from "./icons";
import { Notice } from "./notice";

/** Demo sign-in, as simple as SafeTrip's: pick a role, keep or change the account, press one button
 * (app/api/demo-signin holds the password). With one group (a share link's verifiers) the role
 * picker is left out. */
export function DemoSignIn({
  groups,
  initial,
  action,
  onSignedIn,
}: {
  groups: readonly DemoGroup[];
  initial?: string | null;
  action?: string;
  onSignedIn: (session: Session) => void;
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
    if (result.ok) onSignedIn(result.data);
    else setError(result.error);
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

      <AccountPicker
        accounts={group.accounts}
        value={account.username}
        onChange={(next) => {
          setUsername(next);
          setError(null);
        }}
      />

      <button className="btn btn--primary btn--block" type="button" onClick={enter} disabled={busy}>
        {busy ? "Signing in" : (action ?? `Enter ${group.portal}`)}
      </button>
      {error ? <Notice error={error} title="Could not sign in." /> : null}

      {groups.length > 1 ? (
        <p className="quick-pick small muted">
          <span>Quick pick</span>
          {groups.map((g) => (
            <span key={g.role} className="quick-pick__item">
              <kbd>Alt+{g.key.slice(3)}</kbd>
              {g.short}
            </span>
          ))}
        </p>
      ) : null}
    </div>
  );
}

function AccountRow({ account }: { account: DemoAccount }) {
  return (
    <span className="account-row">
      <span className="account-row__avatar" aria-hidden="true">
        {initials(account.name)}
      </span>
      <span className="account-row__text">
        <strong>{account.name}</strong>
        <span className="account-row__title">{account.title}</span>
      </span>
      <span className="account-row__meta">
        {account.id ? <span className="account-row__id">{account.id}</span> : null}
        <span className="mono">{account.username}</span>
      </span>
    </span>
  );
}

/** A styled listbox (the native select cannot show an avatar or a second line). Keyboard: arrows,
 * Home and End move, Enter or Space picks, Escape closes; a click outside closes it too. */
function AccountPicker({ accounts, value, onChange }: { accounts: readonly DemoAccount[]; value: string; onChange: (username: string) => void }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const selectedIndex = Math.max(
    accounts.findIndex((a) => a.username === value),
    0,
  );

  useEffect(() => {
    if (!open) return;
    listRef.current?.focus();
    const onDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onDown);
    return () => document.removeEventListener("pointerdown", onDown);
  }, [open]);

  function show() {
    setActive(selectedIndex);
    setOpen(true);
  }

  function pick(index: number) {
    onChange(accounts[index].username);
    setOpen(false);
    buttonRef.current?.focus();
  }

  function onButtonKey(event: ReactKeyboardEvent) {
    if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
      event.preventDefault();
      show();
    }
  }

  function onListKey(event: ReactKeyboardEvent) {
    const last = accounts.length - 1;
    const moves: Record<string, number> = { ArrowDown: Math.min(active + 1, last), ArrowUp: Math.max(active - 1, 0), Home: 0, End: last };
    if (event.key in moves) {
      event.preventDefault();
      setActive(moves[event.key]);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      pick(active);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      buttonRef.current?.focus();
    } else if (event.key === "Tab") {
      setOpen(false);
    }
  }

  return (
    <div className="picker" ref={rootRef}>
      <span className="label" id={`${id}-label`}>
        Account
      </span>
      <button
        ref={buttonRef}
        id={`${id}-button`}
        type="button"
        className="picker__button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-labelledby={`${id}-label ${id}-button`}
        onClick={() => (open ? setOpen(false) : show())}
        onKeyDown={onButtonKey}
      >
        <AccountRow account={accounts[selectedIndex]} />
        <svg className="picker__chevron" width="14" height="14" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M2.5 4.5 6 8l3.5-3.5" />
        </svg>
      </button>
      {open ? (
        <ul
          ref={listRef}
          className="picker__list"
          role="listbox"
          tabIndex={-1}
          aria-labelledby={`${id}-label`}
          aria-activedescendant={`${id}-option-${active}`}
          onKeyDown={onListKey}
        >
          {accounts.map((account, index) => (
            <li
              key={account.username}
              id={`${id}-option-${index}`}
              role="option"
              aria-selected={index === selectedIndex}
              className="picker__option"
              data-active={index === active || undefined}
              onPointerEnter={() => setActive(index)}
              onClick={() => pick(index)}
            >
              <AccountRow account={account} />
              <span className="picker__check" aria-hidden="true">
                {index === selectedIndex ? <CheckIcon size={16} /> : null}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
