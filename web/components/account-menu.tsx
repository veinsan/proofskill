"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import type { Role } from "@/lib/api";
import { type Session, signOut } from "@/lib/session";

const ROLE_LABEL: Record<Role, string> = {
  issuer_admin: "Issuer admin",
  holder: "Holder",
  verifier: "Verifier",
  platform_admin: "Platform admin",
};

/** The avatar opens a small menu; signing out asks once in a modal dialog before it happens. */
export function AccountMenu({ session }: { session: Session }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const menuId = useId();
  const titleId = useId();

  // Close the menu on an outside click or Escape, as a native menu would.
  useEffect(() => {
    if (!open) return;
    function onPointer(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function confirmSignOut() {
    dialogRef.current?.close();
    signOut();
    router.push("/");
  }

  return (
    <div className="account-menu" ref={rootRef}>
      <button
        type="button"
        className="account"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="avatar" aria-hidden="true">
          {session.username.slice(0, 1)}
        </span>
        <span className="account__name">{session.username}</span>
        <svg className="account__chevron" width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M2.5 4.5 6 8l3.5-3.5" />
        </svg>
      </button>

      {open ? (
        <div className="account-menu__panel" id={menuId} role="menu" aria-label="Account">
          <div className="account-menu__who">
            <span className="avatar avatar--lg" aria-hidden="true">
              {session.username.slice(0, 1)}
            </span>
            <div>
              <b>{session.username}</b>
              <span className="small muted">{ROLE_LABEL[session.role]}</span>
            </div>
          </div>
          <button
            type="button"
            role="menuitem"
            className="btn btn--danger btn--block"
            autoFocus
            onClick={() => {
              setOpen(false);
              dialogRef.current?.showModal();
            }}
          >
            Sign out
          </button>
        </div>
      ) : null}

      <dialog ref={dialogRef} className="confirm-dialog" aria-labelledby={titleId}>
        <h2 className="title" id={titleId}>
          Sign out of ProofSkill?
        </h2>
        <p className="muted">
          You are signed in as <b>{session.username}</b>. You will need to sign in again to open your portal.
        </p>
        <div className="confirm-dialog__actions">
          <button type="button" className="btn btn--secondary" autoFocus onClick={() => dialogRef.current?.close()}>
            Cancel
          </button>
          <button type="button" className="btn btn--danger" onClick={confirmSignOut}>
            Sign out
          </button>
        </div>
      </dialog>
    </div>
  );
}
