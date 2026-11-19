"""Synthetic seed for the local prototype (A-03, assumption A6).

Loads two issuers (also registered on-chain), one account per role plus the extra accounts
the TCs need, the skill catalog, and sample position descriptions. Every value is invented.

Run from api/: uv run python -m app.seed [--reset]
"""

import argparse

import psycopg
from psycopg.rows import DictRow

from app import db, ias, rgs

# Synthetic test credential shared by every local demo account. Never reuse it elsewhere.
DEMO_PASSWORD = "proofskill-demo"

# (issuer_id, name, unit_type, chain_account). The accounts are public Hardhat test accounts #1 and #2.
ISSUERS = [
    ("ISS-001", "Unit Pelatihan Contoh", "Unit pelatihan kampus", "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"),
    ("ISS-002", "Himpunan Mahasiswa Contoh", "Himpunan mahasiswa", "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"),
]

# (username, role, issuer_id, holder_ref). Two verifiers for TC-15, two issuers for TC-14,
# and an issuer_admin without an issuer for TC-02.
ACCOUNTS = [
    ("platform.admin", "platform_admin", None, None),
    ("admin.iss001", "issuer_admin", "ISS-001", None),
    ("admin.iss002", "issuer_admin", "ISS-002", None),
    ("admin.unregistered", "issuer_admin", None, None),
    ("holder.a", "holder", None, "HLD-2026-0007"),
    ("holder.b", "holder", None, "HLD-2026-0008"),
    ("verifier.a", "verifier", None, None),
    ("verifier.b", "verifier", None, None),
]

# (skill_id, label, aliases). SK-014, SK-021, and SK-033 match the report's API-02 example.
SKILLS = [
    ("SK-011", "Network Security Fundamentals", ["keamanan jaringan", "firewall"]),
    ("SK-014", "OWASP Top 10", ["kerentanan aplikasi web", "web application vulnerabilities"]),
    ("SK-021", "Web Security Testing", ["pengujian keamanan", "penetration testing dasar"]),
    ("SK-033", "Secure Coding", ["pemrograman aman", "validasi input"]),
    ("SK-040", "Python Programming", ["python", "pemrograman python"]),
    ("SK-041", "SQL", ["basis data relasional", "query sql"]),
    ("SK-042", "Data Visualization", ["visualisasi data", "dashboard"]),
    ("SK-043", "Statistics Fundamentals", ["statistika dasar", "analisis statistik"]),
    ("SK-050", "HTML and CSS", ["html", "css", "tata letak web"]),
    ("SK-051", "JavaScript", ["javascript", "pemrograman web front-end"]),
    ("SK-052", "React", ["react", "komponen antarmuka"]),
    ("SK-060", "UI Design", ["desain antarmuka", "user interface design"]),
    ("SK-061", "Usability Testing", ["pengujian kegunaan", "user testing"]),
    ("SK-070", "Project Management", ["manajemen proyek", "perencanaan proyek"]),
    ("SK-071", "Public Speaking", ["berbicara di depan umum", "presentasi"]),
]

# (title, description). Sample position texts for skill matching (API-07, OD-7).
POSITIONS = [
    (
        "Junior Security Analyst",
        "Menganalisis kerentanan aplikasi web, memahami OWASP Top 10, melakukan pengujian keamanan dasar,"
        " dan memantau log dengan SIEM.",
    ),
    (
        "Data Analyst Intern",
        "Mengolah data dengan SQL dan Python, membuat dashboard visualisasi data,"
        " dan menyajikan temuan kepada tim bisnis.",
    ),
    (
        "Frontend Developer Intern",
        "Membangun antarmuka web dengan React dan JavaScript, menulis HTML dan CSS yang rapi,"
        " dan bekerja dengan desainer UI.",
    ),
]


def seed(conn: psycopg.Connection[DictRow]) -> None:
    """Inserts the seed rows. Rows that already exist are left as they are."""
    for issuer_id, name, unit_type, account in ISSUERS:
        conn.execute(
            "INSERT INTO issuers (issuer_id, name, unit_type, chain_account) VALUES (%s, %s, %s, %s)"
            " ON CONFLICT (issuer_id) DO NOTHING",
            (issuer_id, name, unit_type, account),
        )
    for username, role, issuer_id, holder_ref in ACCOUNTS:
        conn.execute(
            "INSERT INTO accounts (username, password_hash, role, issuer_id, holder_ref)"
            " VALUES (%s, %s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (username, ias.hash_password(DEMO_PASSWORD), role, issuer_id, holder_ref),
        )
    for skill_id, label, aliases in SKILLS:
        conn.execute(
            "INSERT INTO skills (skill_id, label, aliases) VALUES (%s, %s, %s) ON CONFLICT (skill_id) DO NOTHING",
            (skill_id, label, aliases),
        )
    conn.commit()


def register_issuers_on_chain(conn: psycopg.Connection[DictRow]) -> None:
    """Registers every database issuer on the registry so both sides hold the same issuers."""
    for row in conn.execute("SELECT issuer_id, chain_account FROM issuers ORDER BY issuer_id"):
        current = rgs.issuer_account(row["issuer_id"])
        if current is None:
            rgs.register_issuer(row["issuer_id"], row["chain_account"])
        elif current.lower() != row["chain_account"].lower():
            raise SystemExit(f"{row['issuer_id']} is bound to {current} on-chain, not {row['chain_account']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="drop all tables first")
    args = parser.parse_args()
    with db.connect() as conn:
        if args.reset:
            db.reset(conn)
        applied = db.migrate(conn)
        seed(conn)
        register_issuers_on_chain(conn)
    print(f"Migrations applied: {applied or 'none'}. Seed loaded; issuers registered on-chain.")


if __name__ == "__main__":
    main()
