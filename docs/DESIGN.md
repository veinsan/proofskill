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
  status-word:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "2.875rem"
    fontWeight: 800
    lineHeight: 1
    fontVariation: "'wdth' 120"
  brand:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 800
    lineHeight: 1
    fontVariation: "'wdth' 115"
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
    fontFeature: "'tnum'"
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
    padding: "0 14px"
  top-nav-item-active:
    textColor: "{colors.white}"
    typography: "{typography.small}"
    padding: "0 14px"
  synthetic-pill:
    textColor: "{colors.white}"
    typography: "{typography.mono-tag}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
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
  button-secondary-hover:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.navy}"
  button-quiet:
    textColor: "{colors.navy}"
    typography: "{typography.small}"
    padding: "6px 10px"
    height: "32px"
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
  notice:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.small}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  confirm:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
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
  state:
    textColor: "{colors.navy}"
    typography: "{typography.mono-tag}"
  table-cell:
    textColor: "{colors.navy}"
    typography: "{typography.body}"
    padding: "{spacing.md}"
  table-row-hover:
    backgroundColor: "{colors.tint}"
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
  url-box:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.navy}"
    typography: "{typography.mono}"
    rounded: "{rounded.sm}"
    padding: "8px 10px"
  qr:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.sm}"
    padding: "6px"
    size: "132px"
---

# Design System: ProofSkill

## Overview

**Creative North Star: "The Gate Pass"**

Every shared credential is a pass, and verification is the gate check that clears it or stops it. The interface borrows the discipline of a boarding pass checked at a gate. It has a field grid of tracked capital labels over clear values, codes set in a mono face, and a perforated stub that carries the verdict. It never borrows travel imagery: no planes, no airport words. The world contributes only type, palette, density, and one signature move (the stub). Navigation, inputs, buttons, and tables stay standard web controls.

This is a working tool for people in an office on a laptop in daylight, so the ground is light and the density is moderate. A verifier should understand the verdict, the three checks, and what the holder chose to share within seconds, then press one button to read a skill-fit recommendation. Hot pink exists only on that button. Everything else is navy and white.

The same pass appears in all three portals: the issuer's credential page, the holder's credential page, and the verifier's result. Only the stub's content changes: the issuer and holder see the registry status, the verifier sees the verdict and its three checks. A credential therefore looks like the same object wherever it is seen.

**Key Characteristics:**
- White ground, navy structure, and a single hot-pink action. The color split follows the user's 60/30/10 rule.
- Field grid with drawn hairline cell rules. Alignment itself reads as precision.
- A perforated stub with notched ends holds the verdict and the three checks: integrity, issuer, and status. Solid navy when cleared, white with a hatched band when not.
- Plain-English sentences next to verbatim API enums (VALID, REVOKED, TAMPERED, ISSUER_UNAUTHORIZED, ACTIVE, REKOMENDASI).
- Flat surfaces with no shadows or gradients. Browser surfaces (selection, caret, scrollbar, focus) are themed in the same two inks.

## Colors

The palette has two inks on paper and one signal reserved for pressing.

### Primary
- **Gate Navy** (#0F1B3D): structure and voice. Used for the top bar, the cleared stub, all body and value text, pass outlines, table header rules, similarity fills, the QR modules, text selection, the caret, and focus rings. It covers roughly 30% of any screen.

### Secondary
- **Signal Pink** (#FF3D8B): the one action to press, and nothing else. It appears on the primary button only, at most once per work area, about 10% of the screen at most. Button text on it is Gate Navy (5.06:1). White text on Signal Pink fails contrast (3.34:1) and is not allowed.
- **Signal Pink Hover** (#FF5C9E): the primary button's hover state. It is lighter, not darker, so navy text keeps 5.85:1.

### Neutral
- **Paper White** (#FFFFFF): the ground and every card, pass, panel, and not-cleared stub. It covers roughly 60% of any screen.
- **Muted Ink** (#575F77): secondary text, field labels, helper lines, placeholders, and "Withheld" or "Not shared" values. It is 70% navy in white, at 6.35:1 on white.
- **Control Edge** (#878D9E): borders of inputs and other controls a user must find, and the scrollbar thumb. It is 50% navy in white, at 3.32:1 on white.
- **Rule** (#D9DBE0): decorative hairlines between field cells, table rows, and list rows, and the panel border. It is 16% navy in white and never marks a control boundary.
- **Tint** (#F3F4F5): quiet surfaces: similarity tracks, the share URL box, table row hover, the secondary button hover, the scrollbar track, loading skeletons, and the disabled button. It is 5% navy in white.

On navy, secondary text is Paper White at reduced opacity rather than a new color: nav items and Sign out at 72%, the portal name at 80%, stub labels at 75%, the cleared stub's perforation at 55%, the Synthetic data pill outline at 45%, and check-row rules at 25%.

### Named Rules
**The 60/30/10 Rule.** Paper White carries about 60% of every screen, Gate Navy about 30%, and Signal Pink 10% at most, only on the button the user should press. Measure it on every screen before it ships.

**The One Press Rule.** Signal Pink marks the single action that moves the task forward: "Sign in", "Issue credential", "Create share link", "Check skill fit", or "Revoke credential" (the last only inside its confirmation region). It never colors links, status, icons, focus rings, charts, or decoration. A disabled or unavailable action loses the pink entirely.

**The Diluted Navy Rule.** Every neutral is Gate Navy diluted in white (5%, 16%, 50%, or 70%), and every secondary tone on navy is white at an opacity. No other gray and no other hue enters the palette.

**The Two-Ink State Rule.** Verification and request states use words, icons, and fill, not new hues. A cleared credential gets a solid navy stub and filled dots. A credential that is not cleared gets a white stub with a band of 45° navy hatching (22% opacity) behind its verdict or status word, and hollow rings on the failed checks. Red, green, and amber are not part of this system.

## Typography

**Display, Body, and Label Font:** Archivo (variable width and weight, loaded with its `wdth` axis, with system-ui as fallback)
**Mono Font:** Red Hat Mono (with ui-monospace as fallback)

**Character:** Archivo's width axis does the work a boarding pass needs. Labels are condensed and tracked, while codes and the verdict are set wide and heavy. Red Hat Mono keeps machine values (IDs, hashes, tokens, timestamps) calm and compact, with tabular figures.

### Hierarchy
- **Verdict** (800, up to 4rem, width 125, line-height 1): only the verification result word in the verifier's stub. It scales to the stub's width: the stub is a size container and the word is set at the smaller of 4rem and the stub width divided by the word's estimated width in em (per-letter estimate with 10% slack). An enum may break only after "_".
- **Code display** (800, up to 2.875rem, width 120, line-height 1, -0.01em): the pass's code pair, issuer code to credential code (ISS-001 → CRD-0001). It shrinks with its column (at most 15% of the column width) and never wraps. The sign-in lead line uses the same face at 2.875rem.
- **Status word** (800, up to 2.875rem, width 120, line-height 1): ACTIVE or REVOKED in the registry stub on issuer and holder views. It scales and breaks like the verdict.
- **Brand** (800, 1.375rem, width 115): the ProofSkill wordmark in the top bar.
- **Title** (700, 1.375rem, width 108, line-height 1.3, balanced wrapping): work-area and panel titles such as "Revoke this credential".
- **Value** (500, 1rem, line-height 1.4): field values on the pass and in detail views.
- **Body** (400, 0.9375rem, line-height 1.45): sentences, inputs, and table rows. Keep lines at 75ch or less.
- **Small** (400, 0.8125rem, line-height 1.45): helper text, limitations, check reasons, notices, and navigation items.
- **Label** (600, 0.71875rem, width 72, letter-spacing 0.14em, uppercase): every field label, every table header, the portal name, and the single stub label.
- **Mono** (500, 0.8125rem, tabular figures): IDs (CRD-, ISS-, SHL-, VER-, MAT-, HLD-, SK-), hashes, share URLs, and timestamps.
- **Mono tag** (500 to 600, 0.6875rem, letter-spacing 0.06em, uppercase): tags (REKOMENDASI, AI · GEMINI MODELS), check states (PASS, FAIL, ACTIVE, REVOKED), table status words, and the Synthetic data pill.

### Named Rules
**The Label-Over-Value Rule.** Every field is a tracked capital label above its value, never "Label: value" on one line. Values align on a shared baseline.

**The Mono-for-Machines Rule.** Anything a machine issued (IDs, hashes, tokens, UTC timestamps) is set in Red Hat Mono. Human words are never set in mono. Long hashes are truncated in the middle (`0x0b9e242b…9ce3`), with the full value available to copy.

**The No-Eyebrow Rule.** No tag or label sits above a heading. Technology markers ride inside the content they mark: the stub's single label names the blockchain registry, and the AI · GEMINI MODELS tag sits in the REKOMENDASI row of the model's output, never above a panel title.

## Layout

The signed-in shell is a navy top bar 64px tall: the ProofSkill wordmark, the portal name (Issuer portal, Holder portal, or Verifier portal), portal navigation, and on the right a Synthetic data pill, the account name, and a Sign out text button. The content area below has 40px side padding (16px on phones), 24px top padding, and 40px bottom padding. Pages open with a page head (title and one sentence, with the page's primary action aligned to the bottom right) or a breadcrumb in Small Muted Ink with the current ID in mono.

Each screen has at most two work areas side by side: a fluid main area and a 500px side panel, with a 32px gap. On the verifier result page, the pass fills the main area and the skill-fit panel is the side panel. On issuer and holder screens, the main area holds a table or the pass, and the side panel holds its actions (revoke, share links).

The spacing rhythm is 4px-based: 4, 8, 12, 16, 24, 32, 40. Field cells use 14px vertical and 18px horizontal padding on each side of the cell rule. Leave more space above a section heading than below it.

Responsive behavior:
- **1280px and up:** two work areas, a 500px side panel and a 292px stub. The reference frame is 1440 × 900.
- **1024–1279px:** the side panel narrows to 420px and the stub to 260px.
- **768–1023px:** one column. The side panel moves below the main area, and the stub stays on the pass's right edge.
- **Below 768px:** the stub stacks above the pass body so the verdict is read first on a phone (where QR scans land). The dashed perforation becomes the stub's bottom border, and the notches sit at its bottom corners. Field cells become one column, the code pair stacks without its arrow, the portal name and account name hide, and the primary button in a page head or panel spans the full width.

The pass keeps one internal structure at every width; its display words scale to their containers instead of reflowing the grid.

## Elevation & Depth

The system is flat. Depth comes from two things only: solid navy fills (the top bar and the cleared stub) against Paper White, and rules (hairlines, the 1.5px pass outline, and the dashed perforation). No element casts a shadow, and no surface uses a gradient or blur. The secondary button draws its 1.5px navy border as an inset box-shadow so it does not change the button's size; that is a border, not elevation. Focus is shown with a 2px Gate Navy outline offset by 2px. On navy surfaces (the top bar and the cleared stub), the outline is Paper White.

### Named Rules
**The Flat Gate Rule.** No shadows and no gradients. A surface is either paper or navy, and the line between them is a rule or a perforation.

## Shapes

- **Large radius (16px):** passes, panels, and the sign-in account grid.
- **Medium radius (8px):** buttons, inputs, notices, the confirmation region, and dashed callouts.
- **Small radius (4px):** tags, skill chips, similarity bars, the URL box, the QR frame, and the hatched band behind a not-cleared verdict.
- **Pill:** only the top bar's Synthetic data pill.

Pass outlines are 1.5px Gate Navy. Field-cell rules and row dividers are 1px Rule. Input borders are 1px Control Edge (2px Gate Navy when invalid). Notices carry a 2px navy border.

**The perforation is the signature shape.** It is a 2px dashed line between the pass body and its stub, with a 24px circular notch (Paper White, 1.5px navy edge) cut at each end of the line.

**The Line Weight Rule.** Each border style has one meaning. Dashed 1px navy means "not covered": missing-requirement callouts and empty states only. Solid 1.5px navy encloses an object or an irreversible step: the pass, the account grid, the secondary button, and the revoke confirmation region. Solid 2px navy marks something that needs attention: notices and invalid inputs.

## Components

### Buttons
- **Shape:** gently rounded (8px), at least 44px tall, with 12px × 20px padding.
- **Primary:** Signal Pink with Gate Navy text in Archivo 700. Use one per work area, only for the action that advances the task. In a form panel it spans the panel's width.
- **Hover / Focus:** hover lightens to Signal Pink Hover. Focus adds a 2px navy outline offset by 2px. Pressing shifts the button 1px down. Transitions take 150ms ease-out, and there is no motion under `prefers-reduced-motion`.
- **Disabled / Unavailable:** Tint background with Muted Ink text and no pink. When an action is impossible in the current state, for example skill fit on a result that is not VALID, remove the button and explain why in one sentence instead.
- **Secondary:** Paper White with a 1.5px navy border and navy text; hover fills with Tint. Use it for Cancel, Review revocation, Copy link, and Go to sign in.
- **Quiet:** an underlined navy text button in Small 600, 32px tall, for row-level and utility actions: Copy and Revoke on a share-link row, and Download QR. Sign out in the top bar is the same pattern in white at 72%.
- **Irreversible actions:** "Revoke credential" starts as a secondary "Review revocation" button. It opens an inline confirmation region with a 1.5px solid navy border that restates the consequence ("The next verification of CRD-0001 will read REVOKED. This cannot be undone.") and quotes the reason the admin entered. The pink button commits only from that region, next to a secondary Cancel. Editing the reason closes the region.

### Pass (signature component)
The pass is one object, the credential, with the same structure everywhere.
- **Body:** Paper White inside a 1.5px navy outline with a 16px radius. At the top is the code pair (Issuer label, issuer code, issuer name → Credential label, credential code, issue detail) over a 1px Rule. Below it are ruled two-column field cells: program, completed date, link expiry, pass criteria, skills, and the scope the holder shared. Full-width cells span both columns.
- **Stub:** sits across the perforation and carries exactly one label, then the display word, one plain-English sentence, and the chain reference in mono at the bottom. There is no chip or tag above the display word.
- **Verification stub (verifier):** label "Blockchain registry · checked {UTC time}" (the time never breaks), the verdict, its sentence, the three check rows (Integrity, Issuer, Status: dot or ring, name, reason in Small, and the check state in mono tag), then the transaction hash and VER- ID.
- **Registry stub (issuer and holder):** label "Blockchain registry status", the status word ACTIVE or REVOKED, a sentence (anchored and active, or revoked by whom, when, and why), then the commitment and transaction hash.
- **Cleared stub (VALID, ACTIVE):** solid Gate Navy with white text, white-at-75% label, and filled check dots.
- **Not-cleared stub (REVOKED, TAMPERED, ISSUER_UNAUTHORIZED):** Paper White with a band of 45° navy hatching behind the verdict or status word. A failed check shows a hollow ring instead of a filled dot. Credential fields the API withholds (TAMPERED returns no credential data) render as "Withheld" in Muted Ink, and fields outside the share scope as "Not shared", never as empty cells.
- **Fixed cells:** a state change restyles a cell in place and never reflows the pass.
- **Mirrored rows:** each claim on the body lines up with the check that confirms it on the stub.

**Verdict sentence patterns.** These explain without accusing the holder:
- **VALID:** "Issued by an authorized issuer, unchanged since issuance, and still active. You can rely on it and check skill fit."
- **REVOKED:** "The issuer revoked this credential. Reason: {reason}. Do not rely on it for this application."
- **TAMPERED:** "The credential data no longer matches what the issuer recorded, so its details are withheld. Ask the holder for a new link."
- **ISSUER_UNAUTHORIZED:** "The issuer of this credential is not authorized on the registry, so it cannot be relied on."

### Tags and states
- **Tags:** transparent with a 1px outline in the current text color, Red Hat Mono uppercase, 4px radius.
- **REKOMENDASI row:** the first line of any AI output is a row with the REKOMENDASI tag, the AI · GEMINI MODELS tag, and "A recommendation, not a decision. No total score." in Small Muted Ink, over a 1px Rule.
- **Status in tables and lists:** the status word in mono tag next to a 10px filled dot (active) or hollow ring (revoked).
- **Skill chips:** a 1px navy outline at 4px radius, the skill label in Body with its SK- ID in Muted Ink mono beside it.

### Inputs / Fields
- **Style:** Paper White with a 1px Control Edge border, 8px radius, at least 40px tall. Text areas grow from 76px and resize vertically. Selects share the input style. Checkboxes are 18px with a navy accent.
- **Labels:** a tracked capital Label above every input, with a character count or helper line in Small Muted Ink below it where useful.
- **Focus:** the border turns Gate Navy and gains a 2px navy outline offset by 2px.
- **Error:** the border turns Gate Navy at 2px. A hollow-ring icon and a plain-English message sit under the field and quote the API's error code (for example `INVALID_POSITION_TEXT`). There is no red.
- **Notices:** request-level errors are a 2px navy box with an 8px radius, a ring icon, a bold one-line title, and the API message with its code.

### Skill-fit results
- **Matched row:** the skill label, the quoted position requirement it matched and the reason (both Small Muted Ink), a 6px similarity bar (Tint track with navy fill), and the per-pair similarity in mono. There is never a total score or a ranking.
- **Bar motion:** each fill grows once from the left (scaleX, 600ms, ease-out) when the result arrives; under `prefers-reduced-motion` it appears at full width.
- **Missing requirement:** a dashed 1px navy callout with an 8px radius that begins "Not covered:" and names the uncovered requirement.
- **Footer:** the limitations as a Small Muted Ink list, then the MAT- ID and model version in mono.

### Share links
- **Create:** scope checkboxes for what the holder shares, a lifetime select (1, 3, 7, or 30 days), and the pink "Create share link" button.
- **Result:** a 132px QR code (navy modules on white, rendered in the browser so the token never leaves the page) in a 1px Rule frame with a quiet Download QR button, beside the URL in mono on a Tint box and a secondary Copy link button.
- **List:** each existing link is a row over a 1px Rule with its scope, expiry or revocation time, and quiet Copy and Revoke buttons.

### Navigation
- **Top bar:** Gate Navy, 64px. Nav items fill the bar's height and are white at 72% in Small type; hover turns them full white.
- **Active item:** full white with a 2px white bottom border.
- **Below 1024px:** the nav moves to a second 44px row inside the top bar, under the wordmark, and scrolls sideways if it must. It is never hidden.
- **Synthetic data pill:** Red Hat Mono in a 1px white-at-45% outline, always visible while the prototype runs on synthetic data.

### Panels and tables
- **Panels:** Paper White with a 1px Rule border, 16px radius, and 24px padding. A panel head stacks the title over one Small Muted Ink sentence.
- **Tables (issuer credential list, holder credential list, audit log):** tracked capital Label headers over a 1.5px navy rule, 1px Rule row dividers, Tint on row hover, IDs and times in mono with tabular figures, and status as a word plus dot or ring. Audit rows show time, actor role, operation, object ID, and outcome only, never payload content.
- **Empty states:** a dashed 1px navy box with 24px padding, a title, one sentence, and at most one secondary action.
- **Loading:** Tint skeleton blocks at 4px radius in place of the content.

## Do's and Don'ts

### Do:
- **Do** keep Signal Pink (#FF3D8B) on exactly one action per work area, with Gate Navy text on it.
- **Do** pair every verdict enum with its plain-English sentence and show the three checks separately with their reasons.
- **Do** keep the Synthetic data pill visible on every screen while demo data is in use.
- **Do** show only the fields inside the holder's share scope, and say "Not shared" for anything outside it.
- **Do** name the blockchain registry in the stub's single label, and put the AI · GEMINI MODELS tag in the REKOMENDASI row of model output.
- **Do** write interface copy in English and keep API enums and error codes verbatim (VALID, REVOKED, TAMPERED, ISSUER_UNAUTHORIZED, REKOMENDASI, SHARE_LINK_EXPIRED, and so on).
- **Do** let the verdict, status word, and codes scale to their container instead of wrapping mid-word; an enum breaks only after "_".
- **Do** put the stub above the pass body below 768px so the verdict is read first.
- **Do** restate an irreversible action in a 1.5px solid navy confirmation region before the pink button commits it.

### Don't:
- **Don't** add red, green, amber, or any hue outside the eight color tokens. States are words, icons, and fill.
- **Don't** put Signal Pink on links, focus rings, status, icons, or decoration, or keep it on a disabled action.
- **Don't** use white text on Signal Pink (3.34:1 fails contrast).
- **Don't** build any candidate search, browse, list, or ranking surface, and never show a total or aggregate skill score.
- **Don't** show AI output without the REKOMENDASI tag, its limitations, and the statement that it is a recommendation, not a decision.
- **Don't** phrase a failed verification as an accusation against the holder.
- **Don't** place a tag, label, or chip above a heading or above the stub's display word.
- **Don't** use dashed borders for anything except "not covered" callouts and empty states.
- **Don't** use plane icons, airport vocabulary, or ticket illustrations. The pass is a field grid, not a picture of a ticket.
- **Don't** add shadows, gradients, glass, or blur.
