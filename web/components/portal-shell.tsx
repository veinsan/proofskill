"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import type { Role } from "@/lib/api";
import { type Session, signOut, useSession } from "@/lib/session";

export type Portal = "issuer" | "holder" | "verifier";

const PORTALS: Record<Portal, { name: string; role: Role; nav: { href: string; label: string }[] }> = {
  issuer: {
    name: "Issuer portal",
    role: "issuer_admin",
    nav: [
      { href: "/issuer", label: "Credentials" },
      { href: "/issuer/issue", label: "Issue credential" },
      { href: "/issuer/audit", label: "Audit log" },
    ],
  },
  holder: { name: "Holder portal", role: "holder", nav: [{ href: "/holder", label: "My credentials" }] },
  verifier: { name: "Verifier portal", role: "verifier", nav: [{ href: "/verifier", label: "Check a credential" }] },
};

export function TopBar({ portal, session }: { portal?: Portal; session: Session | null | undefined }) {
  const pathname = usePathname();
  const router = useRouter();
  const config = portal ? PORTALS[portal] : null;
  return (
    <header className="topbar">
      <Link className="brand" href="/">
        ProofSkill
      </Link>
      {config ? <span className="portal-name">{config.name}</span> : null}
      {config && session?.role === config.role ? (
        <nav className="nav" aria-label={config.name}>
          {config.nav.map((item) => (
            <Link key={item.href} href={item.href} aria-current={pathname === item.href ? "page" : undefined}>
              {item.label}
            </Link>
          ))}
        </nav>
      ) : null}
      <div className="topbar__right">
        <span className="synthetic" title="All data in this prototype is invented (assumption A6)">
          Synthetic data
        </span>
        {session ? (
          <>
            <span className="account">{session.username}</span>
            <button
              type="button"
              className="topbar__signout"
              onClick={() => {
                signOut();
                router.push("/");
              }}
            >
              Sign out
            </button>
          </>
        ) : null}
      </div>
    </header>
  );
}

/** Portal page frame: renders children only for the portal's role, otherwise asks to sign in. */
export function PortalShell({ portal, children }: { portal: Portal; children: (session: Session) => ReactNode }) {
  const session = useSession();
  const pathname = usePathname();
  const config = PORTALS[portal];
  let content: ReactNode;
  if (session === undefined) {
    content = <div className="skeleton" style={{ height: 320 }} aria-busy="true" />;
  } else if (session === null || session.role !== config.role) {
    content = (
      <div className="empty">
        <p className="title">Sign in to the {config.name.toLowerCase()}</p>
        <p className="muted prose">
          {session ? `You are signed in as ${session.username}, which is not a ${config.role} account. ` : ""}
          This page needs a <span className="mono">{config.role}</span> account.
        </p>
        <Link className="btn btn--secondary" href={`/?next=${encodeURIComponent(pathname)}`}>
          Go to sign in
        </Link>
      </div>
    );
  } else {
    content = children(session);
  }
  return (
    <>
      <TopBar portal={portal} session={session} />
      <main className="page">{content}</main>
    </>
  );
}
