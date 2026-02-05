INSERT INTO user_stories (epic_id, code, title, acceptance_criteria)
VALUES (1, 'US-01-01', 'Register user', '["User can register"]')
ON CONFLICT (code) DO NOTHING;
