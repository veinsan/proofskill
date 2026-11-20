-- B-02: passwords live in Supabase Auth now. The accounts table stays as the directory of roles,
-- issuers, and holder references that API-02 checks a holderRef against.
ALTER TABLE accounts DROP COLUMN password_hash;
