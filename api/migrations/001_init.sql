-- Off-chain schema for ProofSkill (A-03, report Tabel 8.6). All rows are synthetic (A6).
-- On-chain holds only commitment, issuer, status, and time; everything here can be corrected.

CREATE SEQUENCE credential_seq;
CREATE SEQUENCE share_link_seq;
CREATE SEQUENCE verification_seq;
CREATE SEQUENCE matching_seq;

-- Authorized issuers (FR-01). chain_account signs registry transactions for the issuer.
CREATE TABLE issuers (
    issuer_id     text PRIMARY KEY CHECK (issuer_id ~ '^ISS-[0-9]{3}$'),
    name          text NOT NULL,
    unit_type     text NOT NULL,
    chain_account text NOT NULL UNIQUE,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Accounts per role (NFR-01). A holder has one fixed holder_ref (OD-5); an issuer admin
-- belongs to an issuer, or to none (an account that is not a registered issuer, TC-02).
CREATE TABLE accounts (
    username      text PRIMARY KEY,
    password_hash text NOT NULL,
    role          text NOT NULL CHECK (role IN ('platform_admin', 'issuer_admin', 'holder', 'verifier')),
    issuer_id     text REFERENCES issuers,
    holder_ref    text UNIQUE CHECK (holder_ref ~ '^HLD-[0-9]{4}-[0-9]{4}$'),
    CHECK (issuer_id IS NULL OR role = 'issuer_admin'),
    CHECK ((holder_ref IS NOT NULL) = (role = 'holder'))
);

-- Skill catalog (SCS, API-08).
CREATE TABLE skills (
    skill_id text PRIMARY KEY CHECK (skill_id ~ '^SK-[0-9]{3}$'),
    label    text NOT NULL UNIQUE,
    aliases  text[] NOT NULL DEFAULT '{}'
);

-- Credential metadata (FR-03). holder_display_name is off-chain only and is not hashed;
-- nonce and commitment follow the canonical payload of OD-6. No NIK column exists (NFR-02).
CREATE TABLE credentials (
    credential_id       text PRIMARY KEY DEFAULT 'CRD-' || lpad(nextval('credential_seq')::text, 4, '0'),
    issuer_id           text NOT NULL REFERENCES issuers,
    holder_ref          text NOT NULL REFERENCES accounts (holder_ref),
    holder_display_name text NOT NULL,
    program_title       text NOT NULL,
    completed_at        date NOT NULL,
    criteria            text NOT NULL,
    nonce               bytea NOT NULL CHECK (length(nonce) = 32),
    commitment          text NOT NULL,
    tx_hash             text,
    status              text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    issued_at           timestamptz NOT NULL DEFAULT now(),
    revoked_at          timestamptz,
    revocation_reason   text
);

CREATE TABLE credential_skills (
    credential_id text NOT NULL REFERENCES credentials ON DELETE CASCADE,
    skill_id      text NOT NULL REFERENCES skills,
    PRIMARY KEY (credential_id, skill_id)
);

-- Scoped share links (AAS, API-04). Scope is stored server-side so a verifier cannot widen it.
CREATE TABLE share_links (
    link_id       text PRIMARY KEY DEFAULT 'SHL-' || lpad(nextval('share_link_seq')::text, 4, '0'),
    credential_id text NOT NULL REFERENCES credentials,
    share_token   text NOT NULL UNIQUE,
    scope         text[] NOT NULL,
    expires_at    timestamptz NOT NULL,
    revoked_at    timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Verification results (VRS, API-06). Owned by the verifier who ran them (TC-15).
CREATE TABLE verifications (
    verification_id   text PRIMARY KEY DEFAULT 'VER-' || lpad(nextval('verification_seq')::text, 4, '0'),
    link_id           text NOT NULL REFERENCES share_links,
    verifier          text NOT NULL REFERENCES accounts,
    result            text NOT NULL CHECK (result IN ('VALID', 'REVOKED', 'TAMPERED', 'ISSUER_UNAUTHORIZED')),
    integrity         text NOT NULL CHECK (integrity IN ('PASS', 'FAIL')),
    issuer_authorized text NOT NULL CHECK (issuer_authorized IN ('PASS', 'FAIL')),
    status_check      text NOT NULL CHECK (status_check IN ('ACTIVE', 'REVOKED')),
    verified_at       timestamptz NOT NULL DEFAULT now()
);

-- Skill-fit recommendations (AMS, API-07). No total score is stored or returned.
CREATE TABLE matchings (
    matching_id     text PRIMARY KEY DEFAULT 'MAT-' || lpad(nextval('matching_seq')::text, 4, '0'),
    verification_id text NOT NULL REFERENCES verifications,
    position_title  text NOT NULL,
    result          jsonb NOT NULL,
    model_version   text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- Audit trail (FR-10, NFR-07): time, actor role, operation, object, outcome; never payload.
CREATE TABLE audit_events (
    event_id   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    time       timestamptz NOT NULL DEFAULT now(),
    actor_role text NOT NULL,
    operation  text NOT NULL,
    object_id  text,
    outcome    text NOT NULL
);

-- Simulated email outbox for T06 and T27 (OD-3). Nothing is sent.
CREATE TABLE notifications (
    notification_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    holder_ref      text NOT NULL REFERENCES accounts (holder_ref),
    subject         text NOT NULL,
    body            text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);
