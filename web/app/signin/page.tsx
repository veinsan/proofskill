"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Certificate3D } from "@/components/certificate-3d";
import { DemoSignIn } from "@/components/demo-accounts";
import { TopBar } from "@/components/portal-shell";
import { DEMO_GROUPS } from "@/lib/demo";
import { HOME_BY_ROLE, type Session, useSession } from "@/lib/session";

// Resolve like the browser does, so "/\evil.com" or a tab inside "//" cannot redirect off site.
function isSameOrigin(path: string): boolean {
  try {
    return path.startsWith("/") && new URL(path, window.location.origin).origin === window.location.origin;
  } catch {
    return false;
  }
}

function SignIn() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next");
  const session = useSession();

  function go(signedIn: Session) {
    const home = HOME_BY_ROLE[signedIn.role];
    router.push(next && isSameOrigin(next) ? next : home);
  }

  return (
    <>
      <TopBar session={session} />
      <main className="page">
        <div className="signin">
          <section className="signin__panel" aria-labelledby="signin-lead">
            <div className="stack">
              <h1 className="signin__lead" id="signin-lead">
                One sign-in.
                <br />
                Your role opens the right door.
              </h1>
              <p>Issuers issue and revoke. Holders share. Verifiers check, then read skill fit. Every account here is synthetic.</p>
            </div>
            <Certificate3D className="signin__art" width={340} height={347} parallax={0.06} />
          </section>

          <section className="panel signin__form" aria-labelledby="signin-title">
            <div className="panel__head">
              <h2 className="title" id="signin-title">
                Continue to the demo
              </h2>
              <p className="small muted">Choose a role. Every account here is synthetic, so no password is needed.</p>
            </div>

            {session && session.role !== "platform_admin" ? (
              <p className="notice notice--good" role="status">
                <span>
                  You are already signed in as <b>{session.username}</b>. <Link href={HOME_BY_ROLE[session.role]}>Open your portal</Link>
                </span>
              </p>
            ) : null}

            {/* A demo account picked on the landing page arrives as ?u=… and is preselected. */}
            <DemoSignIn groups={DEMO_GROUPS} initial={params.get("u")} onSignedIn={go} />
          </section>
        </div>
      </main>
    </>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignIn />
    </Suspense>
  );
}
