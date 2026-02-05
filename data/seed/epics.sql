INSERT INTO epics (code, name, description, story_count, order_index)
VALUES
  ('EPIC-01', 'Authentication & Access', 'Registration, login, and role-based access', 6, 1),
  ('EPIC-02', 'DPP Creation & Registration', 'Create DPP shells and register them', 8, 2),
  ('EPIC-03', 'Information Access & Retrieval', 'Search, view, and export DPP data', 9, 3),
  ('EPIC-04', 'Data Update & Maintenance', 'Update DPP data and maintain records', 7, 4),
  ('EPIC-05', 'Ownership Transfer', 'Transfer ownership and access', 5, 5),
  ('EPIC-06', 'End-of-Life & Archival', 'End-of-life workflows and archival', 6, 6),
  ('EPIC-07', 'Compliance & Reporting', 'Run compliance checks and reports', 5, 7),
  ('EPIC-08', 'Dashboard & Analytics', 'Dashboards and analytics', 5, 8),
  ('EPIC-09', 'System Integration', 'Integrations and data exchange', 6, 9),
  ('EPIC-10', 'Ethics & Sustainability', 'Sustainability and ethics workflows', 4, 10)
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  story_count = EXCLUDED.story_count,
  order_index = EXCLUDED.order_index;
