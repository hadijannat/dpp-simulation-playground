INSERT INTO user_points (user_id, total_points, level)
SELECT id, 0, 1 FROM users;
