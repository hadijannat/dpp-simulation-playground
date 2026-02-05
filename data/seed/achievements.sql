INSERT INTO achievements (code, name, description, points, criteria)
VALUES
  ('first-dpp', 'First DPP', 'Create your first DPP shell', 25, '{"event": "aas_created"}'),
  ('compliance-master', 'Compliance Master', 'Pass a compliance check', 30, '{"event": "compliance_check_passed"}'),
  ('negotiation-closer', 'Negotiation Closer', 'Finalize an EDC negotiation', 20, '{"event": "edc_negotiation_completed"}'),
  ('transfer-finisher', 'Transfer Finisher', 'Complete a data transfer', 20, '{"event": "edc_transfer_completed"}'),
  ('story-complete', 'Story Completed', 'Complete a story', 15, '{"event": "story_completed"}'),
  ('gap-finder', 'Gap Finder', 'Report a validated gap', 10, '{"event": "gap_reported"}'),
  ('aasx-uploader', 'AASX Uploader', 'Upload an AASX package', 10, '{"event": "aasx_uploaded"}')
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  points = EXCLUDED.points,
  criteria = EXCLUDED.criteria;
