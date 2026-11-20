---
version: beta
name: ProofSkill
description: Verifiable training credentials. Liquid glass over solid royal blue and generated 3D shapes; each credential is a pass, and verification is the gate check.
colors:
  ink: "#0E1A3B"
  ink-2: "#3B4566"
  ink-3: "#5F6887"
  royal: "#2453D6"
  royal-600: "#1C43B8"
  royal-900: "#10266B"
  royal-50: "#EEF2FD"
  seal: "#F7A8C4"
  action: "#FF7AAE"
  action-hover: "#FF93BD"
  paper: "#E9EFFC"
  white: "#FFFFFF"
  line: "rgba(14, 26, 59, 0.10)"
  line-strong: "rgba(14, 26, 59, 0.18)"
  glass: "rgba(255, 255, 255, 0.62)"
  glass-strong: "rgba(255, 255, 255, 0.82)"
  glass-edge: "rgba(255, 255, 255, 0.80)"
  glass-dark: "rgba(255, 255, 255, 0.14)"
typography:
  display:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 6vw, 5.5rem)"
    fontWeight: 800
    lineHeight: 0.9
    letterSpacing: "-0.05em"
  section:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 5vw, 4rem)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "-0.045em"
  page-title:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 3vw, 2.375rem)"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  verdict:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "4rem"
    fontWeight: 800
    lineHeight: 1
  code-display:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.25
  body:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
  small:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.3
  button:
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 650
    lineHeight: 1.2
  mono:
    fontFamily: "'Red Hat Mono', ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    fontFeature: "'tnum'"
rounded:
  sm: "10px"
  md: "16px"
  lg: "24px"
  xl: "36px"
  hero: "44px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
  3xl: "48px"
effects:
  blur: "blur(22px) saturate(170%)"
  lift: "inset 0 1px 0 rgba(255,255,255,.9), 0 24px 48px -28px rgba(16,38,107,.35), 0 2px 6px rgba(16,38,107,.06)"
  ease-out: "cubic-bezier(0.16, 1, 0.3, 1)"
---

# Design System: ProofSkill

`web/app/globals.css` implements this file. When a token changes, change both.

## Overview

**North star: "Proof, not promises."** ProofSkill turns a certificate into something a stranger can check in seconds. The interface should feel the way that check feels: calm, clear, and safe. It takes its palette and 3D language from the team's deck (royal blue, a soft pink seal, cream paper, clay-like 3D objects) and sets them in liquid glass: frosted white surfaces that float over soft colour fields, with one strong royal-blue panel per page where the story starts.

- **Glass for what floats, white for what you read.** Navigation, panels, passes, and hero readouts are frosted glass with a bright top edge. Reading surfaces (inputs, the confirmation region, share results) are near-solid white, so text never sits on busy blur.
- **One bold place per page.** On the landing page it is the royal-blue hero with the huge "Proof, not promises." and the 3D certificate. In the portals it is the pass's stub. Everything around it stays quiet.
- **Safety is shown, not claimed.** The landing page says exactly what goes on the registry and what never does. The verifier sees three separate checks with reasons, not a badge.

## Colors

- **Ink** (#0E1A3B): all body text, the dark skill-fit band, check rings, and the hatching on a not-cleared stub. **Ink 2** (#3B4566) is secondary text, and **Ink 3** (#5F6887, 4.9:1 on white) is labels, helper lines, and "Not shared".
- **Royal** (#2453D6) is the brand: the hero and sign-in panels, the cleared stub, the avatar, active status, links, and focus rings. **Royal 600 / 900** shade it, and **Royal 50** (#EEF2FD) tints chips, selected options, and good-news notices.
- **Seal** (#F7A8C4) is the deck's pink seal. It marks the REKOMENDASI tag and warms the blue panels as a soft radial glow. It never marks an action.
- **Action** (#FF7AAE, hover #FF93BD) is the one button to press, always with Ink text (7.3:1). White text on it is not allowed.
- **Paper** (#E9EFFC) is a light blue page ground. Generated 3D shapes (`shapes`, `arch`, `tiles`) sit fixed behind it so the glass has colour to refract.

### Named rule
**The Solid Colour Rule.** Colour comes from solid fills and the 3D art, not gradient washes. Royal panels are flat royal with a faint ledger grid; the only gradients left are that grid's lines and the loading shimmer.

### Named rules
**The One Press Rule.** Action pink appears on the single control that moves the task forward in each work area: Sign in, Issue credential, Create share link, Check skill fit, or Revoke credential (only inside its confirmation region). A disabled action keeps the colour at 45% opacity and loses its glow.

**The No Traffic Light Rule.** States are words, icons, and fill, never red, green, or amber. A cleared credential gets a royal stub with filled dots. A credential that is not cleared gets a white stub with ink hatching behind its verdict word and hollow rings on the failed checks.

## Typography

**Plus Jakarta Sans** (chosen 2026-11-20 for a modern, clean voice; designed in Jakarta) carries everything human. Display lines are set heavy (800) and tight (-0.035 to -0.045em). **Red Hat Mono** is only for machine values: IDs, hashes, tokens, timestamps, and check states.

- Display headlines may use a two-tone line: the second line at 55% white on blue, or 32% ink on paper ("Three steps. Zero admin emails."). That is the only typographic accent; single words are never highlighted.
- Labels are sentence case at 0.8125rem, weight 500, in Ink 3. No all-caps tracked eyebrows.
- Body lines stay under about 64 characters.

## Layout

- **Top bar:** a floating glass pill, sticky 12px from the top, max 1280px wide. Brand mark and wordmark, the portal name chip, a segmented nav (white pill on the active item), then Synthetic data and the account button (avatar, name, chevron) on the right. The account button opens a small menu with the username, the role, and a translucent pink-red Sign out pill; Sign out always asks once in a modal dialog (Cancel / Sign out) before it signs out and returns to `/`. Signed-out pages show a pink Sign in instead, except on `/signin` and on a share link's page, which has its own inline sign-in. Below 1024px the nav moves to a second row; below 768px section anchors and the account name hide (the avatar stays, since it is the way to sign out) so the bar stays one row.
- **Landing (`/`):** hero panel (44px radius, ledger grid, 3D certificate with floating glass readouts) → "How it works" as three numbered steps with 3D art (a real sequence: Issue, Share, Verify) → the dark skill-fit band → "Safe by design" (on the registry vs. never on the registry, then four rules) → demo band with one chip per role → footer.
- **Sign in (`/signin`):** blue panel with the 3D certificate on the left, a glass form on the right, as simple as SafeTrip's demo entry and with no password anywhere: "Continue to the demo", three role tiles (Issuer, Holder, Verifier, each with its 3D art and one line; the chosen tile turns solid royal), an Account picker, and one pink "Enter … portal" button that signs in through the web server's demo password. The picker is a styled listbox, not a native select: a royal initials avatar, the synthetic name, the role and organisation, the ID as a small royal tag, and the login name in mono; it opens a solid white list with a check on the chosen account and works with the arrow keys, Home, End, Enter, and Escape. Alt+I, Alt+H, and Alt+V pick a role (hidden on phones, where the tiles stack and the ID moves under the name). `?u=<username>` preselects that role and account, and `?next=` returns to the page that asked for sign-in. No middle dots in this block. A share link's page uses the same block with only the verifiers and a "Sign in and verify" button.
- **Portals:** a solid royal canopy (330px, grid lines, 44px bottom radius) sits behind the top bar and the page head, which turns white on it. The glass content below overlaps the canopy's edge. The page head has the role's 3D art (84px), a title, and one sentence, with the primary action on the right. The verify page shows the canopy once a verifier is signed in. Two work areas at most: a fluid main area and a 480px side panel (420px below 1280px, stacked below 1024px).
- **Breakpoints:** 1280, 1024, and 768px. Below 768px the stub sits above the pass body so the verdict is read first on a phone.

## Surfaces and depth

- **Glass:** `glass` fill, `blur` backdrop, 1px `glass-edge` border, and `lift` shadow (a bright inset top edge plus a long, soft royal shadow). Used for the top bar, panels, the pass, tables, holder cards, steps, and empty states.
- **Glass on blue:** `glass-dark` with a 32% white edge, used for buttons and chips on the hero and blue panels. Hero readouts are tinted toward navy so white text holds contrast even over the cream certificate.
- **Radii have rank:** 44px hero panels, 36px passes and feature cards, 24px panels and tables, 16px inputs and notices, 10px small chips, pill for buttons and tags.

## Motion

One orchestrated moment per page, then stillness.

- **Show up:** every page's top-level blocks rise 18px from a 10px blur over 700ms on `ease-out`, staggered by 70ms. The second work area follows 160ms later.
- **Hero:** the two headline lines ("Proof," and "not promises.", never wrapped) rise in turn, the certificate settles in from a slight tilt without blur and then floats as a live 3D object (three.js: a slow rise and fall with a gentle sway that leans toward the pointer; still under reduced motion, paused off screen), and the glass readouts arrive last. The WebP holds its place until the first 3D frame and stays when WebGL is unavailable.
- **Verdict:** the verdict word lands with one stamp (scale 1.18 → 1 with blur), then the three checks rise in order. This is the only flourish in the portals.
- **Results:** similarity bars grow from the left, and a new share link or skill-fit result scrolls itself into view.
- **Scroll:** every page scrolls through Lenis (lerp 0.09), so a wheel notch eases over about half a second instead of jumping; anchor links land 96px below the top, clear of the top bar. `.reveal` blocks rise 36px and settle from 98.5% scale over about a second as they enter the viewport, once, with siblings 90ms apart (at most 360ms). Elements with `data-parallax` drift against the scroll at their own speed: positive speeds lag (the hero certificate 0.1, step and ledger art 0.08–0.1, the portal page-head art 0.12, the sign-in certificate 0.06), negative ones run ahead (the hero's glass readouts −0.06 to −0.16), and anything in the first screen starts exactly where the layout puts it. The fixed backdrop shapes slide up slightly as the page scrolls (capped). All of it lives in `web/components/smooth-scroll.tsx`.
- `prefers-reduced-motion` turns every animation, the parallax, and smooth scroll off; reveal blocks are then simply visible.

## 3D art

Thirteen clay-style objects in the deck's palette, in `web/public/art/` as transparent WebP (about 40 KB each). `certificate` comes from the deck. The rest were generated with Figma AI (file "ProofSkill web assets") and cut out of their white ground: `issuer` (stamp), `holder` (phone with QR), `verifier` (magnifier and shield), `chain` (linked cubes), `privacy` (padlock), `match` (puzzle), `empty` (tray), `audit` (clipboard), `closed` (broken link and hourglass), and three abstract background pieces, `shapes`, `arch`, and `tiles`. The art illustrates a role or a state and never carries information the text does not also give, so every image has empty alt text.

## Components

### Pass (signature component)
The credential is one object in all three portals: a glass body and a stub across a dashed perforation.
- **Body:** the code pair (issuer code → credential code), then ruled two-column field cells. Fields the API withholds read "Withheld" and fields outside the share scope read "Not shared", in italic Ink 3, never as empty cells.
- **Registry stub (issuer, holder):** "Blockchain registry status", the status word, one sentence, then commitment and transaction hash in mono.
- **Verification stub (verifier):** "Blockchain registry · checked {UTC}", the verdict, one sentence, the three checks (Integrity, Issuer, Status) with reasons and states, then the transaction hash and VER- ID.
- **Cleared (VALID, ACTIVE):** solid royal, white text, filled dots. **Not cleared (REVOKED, TAMPERED, ISSUER_UNAUTHORIZED):** white with hatching behind the word and rings on failed checks.

Verdict sentences never accuse the holder:
- **VALID:** "Issued by an authorized issuer, unchanged since issuance, and still active. You can rely on it and check skill fit."
- **REVOKED:** "The issuer revoked this credential. Reason: {reason}. Do not rely on it for this application."
- **TAMPERED:** "The credential data no longer matches what the issuer recorded, so its details are withheld. Ask the holder for a new link."
- **ISSUER_UNAUTHORIZED:** "The issuer of this credential is not authorized on the registry, so it cannot be relied on."

### Buttons
Pill-shaped, at least 46px tall. **Primary:** action pink with ink text and a pink glow, lifting 1px on hover and scaling to 0.97 on press. **Secondary:** frosted white with a `line-strong` border. **On dark:** `glass-dark` for blue panels. **Quiet:** text-only for row actions (Copy, Revoke, Download QR). An irreversible revocation always passes through an inline confirmation region (1.5px ink border) that restates the consequence before the pink button commits.

### Inputs
16px radius, at least 48px tall, near-white fill. Focus turns the border royal with a 4px royal halo. Errors use a 2px ink border, a ring icon, a plain sentence, and the API code verbatim; there is no red. Checkbox options are full-width rows that turn Royal 50 when checked. The issue form offers the seeded holder references as one-click chips.

### Tags and status
- REKOMENDASI is a seal-pink mono tag, always beside "AI Gemini models" and the sentence "A recommendation, not a decision. No total score."
- Status in lists is a pill: `active` in Royal 50 with a filled dot, `revoked` outlined with a ring.
- Skill chips are Royal 50 pills with the SK- ID in mono.

### Lists, cards, empty states
- Issuer credentials and the audit log are glass tables (IDs and times in mono).
- Holder credentials are cards that lift 3px on hover, because a person scans a handful rather than a ledger.
- Empty and error states are glass blocks with a 3D object, a title, one sentence, and at most one action that says what to do next.

## Do's and Don'ts

### Do
- Keep action pink on one control per work area, with ink text.
- Pair every verdict enum with its sentence, and show the three checks separately.
- Keep "Synthetic data" visible while demo data is in use (in the top bar everywhere except the landing bar on phones, whose footer says it).
- Show only fields inside the holder's scope; say "Not shared" for the rest.
- Keep API enums and error codes verbatim in English UI copy.
- Let the verdict, status word, and codes scale to their container; an enum breaks only after "_".

### Don't
- Don't use red, green, or amber for states.
- Don't put pink on links, status, icons, or focus rings, or use white text on it.
- Don't build candidate search, browse, ranking, or any total skill score.
- Don't show AI output without REKOMENDASI, its limitations, and the not-a-decision line.
- Don't put text directly on heavy blur; give it a white or navy-tinted surface.
- Don't add gradient colour washes; use solid royal, light blue paper, and the 3D art.
- Don't add motion that plays on its own beyond the page's show-up sequence, the 3D certificate's float, and the verdict stamp. Scroll-linked motion (reveal, parallax) moves only while the reader scrolls.
