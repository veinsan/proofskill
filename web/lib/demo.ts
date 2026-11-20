// Seeded synthetic accounts (api/app/seed.py), listed so a demo can switch roles quickly.
// They share one password, which the ProofSkill team gives out for demos; it is never in git.
export const DEMO_GROUPS = [
  {
    role: "Issuer admin",
    art: "issuer",
    accounts: [
      { username: "admin.iss001", note: "ISS-001" },
      { username: "admin.iss002", note: "ISS-002" },
    ],
  },
  {
    role: "Holder",
    art: "holder",
    accounts: [
      { username: "holder.a", note: "HLD-2026-0007" },
      { username: "holder.b", note: "HLD-2026-0008" },
    ],
  },
  {
    role: "Verifier",
    art: "verifier",
    accounts: [
      { username: "verifier.a", note: "Recruiter" },
      { username: "verifier.b", note: "Recruiter" },
    ],
  },
] as const;

/** The seeded holder references, offered as quick fills on the issue form. */
export const DEMO_HOLDERS = [
  { holderRef: "HLD-2026-0007", name: "Peserta Contoh A" },
  { holderRef: "HLD-2026-0008", name: "Peserta Contoh B" },
] as const;
