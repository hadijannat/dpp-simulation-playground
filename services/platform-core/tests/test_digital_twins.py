"""Tests for the digital-twins API routes on platform-core.

Covers:
- GET /api/v2/core/digital-twins/{dpp_id}  (empty graph fallback)
- GET /api/v2/core/digital-twins/{dpp_id}  (populated graph with nodes/edges)
"""
from __future__ import annotations

from uuid import uuid4

from services.shared.models.digital_twin_snapshot import DigitalTwinSnapshot
from services.shared.models.digital_twin_node import DigitalTwinNode
from services.shared.models.digital_twin_edge import DigitalTwinEdge
from services.shared.models.dpp_instance import DppInstance
from services.shared.models.user import User
from services.shared.models.session import SimulationSession


PREFIX = "/api/v2/core/digital-twins"


def test_get_digital_twin_returns_empty_graph_when_no_data(client):
    """When no snapshot exists for the given dpp_id, the endpoint returns
    an empty graph structure rather than a 404."""
    dpp_id = str(uuid4())
    response = client.get(f"{PREFIX}/{dpp_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["dpp_id"] == dpp_id
    assert body["nodes"] == []
    assert body["edges"] == []
    assert body["timeline"] == []


def test_get_digital_twin_returns_graph_with_nodes_and_edges(client, db_session):
    """When a snapshot with nodes and edges exists, the endpoint returns
    the populated graph structure."""
    # Build prerequisite chain: user -> session -> dpp_instance -> snapshot
    user_id = uuid4()
    db_session.add(User(id=user_id, keycloak_id="dt-test-user", email="dt@test.com"))
    db_session.flush()

    session_id = uuid4()
    db_session.add(SimulationSession(
        id=session_id,
        user_id=user_id,
        active_role="manufacturer",
    ))
    db_session.flush()

    dpp_id = uuid4()
    db_session.add(DppInstance(
        id=dpp_id,
        session_id=session_id,
        aas_identifier="urn:example:battery:001",
        product_name="Battery Pack",
    ))
    db_session.flush()

    snapshot_id = uuid4()
    db_session.add(DigitalTwinSnapshot(
        id=snapshot_id,
        dpp_instance_id=dpp_id,
        label="v1",
    ))
    db_session.flush()

    node_1_id = uuid4()
    node_2_id = uuid4()
    db_session.add_all([
        DigitalTwinNode(
            id=node_1_id,
            snapshot_id=snapshot_id,
            node_key="product-node",
            node_type="product",
            label="Battery Pack",
            payload={"weight": "10kg"},
        ),
        DigitalTwinNode(
            id=node_2_id,
            snapshot_id=snapshot_id,
            node_key="material-node",
            node_type="material",
            label="Lithium",
            payload={},
        ),
    ])
    db_session.flush()

    edge_id = uuid4()
    db_session.add(DigitalTwinEdge(
        id=edge_id,
        snapshot_id=snapshot_id,
        edge_key="contains-edge",
        source_node_key="product-node",
        target_node_key="material-node",
        label="contains",
    ))
    db_session.commit()

    response = client.get(f"{PREFIX}/{dpp_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["dpp_id"] == str(dpp_id)

    assert len(body["nodes"]) == 2
    node_ids = {n["id"] for n in body["nodes"]}
    assert "product-node" in node_ids
    assert "material-node" in node_ids

    product_node = next(n for n in body["nodes"] if n["id"] == "product-node")
    assert product_node["label"] == "Battery Pack"
    assert product_node["type"] == "product"
    assert product_node["payload"] == {"weight": "10kg"}

    assert len(body["edges"]) == 1
    edge = body["edges"][0]
    assert edge["id"] == "contains-edge"
    assert edge["source"] == "product-node"
    assert edge["target"] == "material-node"
    assert edge["label"] == "contains"

    assert body["timeline"] == []
