"use client";

import Link from "next/link";
import { CheckIcon, CrossIcon, DotIcon } from "@/components/icons";
import { TopBar } from "@/components/portal-shell";
import { DEMO_GROUPS } from "@/lib/demo";
import { useSession } from "@/lib/session";
import { Certificate3D } from "@/components/certificate-3d";

const STEPS = [
  {
    art: "issuer",
    title: "Issue",
    body: "After a participant passes, the organizer issues the credential. Only a salted fingerprint of it, the issuer, and its status go to the blockchain registry.",
    who: "Training organizer",
  },
  {
    art: "holder",
    title: "Share",
    body: "The participant picks which fields a reader may see and for how long, then sends a link or QR code. It fits LinkedIn's Credential URL field.",
    who: "Participant",
  },
  {
    art: "verifier",
    title: "Verify",
    body: "A recruiter opens the link. ProofSkill recomputes the fingerprint and reads the registry: integrity, issuer, and status. No admin in the loop.",
    who: "Recruiter or committee",
  },
] as const;

const RULES = [
  { title: "No candidate search", body: "Credential data leaves only through a link its owner made. There is nothing to browse." },
  { title: "The AI never sees who", body: "Skill fit reads verified skills and the position text. Never a name or an ID number." },
  { title: "History is kept", body: "A revocation is a new transaction. The original record is never overwritten." },
  { title: "Checks without the AI", body: "If the AI is down, verification still works. Only skill fit waits." },
] as const;

export default function Landing() {
  const session = useSession();
  return (
    <>
      <TopBar session={session}>
        <nav className="nav nav--sections" aria-label="Sections">
          <a href="#how">How it works</a>
          <a href="#safety">Safety</a>
          <a href="#try">Demo</a>
        </nav>
      </TopBar>

      <main className="landing">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero__copy">
            <span className="hero__kicker">
              <span className="tag">Testnet</span>
              Anchored on the Base Sepolia public testnet
            </span>
            <h1 id="hero-title">
              <span>Proof,</span>
              <span>not promises.</span>
            </h1>
            <p className="hero__lede">
              Issue training certificates that a recruiter can check in seconds with a free verifier account: unchanged, from an
              authorized organizer, and not revoked. No emails to an admin, no personal data on the chain.
            </p>
            <div className="hero__actions">
              <Link className="btn btn--primary" href="/signin">
                Sign in
              </Link>
              <a className="btn btn--on-dark" href="#how">
                See how it works
              </a>
            </div>
          </div>

          <div className="hero__visual" aria-hidden="true">
            <Certificate3D className="hero__art" width={705} height={720} parallax={0.1} />
            <div className="float float--verdict" data-parallax="-0.12">
              <span className="label">Verification result</span>
              <strong>VALID</strong>
              <ul>
                <li>
                  <span>Integrity</span>
                  <span>PASS</span>
                </li>
                <li>
                  <span>Issuer</span>
                  <span>PASS</span>
                </li>
                <li>
                  <span>Status</span>
                  <span>ACTIVE</span>
                </li>
              </ul>
            </div>
            <div className="float float--time" data-parallax="-0.06">
              <strong>0.44 s</strong>
              <span>median check on Base Sepolia</span>
            </div>
            <div className="float float--seal" data-parallax="-0.16">
              <span className="tag tag--seal">REKOMENDASI</span>
              <span className="small">Skill fit, never a score</span>
            </div>
          </div>

          <div className="hero__strip" aria-hidden="true">
            <span>II3120 Kelompok 02, Institut Teknologi Bandung</span>
          </div>
        </section>

        <section className="section" id="how" aria-labelledby="how-title">
          <div className="section__head reveal">
            <h2 id="how-title">
              Three steps. <span>Zero admin emails.</span>
            </h2>
            <p>
              A certificate today is a PDF that only its issuer can vouch for. ProofSkill turns it into a record a verifier can check on
              their own, while the participant decides who sees what.
            </p>
          </div>
          <ol className="steps">
            {STEPS.map((step) => (
              <li key={step.title} className="step reveal">
                <div className="step__art">
                  <img src={`/art/${step.art}.webp`} alt="" width={160} height={168} loading="lazy" data-parallax="0.08" />
                </div>
                <span className="step__num" aria-hidden="true" />
                <h3>{step.title}</h3>
                <p>{step.body}</p>
                <p className="step__who">{step.who}</p>
              </li>
            ))}
          </ol>

          <div className="fit reveal">
            <div>
              <span className="tag tag--seal">REKOMENDASI</span>
              <h3 style={{ marginTop: 16 }}>Then, read the skills against your opening.</h3>
              <p>
                After a VALID check, paste the position description. You get each matched requirement with its similarity, the gaps, and
                the limits of the model. There is no total score. A person makes the call.
              </p>
            </div>
            <div className="fit__demo" aria-label="Example skill fit">
              <div className="fit__row">
                <span>
                  OWASP Top 10
                  <i>&ldquo;menganalisis kerentanan aplikasi web&rdquo;</i>
                </span>
                <span className="sim">
                  <span style={{ width: "85%" }} />
                </span>
                <span className="mono">0.85</span>
              </div>
              <div className="fit__row">
                <span>
                  Web Security Testing
                  <i>&ldquo;melakukan pengujian keamanan dasar&rdquo;</i>
                </span>
                <span className="sim">
                  <span style={{ width: "85%" }} />
                </span>
                <span className="mono">0.85</span>
              </div>
              <p className="fit__miss">Not covered: &ldquo;memantau log dengan SIEM&rdquo;</p>
            </div>
          </div>
        </section>

        <section className="section" id="safety" aria-labelledby="safety-title">
          <div className="section__head reveal">
            <h2 id="safety-title">
              Safe by design. <span>Private by default.</span>
            </h2>
            <p>
              The blockchain only proves that a record exists and has not changed. Everything personal stays off it, and every action is
              written to an audit log.
            </p>
          </div>
          <div className="safety">
            <div className="ledger reveal">
              <div>
                <h3>On the registry</h3>
                <p className="small muted">Public, permanent, readable by anyone</p>
                <ul>
                  {["A salted SHA-256 fingerprint", "Which organizer issued it", "Active or revoked", "When it happened"].map((item) => (
                    <li key={item}>
                      <CheckIcon />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <img src="/art/chain.webp" alt="" width={132} height={95} loading="lazy" data-parallax="0.1" />
            </div>
            <div className="ledger ledger--off reveal">
              <div>
                <h3>Never on the registry</h3>
                <p className="small muted">Kept off-chain, shared only by the participant</p>
                <ul>
                  {["Names and ID numbers (NIK)", "Grades and documents", "Program details and skills", "Who viewed a credential"].map((item) => (
                    <li key={item}>
                      <CrossIcon />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <img src="/art/privacy.webp" alt="" width={132} height={130} loading="lazy" data-parallax="0.1" />
            </div>
          </div>
          <ul className="rules">
            {RULES.map((rule) => (
              <li key={rule.title} className="reveal">
                <b>{rule.title}</b>
                <span>{rule.body}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="try reveal" id="try" aria-labelledby="try-title">
          <div>
            <h2 id="try-title">Try it with a demo account.</h2>
            <p>Pick a role. Every account and record here is synthetic, so you can issue, share, verify, and revoke freely.</p>
            <div className="try__roles">
              {DEMO_GROUPS.map((group) => (
                <Link key={group.role} className="role-chip" href={`/signin?u=${group.accounts[0].username}`}>
                  <img src={`/art/${group.art}.webp`} alt="" width={36} height={36} />
                  {group.role}
                </Link>
              ))}
            </div>
          </div>
        </section>

        <footer className="footer">
          <span>ProofSkill. A prototype for II3120 Layanan Sistem dan Teknologi Informasi, Kelompok 02.</span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <DotIcon size={8} /> Synthetic data only, Base Sepolia testnet
          </span>
        </footer>
      </main>
    </>
  );
}
