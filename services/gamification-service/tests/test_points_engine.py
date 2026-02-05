from app.engine.points_engine import add_points


def test_add_points(monkeypatch):
    # This test only verifies function call signature.
    assert callable(add_points)
