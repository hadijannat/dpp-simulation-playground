INSERT INTO annotations (id, user_id, annotation_type, content)
SELECT gen_random_uuid(), id, 'note', 'Sample annotation' FROM users;
