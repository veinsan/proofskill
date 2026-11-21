# Portal screenshots

Captured 2026-11-21 with headless Chrome at 1440 wide (390 wide for the mobile capture) against the deployed stack, https://proofskill-two.vercel.app, signed in through the demo accounts. Reduced motion was emulated so every scroll-reveal block shows. All data is synthetic (assumption A6).

| File | Shows |
| --- | --- |
| `landing.jpg` | Landing page `/`: the product claim, the Base Sepolia testnet badge, and the 3D art |
| `signin.jpg` | Sign-in page `/signin`: role tiles and the one-press demo sign-in |
| `issuer-home.jpg` | Issuer portal: the credentials this issuer issued (API-13) |
| `issuer-issue-form.jpg` | Issuer portal: issue form with the catalog skill picker (API-08, API-02) |
| `issuer-credential.jpg` | Issuer portal: the pass with the ACTIVE registry stub and the revoke panel (API-03, API-09) |
| `issuer-audit.jpg` | Issuer portal: the audit log without sensitive payload (API-10) |
| `holder-home.jpg` | Holder portal: the holder's own credentials (API-12) |
| `holder-share-link.jpg` | Holder portal: scope and lifetime of a share link, and the link list (API-04, API-05) |
| `verifier-valid.jpg` | Verifier result page: VALID with three checks, scoped fields, skill-fit form (API-06, TC-04) |
| `verifier-skill-fit.jpg` | Verifier result page: REKOMENDASI with matched pairs, judge reasons, a not-covered requirement, limitations, and `modelVersion` (API-07, TC-08) |
| `verifier-revoked.jpg` | Verifier result page for a revoked credential: REVOKED with the issuer's reason, skill fit withheld (API-06, TC-06) |
| `verifier-tampered.jpg` | Verifier result page for a changed credential: TAMPERED, details withheld (API-06, TC-05) |
| `verifier-issuer-unauthorized.jpg` | Verifier result page for a deactivated issuer: ISSUER_UNAUTHORIZED (API-06, TC-16) |
| `verifier-valid-mobile.jpg` | Verifier result page on a phone: the verdict comes first |
