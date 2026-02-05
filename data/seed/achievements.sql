INSERT INTO achievements (code, name, description, points, criteria)
VALUES ('first-dpp', 'First DPP', 'Create first DPP', 25, '{"type": "event", "name": "aas.created"}')
ON CONFLICT (code) DO NOTHING;
