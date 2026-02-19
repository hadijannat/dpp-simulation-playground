from __future__ import annotations

from pathlib import Path

from app.core import aasx_storage


def test_sanitize_filename_strips_path_segments() -> None:
    name = aasx_storage._sanitize_filename("../../etc/passwd?.aasx")
    assert name == "passwd_.aasx"
    assert "/" not in name
    assert "\\" not in name


def test_store_local_keeps_output_within_storage_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(aasx_storage, "AASX_STORAGE_DIR", str(tmp_path))

    stored = aasx_storage._store_local("../../../../tmp/evil.aasx", b"payload")
    stored_path = Path(stored["path"]).resolve()

    assert stored["storage"] == "local"
    assert stored_path.is_file()
    assert str(stored_path).startswith(str(tmp_path.resolve()) + "/")
    assert ".." not in stored["object_key"]
