INSERT INTO user_points (id, user_id, total_points, level)
SELECT gen_random_uuid(), id, 0, 1 FROM users
ON CONFLICT (user_id) DO NOTHING;
