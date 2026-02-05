INSERT INTO epics (code, name, description, story_count)
VALUES ('EPIC-01', 'Authentication', 'Auth and access', 6)
ON CONFLICT (code) DO NOTHING;
