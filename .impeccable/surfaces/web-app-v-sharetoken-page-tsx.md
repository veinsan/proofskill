---
version: 1
slug: "web-app-v-sharetoken-page-tsx"
primary_target: "web/app/v/[shareToken]/page.tsx"
related_targets: []
---

# Surface: Verifier result page

Route (planned): `/v/[shareToken]`, which matches the share-link format in report 9.3 (`/v/sk_…`). Mode: Operate.

Scope: this is the page a verifier reaches from a holder's share link or QR code. It runs verification (API-06). When the result is VALID, it offers skill matching (API-07) for a position.

Audience and job: a recruiter, selection committee member, or lecturer at an office laptop in daylight, screening applications across several tabs. They decide within seconds whether to rely on the credential and how its verified skills relate to the position.

Content and states:

- **Results:** VALID, REVOKED (shown with the issuer's reason), TAMPERED (credential data withheld), and ISSUER_UNAUTHORIZED. Each result shows three separate checks with their reasons.
- **What else is shown:** only the fields in the holder's scope, plus the chain reference.
- **Errors:** 404 SHARE_LINK_NOT_FOUND, 410 SHARE_LINK_EXPIRED, 503 REGISTRY_UNAVAILABLE.
- **Matching:** labeled REKOMENDASI, with matched skills, missing requirements, limitations, and model version. Its error states are 409, 403, 422, and 503 AI_UNAVAILABLE. Verification stays usable when matching fails.

Constraints:

- No candidate search or candidate lists.
- Matching is available only after a VALID result, and only to the verifier who ran that verification.
- No total score.
- Failures are explained without accusing the holder.
- Hot pink appears only on "Check skill fit", and that button is absent when the result is not VALID.

Memorable moment: the stub reads solid navy when the credential is cleared, and turns hollow and hatched when it is not.

Unresolved:

- The exact hatched treatment of the stub for results other than VALID.
- The phone layout. The proposal is that the stub stacks under the pass.
- The composition of the share-link error pages.

## Direction contract

THESIS: The shared credential is a pass, and verification is the gate check: one pass, one verdict stub, three punched checks. It rejects the category default, which is a centered card with a big check badge.

OWN-WORLD: A white ground. A navy field grid with visible hairline cell rules. A perforated, solid-navy stub with notched ends. Condensed, tracked capital labels sit over wider-set values, and codes and hashes are set in a mono face. The only chromatic color is hot pink, used on the one action to press.

STORY: The verifier reads the verdict and its plain-English sentence, then sees which of the three checks passed and what the holder chose to share. They ask for skill fit and read a labeled recommendation, and they still make the decision.

FIRST VIEWPORT: A navy top bar 64px tall. The left two thirds hold the pass: issuer code to credential code at 46px, then program, dates, criteria, skills, and shared scope in ruled cells. On the pass's right edge, the stub shows VALID at 64px over three check rows and the chain reference. The right third is the skill-fit panel: position inputs, the hot-pink "Check skill fit" button, then the REKOMENDASI rows.

FORM: Boarding Pass Gate, candidate 3 of 7 on my ordered list, assigned by the roll. seed:130003625dad81d7. Raises:

- From the split-flap board: fixed cells.
- From the warm consumer app: a plain-English sentence with every verdict.
- From labanotation: claim and confirmation mirrored across the perforation.
- From the botanical folio: one fixed pass scale across all portals.
- From the streaming title wall: one work area in focus at a time.
- From the Crouwel grid: visible cell rules.

The chosen sketch is `.impeccable/mocks/decision/assigned.html`.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
