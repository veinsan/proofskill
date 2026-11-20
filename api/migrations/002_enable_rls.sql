-- B-01: Row Level Security on every table, with no policies. On Supabase this means the public
-- Data API (the anon and authenticated roles) reads and writes nothing; only the API's own
-- connection, which owns the tables, can. Harmless on the local cluster. A later migration that
-- creates a table must enable RLS on it too (tests/test_a03_schema_seed.py checks every table).
DO $$
DECLARE
  t text;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
  END LOOP;
END $$;
