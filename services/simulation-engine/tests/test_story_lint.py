from __future__ import annotations

import textwrap
import time

import yaml

from app.core.story_loader import lint_stories, list_stories


def test_list_stories_includes_story_version_and_metadata(tmp_path):
    story_file = tmp_path / "stories.yaml"
    story_file.write_text(
        textwrap.dedent(
            """
            - code: US-11-01
              title: "Valid story"
              steps:
                - action: user.input
                  params:
                    prompt: "hello"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    items = list_stories(data_dir=str(tmp_path))
    assert len(items) == 1
    assert items[0]["code"] == "US-11-01"
    assert items[0]["story_version"] == 1
    assert items[0]["epic_code"] == "EPIC-11"
    assert items[0]["order_index"] == 1


def test_story_lint_reports_invalid_story_shape(tmp_path):
    story_file = tmp_path / "broken.yaml"
    story_file.write_text(
        textwrap.dedent(
            """
            - code: ""
              title: "Broken story"
              steps:
                - params:
                    prompt: "missing action"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    errors = lint_stories(data_dir=str(tmp_path))
    assert errors


def test_story_loader_cache_uses_file_signature_and_invalidates(tmp_path, monkeypatch):
    story_file = tmp_path / "stories.yaml"
    story_file.write_text(
        textwrap.dedent(
            """
            - code: US-22-01
              title: "Cached story"
              steps:
                - action: user.input
                  params:
                    prompt: "first"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    call_count = 0
    original_safe_load = yaml.safe_load

    def _counting_safe_load(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_safe_load(*args, **kwargs)

    monkeypatch.setattr("app.core.story_loader.yaml.safe_load", _counting_safe_load)

    first = list_stories(data_dir=str(tmp_path))
    second = list_stories(data_dir=str(tmp_path))
    assert first == second
    assert call_count == 1

    time.sleep(0.001)
    story_file.write_text(
        textwrap.dedent(
            """
            - code: US-22-01
              title: "Cached story (updated)"
              steps:
                - action: user.input
                  params:
                    prompt: "second"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    list_stories(data_dir=str(tmp_path))
    assert call_count == 2
