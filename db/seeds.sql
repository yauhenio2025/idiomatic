-- Initial channel seeds. Run AFTER schema.sql.
-- Add more rows here and re-run; ON CONFLICT keeps it idempotent.

INSERT INTO channels (youtube_id, lang, name) VALUES
  ('UC5NOEUbkLheQcaaRldYW5GA', 'de', 'tagesschau'),
  ('UCMIgOXM2JEQ2Pv2d0_PVfcg', 'de', 'DW Deutsch'),
  ('UC6bx8B0W0x_5NQFAF3Nbd-A', 'de', 'Süddeutsche Zeitung')
ON CONFLICT (youtube_id) DO NOTHING;
