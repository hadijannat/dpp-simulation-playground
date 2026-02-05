INSERT INTO users (id, keycloak_id, email, display_name, organization)
VALUES (gen_random_uuid(), 'kc-demo', 'demo@example.com', 'Demo User', 'Demo Org')
ON CONFLICT (email) DO NOTHING;
