---
version: alpha
name: ProofSkill
description: Verifiable training credentials, checked at the gate. Each credential is a pass; verification is the gate check.
colors:
  navy: "#0F1B3D"
  white: "#FFFFFF"
  hot-pink: "#FF3D8B"
  hot-pink-hover: "#FF5C9E"
  ink-muted: "#575F77"
  control-edge: "#878D9E"
  rule: "#D9DBE0"
  tint: "#F3F4F5"
typography:
  verdict:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "4rem"
    fontWeight: 800
    lineHeight: 1
    fontVariation: "'wdth' 125"
  code-display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "2.875rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 120"
  title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.3
    fontVariation: "'wdth' 108"
  value:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.4
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.45
  small:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.71875rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.14em"
    fontVariation: "'wdth' 72"
  button:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 700
    lineHeight: 1.2
  mono:
    fontFamily: "'Red Hat Mono', ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.4
  mono-tag:
    fontFamily: "'Red Hat Mono', ui-monospace, monospace"
    fontSize: "0.6875rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.06em"
rounded:
  sm: "4px"
  md: "8px"
  lg: "16px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
  3xl: "40px"
components:
  top-bar:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.white}"
    height: "64px"
    padding: "0 40px"
  top-nav-item:
    textColor: "{colors.white}"
    typography: "{typography.small}"
    padding: "8px 14px"
  top-nav-item-active:
    textColor: "{colors.white}"
    typography: "{typography.small}"
    padding: "8px 14px"
  button-primary:
    backgroundColor: "{colors.hot-pink}"
    textColor: "{colors.navy}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "12px 20px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.hot-pink-hover}"
    textColor: "{colors.navy}"
  button-primary-disabled:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink-muted}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "12px 20px"
    height: "44px"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "9px 12px"
    height: "40px"
  panel:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  pass:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    rounded: "{rounded.lg}"
  pass-stub:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.white}"
    padding: "{spacing.xl}"
    width: "292px"
  pass-stub-not-cleared:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    padding: "{spacing.xl}"
    width: "292px"
  field-cell:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.value}"
    padding: "14px 18px"
  field-label:
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
  tag:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.mono-tag}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  skill-chip:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "4px 10px"
  similarity-track:
    backgroundColor: "{colors.tint}"
    rounded: "{rounded.sm}"
    height: "6px"
  similarity-fill:
    backgroundColor: "{colors.navy}"
    rounded: "{rounded.sm}"
    height: "6px"
  missing-requirement:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  status-pill:
    textColor: "{colors.white}"
    typography: "{typography.mono-tag}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
---

<!-- SEED: established with the user before implementation; re-run /impeccable document once there's code to capture the actual tokens and components. Values come from the user's pinned palette (2026-11-19) and the chosen decision sketch .impeccable/mocks/decision/assigned.html. -->

# Design System: ProofSkill

## Overview

**Creative North Star: "The Gate Pass"**

Every shared credential is a pass, and verification is the gate check that clears it or stops it. The interface borrows the discipline of a boarding pass checked at a gate. It has a field grid of tracked capital labels over clear values, codes set in a mono face, and a perforated stub that carries the verdict. It never borrows travel imagery: no planes, no airport words. The world contributes only type, palette, density, and one signature move (the stub). Navigation, inputs, buttons, and tables stay standard web controls.

This is a working tool for people in an office on a laptop in daylight, so the ground is light and the density is moderate. A verifier should understand the verdict, the three checks, and what the holder chose to share within seconds, then press one button to read a skill-fit recommendation. Hot pink exists only on that button. Everything else is navy and white.

The same pass appears at one fixed scale in all three portals: the issuer's confirmation, the holder's credential page, and the verifier's result. A credential therefore looks like the same object wherever it is seen.

**Key Characteristics:**
- White ground, navy structure, and a single hot-pink action. The color split follows the user's 60/30/10 rule.
- Field grid with drawn hairline cell rules. Alignment itself reads as precision.
- A perforated navy stub holds the verdict and the three checks: integrity, issuer, and status.
- Plain-English sentences next to verbatim API enums (VALID, REVOKED, TAMPERED, ISSUER_UNAUTHORIZED, REKOMENDASI).
- Flat surfaces with no shadows or gradients.

## Colors

The palette has two inks on paper and one signal reserved for pressing.

### Primary
- **Gate Navy** (#0F1B3D): structure and voice. Used for the top bar, the pass stub, all body and value text, pass outlines, similarity bars, and focus rings. It covers roughly 30% of any screen.

### Secondary
- **Signal Pink** (#FF3D8B): the one action to press, and nothing else. It appears on the primary button only, at most once per work area, about 10% of the screen at most. Button text on it is Gate Navy (5.06:1). White text on Signal Pink fails contrast (3.34:1) and is not allowed.
- **Signal Pink Hover** (#FF5C9E): the primary button's hover state. It is lighter, not darker, so navy text keeps 5.85:1.

### Neutral
- **Paper White** (#FFFFFF): the ground and every card, pass, and panel. It covers roughly 60% of any screen.
- **Muted Ink** (#575F77): secondary text, field labels, and helper lines. It is 70% navy in white, at 6.35:1 on white.
- **Control Edge** (#878D9E): borders of inputs and other controls a user must find. It is 50% navy in white, at 3.32:1 on white.
- **Rule** (#D9DBE0): decorative hairlines between field cells and list rows. It is 16% navy in white and never marks a control boundary.
- **Tint** (#F3F4F5): quiet surfaces, similarity tracks, and the disabled button. It is 5% navy in white.

### Named Rules
**The 60/30/10 Rule.** Paper White carries about 60% of every screen, Gate Navy about 30%, and Signal Pink 10% at most, only on the button the user should press. Measure it on every screen before it ships.

**The One Press Rule.** Signal Pink marks the single action that moves the task forward: "Check skill fit", "Issue credential", "Create share link", or "Revoke credential". It never colors links, status, icons, focus rings, charts, or decoration. A disabled or unavailable action loses the pink entirely.

**The Diluted Navy Rule.** Every neutral is Gate Navy diluted in white (5%, 16%, 50%, or 70%). No other gray and no other hue enters the palette.

**The Two-Ink State Rule.** Verification and request states use words, icons, and fill, not new hues. A cleared credential gets a solid navy stub. A credential that is not cleared gets a hollow stub with a navy outline and diagonal hatching. Red, green, and amber are not part of this system.

## Typography

**Display, Body, and Label Font:** Archivo (variable width and weight, with system-ui as fallback)
**Mono Font:** Red Hat Mono (with ui-monospace as fallback)

**Character:** Archivo's width axis does the work a boarding pass needs. Labels are condensed and tracked, while codes and the verdict are set wide and heavy. Red Hat Mono keeps machine values (IDs, hashes, tokens, timestamps) calm and compact.

### Hierarchy
- **Verdict** (800, 4rem, width 125, line-height 1): only the verification result word in the stub, such as VALID or REVOKED.
- **Code display** (800, 2.875rem, width 120, line-height 1): the pass's code pair, issuer code to credential code (ISS-001 → CRD-0001).
- **Title** (700, 1.375rem, width 108, line-height 1.3): work-area titles such as "Skill fit for a position".
- **Value** (500, 1rem, line-height 1.4): field values on the pass and in detail views.
- **Body** (400, 0.9375rem, line-height 1.45): sentences, inputs, and list rows. Keep lines at 75ch or less.
- **Small** (400, 0.8125rem, line-height 1.45): helper text, limitations, and navigation items.
- **Label** (600, 0.71875rem, width 72, letter-spacing 0.14em, uppercase): every field label.
- **Mono** (500, 0.8125rem): IDs (CRD-, ISS-, SHL-, VER-, MAT-, HLD-, SK-), hashes, share tokens, and timestamps.
- **Mono tag** (500, 0.6875rem, letter-spacing 0.06em, uppercase): tags such as BLOCKCHAIN REGISTRY, AI · EMBEDDING MODEL, and REKOMENDASI.

### Named Rules
**The Label-Over-Value Rule.** Every field is a tracked capital label above its value, never "Label: value" on one line. Values align on a shared baseline.

**The Mono-for-Machines Rule.** Anything a machine issued (IDs, hashes, tokens, UTC timestamps) is set in Red Hat Mono. Human words are never set in mono. Long hashes are truncated in the middle (`0x0b9e242b…9ce3`), with the full value available to copy.

## Layout

The shell is a navy top bar 64px tall. It holds the ProofSkill wordmark, the portal name (Issuer portal, Holder portal, or Verifier portal), portal navigation, a "Synthetic data" pill, and the signed-in account. The content area below has 40px side padding and 24px top padding.

Each screen has at most two work areas side by side: a fluid main area and a 500px side panel, with a 32px gap. On the verifier result page, the pass fills the main area and the skill-fit panel is the side panel. On issuer and holder screens, the main area holds a table or form, and the side panel holds the selected pass or its actions.

The spacing rhythm is 4px-based: 4, 8, 12, 16, 24, 32, 40. Field cells use 14px vertical padding with 18px gutters on each side of the cell rule. Leave more space above a section heading than below it.

Responsive behavior:
- **1280px and up:** two work areas. The reference frame is 1440 × 900.
- **1024–1279px:** the side panel narrows to 420px and the stub to 260px.
- **768–1023px:** one column. The side panel moves below the main area, and the stub stays on the pass's right edge.
- **Below 768px:** the stub stacks under the pass body, and the perforation turns horizontal. Field cells become one column. The primary button spans the full width.

The pass keeps one fixed internal scale at every width. Only its outer width changes.

## Elevation & Depth

The system is flat. Depth comes from two things only: solid navy fills (the top bar and the cleared stub) against Paper White, and hairline rules. No element casts a shadow, and no surface uses a gradient or blur. Focus is shown with a 2px Gate Navy outline offset by 2px. On navy surfaces, the outline is Paper White.

### Named Rules
**The Flat Gate Rule.** No shadows and no gradients. A surface is either paper or navy, and the line between them is a rule or a perforation.

## Shapes

- **Large radius (16px):** passes and panels.
- **Medium radius (8px):** buttons, inputs, and dashed callouts.
- **Small radius (4px):** tags, skill chips, and similarity bars.
- **Pill:** only the top bar's "Synthetic data" pill.

Pass outlines are 1.5px Gate Navy. Field-cell rules and row dividers are 1px Rule. Input borders are 1px Control Edge.

**The perforation is the signature shape.** It is a 2px dashed line between the pass body and its stub, with a 24px semicircular notch cut at each end of the line.

Dashed 1px navy outlines mean "not covered". They appear only on missing-requirement callouts and on empty states.

## Components

### Buttons
- **Shape:** gently rounded (8px), 44px tall, with 12px × 20px padding.
- **Primary:** Signal Pink with Gate Navy text in Archivo 700. Use one per work area, only for the action that advances the task.
- **Hover / Focus:** hover lightens to Signal Pink Hover (#FF5C9E). Focus adds a 2px navy outline offset by 2px. Pressing shifts the button 1px down. Transitions take 150ms ease-out, and there is no motion under `prefers-reduced-motion`.
- **Disabled / Unavailable:** Tint background with Muted Ink text and no pink. When an action is impossible in the current state, for example skill fit on a result that is not VALID, remove the button and explain why in one sentence instead.
- **Secondary:** Paper White with a 1.5px navy border and navy text. Use it for Cancel, Copy link, and Download QR.
- **Irreversible actions:** "Revoke credential" first opens a confirmation panel. The panel restates the consequence ("The next verification of CRD-0001 will read REVOKED. This cannot be undone.") and shows the reason the admin entered. The pink button commits only from that panel.

### Pass (signature component)
The pass is one object, the credential, shown at one fixed scale everywhere.
- **Body:** Paper White inside a 1.5px navy outline with a 16px radius. At the top is the code pair (issuer code → credential code) with the issuer name and issue time under each code. Below it are ruled field cells: program, completed date, link expiry, pass criteria, skills, and the scope the holder shared.
- **Stub:** sits across the perforation. It carries a BLOCKCHAIN REGISTRY tag, the check time, the verdict word, one plain-English sentence, the three check rows (Integrity, Issuer, Status), and the chain reference (transaction hash and VER- ID).
- **Cleared stub (VALID):** solid Gate Navy with white text and filled check dots.
- **Not-cleared stub (REVOKED, TAMPERED, ISSUER_UNAUTHORIZED):** Paper White with a navy outline and 45° navy hatching behind the verdict word. A failed check shows a hollow ring instead of a filled dot. Credential fields the API withholds (TAMPERED returns no credential data) render as "Withheld" in Muted Ink, never as empty cells.
- **Fixed cells:** a state change restyles a cell in place and never reflows the pass.
- **Mirrored rows:** each claim on the body lines up with the check that confirms it on the stub.

**Verdict sentence patterns.** These explain without accusing the holder:
- **VALID:** "Issued by an authorized issuer, unchanged since issuance, and still active. You can rely on it and check skill fit."
- **REVOKED:** "The issuer revoked this credential on {date}. Reason: {reason}. Do not rely on it for this application."
- **TAMPERED:** "The credential data no longer matches what the issuer recorded, so its details are withheld. Ask the holder for a new link."
- **ISSUER_UNAUTHORIZED:** "The issuer of this credential is not authorized on the registry, so it cannot be relied on."

### Tags
- **Style:** Paper White with a 1px navy outline (or white outline on navy), Red Hat Mono uppercase, 4px radius.
- **Technology markers:** BLOCKCHAIN REGISTRY on anything read from the chain, and AI · EMBEDDING MODEL on anything produced by the matching model. They make the two technologies visible wherever they act.
- **REKOMENDASI:** always the first line of any AI output, followed by "A recommendation, not a decision."

### Inputs / Fields
- **Style:** Paper White with a 1px Control Edge border, 8px radius, 40px tall. Text areas grow from 76px.
- **Labels:** a tracked capital Label above every input.
- **Focus:** the border turns Gate Navy and gains a 2px navy outline offset by 2px.
- **Error:** the border turns Gate Navy at 2px. A hollow-ring icon and a plain-English message sit under the field and quote the API's error code (for example `INVALID_POSITION_TEXT`). There is no red.

### Skill-fit results
- **Matched row:** the skill label, the quoted position requirement it matched (Muted Ink), a 6px similarity bar (Tint track with navy fill), and the per-pair similarity in mono. There is never a total score or a ranking.
- **Missing requirement:** a dashed 1px navy callout with an 8px radius that names the uncovered requirement.
- **Footer:** the limitations and the model version in Small, ending with "The hiring decision stays with you."

### Navigation
- **Top bar:** Gate Navy, 64px. Nav items are white at 72% opacity in Small type.
- **Active item:** full white with a 2px white underline.
- **Synthetic data pill:** Red Hat Mono in a 1px white-at-45% outline, always visible while the prototype runs on synthetic data.
- **Mobile:** nav items collapse into a menu button on the right of the top bar.

### Panels and tables
- **Panels:** Paper White with a 1px Rule border, 16px radius, and 24px padding.
- **Tables (issuer credential list, audit log):** standard sortable tables with tracked capital Label headers over a 1.5px navy rule, 1px Rule row dividers, and IDs in mono. Audit rows show time, actor role, operation, object ID, and outcome only, never payload content.

## Do's and Don'ts

### Do:
- **Do** keep Signal Pink (#FF3D8B) on exactly one action per work area, with Gate Navy text on it.
- **Do** pair every verdict enum with its plain-English sentence and show the three checks separately with their reasons.
- **Do** keep the "Synthetic data" pill visible on every screen while demo data is in use.
- **Do** show only the fields inside the holder's share scope, and say "Not shared" for anything outside it.
- **Do** mark chain-backed data with the BLOCKCHAIN REGISTRY tag and model output with the AI · EMBEDDING MODEL tag.
- **Do** write interface copy in English and keep API enums and error codes verbatim (VALID, REVOKED, TAMPERED, ISSUER_UNAUTHORIZED, REKOMENDASI, SHARE_LINK_EXPIRED, and so on).
- **Do** render the pass at the same internal scale on the issuer, holder, and verifier screens.

### Don't:
- **Don't** add red, green, amber, or any hue outside the eight color tokens. States are words, icons, and fill.
- **Don't** put Signal Pink on links, focus rings, status, icons, or decoration, or keep it on a disabled action.
- **Don't** use white text on Signal Pink (3.34:1 fails contrast).
- **Don't** build any candidate search, browse, list, or ranking surface, and never show a total or aggregate skill score.
- **Don't** show AI output without the REKOMENDASI tag, its limitations, and the statement that the decision stays with the verifier.
- **Don't** phrase a failed verification as an accusation against the holder.
- **Don't** use plane icons, airport vocabulary, or ticket illustrations. The pass is a field grid, not a picture of a ticket.
- **Don't** add shadows, gradients, glass, or blur.
