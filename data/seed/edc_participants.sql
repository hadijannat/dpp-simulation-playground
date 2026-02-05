INSERT INTO edc_participants (id, participant_id, name, metadata)
VALUES
  (gen_random_uuid(), 'BPNL000000000001', 'Demo Consumer', '{"type": "consumer"}'),
  (gen_random_uuid(), 'BPNL000000000002', 'Demo Provider', '{"type": "provider"}')
ON CONFLICT (participant_id) DO NOTHING;

INSERT INTO edc_assets (id, asset_id, name, policy_odrl, data_address)
VALUES
  (gen_random_uuid(), 'asset-001', 'Battery Passport Sample', '{"@type": "odrl:Offer"}', '{"type": "HttpData", "baseUrl": "https://example.com/assets/asset-001"}')
ON CONFLICT (asset_id) DO NOTHING;
