// Seeded synthetic accounts (api/app/seed.py), listed so a demo can switch roles in one click.
// The names are synthetic display names for the sign-in page; the usernames are the real logins.
// One-click sign-in goes through app/api/demo-signin, which holds the shared demo password on the
// server (DEMO_PASSWORD); it is never in git or in the browser.
export const DEMO_GROUPS = [
  {
    role: "Issuer admin",
    short: "Issuer",
    key: "KeyI",
    art: "issuer",
    blurb: "Issue and revoke",
    portal: "issuer portal",
    accounts: [
      { username: "admin.iss001", name: "Rina Wijaya", detail: "Admin, Unit Pelatihan Contoh · ISS-001" },
      { username: "admin.iss002", name: "Bima Saputra", detail: "Admin, Himpunan Mahasiswa Contoh · ISS-002" },
    ],
  },
  {
    role: "Holder",
    short: "Holder",
    key: "KeyH",
    art: "holder",
    blurb: "Share a credential",
    portal: "holder portal",
    accounts: [
      { username: "holder.a", name: "Alya Putri", detail: "Participant · HLD-2026-0007" },
      { username: "holder.b", name: "Dimas Nugroho", detail: "Participant · HLD-2026-0008" },
    ],
  },
  {
    role: "Verifier",
    short: "Verifier",
    key: "KeyV",
    art: "verifier",
    blurb: "Check and read skill fit",
    portal: "verifier portal",
    accounts: [
      { username: "verifier.a", name: "Nadia Rahman", detail: "Recruiter, PT Contoh Digital" },
      { username: "verifier.b", name: "Fajar Hidayat", detail: "Selection committee, Beasiswa Contoh" },
    ],
  },
] as const;

export type DemoGroup = (typeof DEMO_GROUPS)[number];

/** The only usernames the one-click route signs in. */
export const DEMO_USERNAMES: readonly string[] = DEMO_GROUPS.flatMap((group) => group.accounts.map((account) => account.username));

/** The seeded holder references, offered as quick fills on the issue form, named like their accounts. */
export const DEMO_HOLDERS = [
  { holderRef: "HLD-2026-0007", name: "Alya Putri" },
  { holderRef: "HLD-2026-0008", name: "Dimas Nugroho" },
] as const;
