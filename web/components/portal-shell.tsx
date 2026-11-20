"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import type { Role } from "@/lib/api";
import { HOME_BY_ROLE, type Session, signOut, useSession } from "@/lib/session";
import { BrandMark } from "./icons";

export type Portal = "issuer" | "holder" | "verifier";

const PORTALS: Record<Portal, { name: string; role: Role; nav: { href: string; label: string }[] }> = {
  issuer: {
    name: "Issuer",
    role: "issuer_admin",
    nav: [
      { href: "/issuer", label: "Credentials" },
      { href: "/issuer/issue", label: "Issue credential" },
      { href: "/issuer/audit", label: "Audit log" },
    ],
  },
  holder: { name: "Holder", role: "holder", nav: [{ href: "/holder", label: "My credentials" }] },
  verifier: { name: "Verifier", role: "verifier", nav: [{ href: "/verifier", label: "Check a credential" }] },
};

export function TopBar({ portal, session, children }: { portal?: Portal; session: Session | null | undefined; children?: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const config = portal ? PORTALS[portal] : null;
  return (
    <header className="topbar">
      <Link className="brand" href="/" aria-label="ProofSkill home">
        <BrandMark />
        ProofSkill
      </Link>
      {config ? <span className="portal-name">{config.name} portal</span> : null}
      {config && session?.role === config.role ? (
        <nav className="nav" aria-label={`${config.name} portal`}>
          {config.nav.map((item) => (
            <Link key={item.href} href={item.href} aria-current={pathname === item.href ? "page" : undefined}>
              {item.label}
            </Link>
          ))}
        </nav>
      ) : null}
      {children}
      <div className="topbar__right">
        <span className="synthetic" title="All data in this prototype is invented (assumption A6)">
          Synthetic data
        </span>
        {session ? (
          <>
            {!config && session.role !== "platform_admin" ? (
              <Link className="btn btn--secondary" href={HOME_BY_ROLE[session.role]} style={{ minHeight: 40 }}>
                My portal
              </Link>
            ) : null}
            <span className="account" title={session.username}>
              <span className="avatar" aria-hidden="true">
                {session.username.slice(0, 1)}
              </span>
              <span className="account__name">{session.username}</span>
            </span>
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
        ) : session === null && pathname !== "/signin" && !pathname.startsWith("/v/") ? (
          <Link className="btn btn--primary" href="/signin" style={{ minHeight: 40 }}>
            Sign in
          </Link>
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
        <img src="/art/privacy.webp" alt="" width={132} height={130} />
        <h1 className="title">Sign in to the {config.name.toLowerCase()} portal</h1>
        <p className="muted prose">
          {session ? `You are signed in as ${session.username}, which is not a ${config.role} account. ` : ""}
          This page needs a <span className="mono">{config.role}</span> account.
        </p>
        <Link className="btn btn--primary" href={`/signin?next=${encodeURIComponent(pathname)}`}>
          Sign in
        </Link>
      </div>
    );
  } else {
    content = children(session);
  }
  return (
    <div className="portal">
      <Canopy />
      <TopBar portal={portal} session={session} />
      <main className="page">{content}</main>
    </div>
  );
}

/** The solid royal band behind the top bar and page head; the glass below overlaps its edge. */
export function Canopy() {
  return <div className="canopy" aria-hidden="true" />;
}

/** Page heading with the role's 3D art. */
export function PageHead({ title, lede, art, action }: { title: string; lede: ReactNode; art?: string; action?: ReactNode }) {
  return (
    <div className="page-head">
      <div className="page-head__text">
        {art ? <img className="page-head__art" src={`/art/${art}.webp`} alt="" width={84} height={84} /> : null}
        <div>
          <h1>{title}</h1>
          <p className="muted">{lede}</p>
        </div>
      </div>
      {action}
    </div>
  );
}
