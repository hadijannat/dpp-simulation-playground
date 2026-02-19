"""Tests for the digital-twins API routes on platform-core.

Covers:
- GET /api/v2/core/digital-twins/{dpp_id}          (empty graph fallback)
- GET /api/v2/core/digital-twins/{dpp_id}          (populated graph with nodes/edges)
- GET /api/v2/core/digital-twins/{dpp_id}/history  (timeline snapshots)
- GET /api/v2/core/digital-twins/{dpp_id}/diff     (snapshot diff)
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
    assert body["snapshot_id"] == str(snapshot_id)
    assert body["snapshot_label"] == "v1"


def test_get_digital_twin_history_returns_empty_when_no_data(client):
    dpp_id = str(uuid4())
    response = client.get(f"{PREFIX}/{dpp_id}/history")
    assert response.status_code == 200
    body = response.json()
    assert body["dpp_id"] == dpp_id
    assert body["items"] == []
    assert body["total"] == 0


def test_get_digital_twin_history_returns_items_with_counts(client, db_session):
    user_id = uuid4()
    db_session.add(User(id=user_id, keycloak_id="dt-history-user", email="dt-history@test.com"))
    db_session.flush()

    session_id = uuid4()
    db_session.add(SimulationSession(id=session_id, user_id=user_id, active_role="manufacturer"))
    db_session.flush()

    dpp_id = uuid4()
    db_session.add(
        DppInstance(
            id=dpp_id,
            session_id=session_id,
            aas_identifier="urn:example:battery:history",
            product_name="Battery History",
        )
    )
    db_session.flush()

    snapshot_1_id = uuid4()
    snapshot_2_id = uuid4()
    db_session.add_all(
        [
            DigitalTwinSnapshot(id=snapshot_1_id, dpp_instance_id=dpp_id, label="v1"),
            DigitalTwinSnapshot(id=snapshot_2_id, dpp_instance_id=dpp_id, label="v2"),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            DigitalTwinNode(
                id=uuid4(),
                snapshot_id=snapshot_1_id,
                node_key="product",
                node_type="product",
                label="Battery",
                payload={},
            ),
            DigitalTwinNode(
                id=uuid4(),
                snapshot_id=snapshot_2_id,
                node_key="product",
                node_type="product",
                label="Battery",
                payload={},
            ),
            DigitalTwinNode(
                id=uuid4(),
                snapshot_id=snapshot_2_id,
                node_key="compliance",
                node_type="status",
                label="Compliance",
                payload={"status": "ok"},
            ),
            DigitalTwinEdge(
                id=uuid4(),
                snapshot_id=snapshot_2_id,
                edge_key="product-compliance",
                source_node_key="product",
                target_node_key="compliance",
                label="validates",
            ),
        ]
    )
    db_session.commit()

    response = client.get(f"{PREFIX}/{dpp_id}/history", params={"limit": 10, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["dpp_id"] == str(dpp_id)
    assert body["total"] == 2
    assert len(body["items"]) == 2

    items_by_label = {item["label"]: item for item in body["items"]}
    assert items_by_label["v1"]["node_count"] == 1
    assert items_by_label["v1"]["edge_count"] == 0
    assert items_by_label["v2"]["node_count"] == 2
    assert items_by_label["v2"]["edge_count"] == 1


def test_get_digital_twin_diff_returns_changes(client, db_session):
    user_id = uuid4()
    db_session.add(User(id=user_id, keycloak_id="dt-diff-user", email="dt-diff@test.com"))
    db_session.flush()

    session_id = uuid4()
    db_session.add(SimulationSession(id=session_id, user_id=user_id, active_role="manufacturer"))
    db_session.flush()

    dpp_id = uuid4()
    db_session.add(
        DppInstance(
            id=dpp_id,
            session_id=session_id,
            aas_identifier="urn:example:battery:diff",
            product_name="Battery Diff",
        )
    )
    db_session.flush()

    snapshot_1_id = uuid4()
    snapshot_2_id = uuid4()
    db_session.add_all(
        [
            DigitalTwinSnapshot(id=snapshot_1_id, dpp_instance_id=dpp_id, label="before"),
            DigitalTwinSnapshot(id=snapshot_2_id, dpp_instance_id=dpp_id, label="after"),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            DigitalTwinNode(
                id=uuid4(),
                snapshot_id=snapshot_1_id,
                node_key="product",
                node_type="product",
                label="Battery",
                payload={"version": 1},
            ),
            DigitalTwinNode(
                id=uuid4(),
                snapshot_id=snapshot_2_id,
                node_key="product",
                node_type="product",
                label="Battery",
                payload={"version": 2},
            ),
            DigitalTwinNode(
                id=uuid4(),
                snapshot_id=snapshot_2_id,
                node_key="transfer",
                node_type="dataspace",
                label="Transfer",
                payload={"status": "completed"},
            ),
            DigitalTwinEdge(
                id=uuid4(),
                snapshot_id=snapshot_2_id,
                edge_key="product-transfer",
                source_node_key="product",
                target_node_key="transfer",
                label="transfers",
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        f"{PREFIX}/{dpp_id}/diff",
        params={"from": str(snapshot_1_id), "to": str(snapshot_2_id)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dpp_id"] == str(dpp_id)
    assert body["from_snapshot"]["snapshot_id"] == str(snapshot_1_id)
    assert body["to_snapshot"]["snapshot_id"] == str(snapshot_2_id)
    assert body["diff"]["summary"]["nodes_added"] == 1
    assert body["diff"]["summary"]["nodes_changed"] == 1
    assert body["diff"]["summary"]["edges_added"] == 1


def test_get_digital_twin_diff_returns_404_for_unknown_snapshot(client):
    dpp_id = str(uuid4())
    response = client.get(
        f"{PREFIX}/{dpp_id}/diff",
        params={"from": str(uuid4()), "to": str(uuid4())},
    )
    assert response.status_code == 404
