from app.main import app
from services.shared.rbac_matrix import extract_route_role_map, load_service_matrix


def test_simulation_engine_rbac_matrix_is_in_sync():
    assert extract_route_role_map(app) == load_service_matrix("simulation-engine")
