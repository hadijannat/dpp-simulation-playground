from __future__ import annotations

import textwrap

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
