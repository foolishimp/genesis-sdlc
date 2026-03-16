# Validates: REQ-F-BACKLOG-001
# Validates: REQ-F-BACKLOG-002
# Validates: REQ-F-BACKLOG-003
# Validates: REQ-F-BACKLOG-004
"""Tests for genesis_sdlc.backlog — pre-intent holding area."""
import json
from pathlib import Path
import pytest

from genesis_sdlc.backlog import (
    load_all, cmd_list, cmd_status, cmd_promote,
    BACKLOG_DIR_REL, VALID_STATUSES,
)


@pytest.fixture()
def workspace(tmp_path):
    """Minimal workspace with a backlog directory and two BL items."""
    bl_dir = tmp_path / ".ai-workspace" / "backlog"
    bl_dir.mkdir(parents=True)

    (bl_dir / "BL-001.yml").write_text(
        "id: BL-001\ntitle: Explore distributed tracing\nstatus: idea\ncreated: 2026-03-16\n",
        encoding="utf-8",
    )
    (bl_dir / "BL-002.yml").write_text(
        "id: BL-002\ntitle: Add multi-agent consensus\nstatus: ready\ncreated: 2026-03-16\n",
        encoding="utf-8",
    )
    return tmp_path


class TestLoadAll:
    def test_returns_all_items(self, workspace):
        items = load_all(workspace)
        assert len(items) == 2

    def test_empty_when_no_backlog_dir(self, tmp_path):
        assert load_all(tmp_path) == []

    def test_item_has_required_fields(self, workspace):
        items = load_all(workspace)
        for item in items:
            assert "id" in item
            assert "status" in item
            assert "title" in item


class TestCmdList:
    def test_list_all(self, workspace):
        result = cmd_list(workspace, None)
        assert result["total"] == 2
        assert result["filter"] is None

    def test_list_by_status(self, workspace):
        result = cmd_list(workspace, "ready")
        assert result["total"] == 1
        assert result["items"][0]["id"] == "BL-002"

    def test_list_empty_filter(self, workspace):
        result = cmd_list(workspace, "promoted")
        assert result["total"] == 0

    def test_by_status_grouping(self, workspace):
        result = cmd_list(workspace, None)
        assert "idea" in result["by_status"]
        assert "ready" in result["by_status"]


class TestCmdStatus:
    def test_attention_required_when_ready_items(self, workspace):
        result = cmd_status(workspace)
        assert result["attention_required"] is True
        assert len(result["ready"]) == 1
        assert result["ready"][0]["id"] == "BL-002"

    def test_no_attention_when_no_ready_items(self, tmp_path):
        bl_dir = tmp_path / ".ai-workspace" / "backlog"
        bl_dir.mkdir(parents=True)
        (bl_dir / "BL-001.yml").write_text(
            "id: BL-001\ntitle: Something\nstatus: idea\n", encoding="utf-8"
        )
        result = cmd_status(tmp_path)
        assert result["attention_required"] is False
        assert result["ready"] == []

    def test_total_count(self, workspace):
        result = cmd_status(workspace)
        assert result["total"] == 2

    def test_counts_by_status(self, workspace):
        result = cmd_status(workspace)
        assert result["counts"]["idea"] == 1
        assert result["counts"]["ready"] == 1


class TestCmdPromote:
    def test_promote_updates_status(self, workspace):
        result = cmd_promote(workspace, "BL-001", "capacity freed up", None)
        assert "error" not in result
        assert result["status"] == "promoted"

    def test_promote_saves_reason(self, workspace):
        cmd_promote(workspace, "BL-001", "strategic fit", "REQ-F-TRACE-001")
        from genesis_sdlc.backlog import _load_item
        path = workspace / BACKLOG_DIR_REL / "BL-001.yml"
        data = _load_item(path)
        assert data["status"] == "promoted"
        assert data.get("promotion_reason") == "strategic fit"
        assert data.get("promoted_to") == "REQ-F-TRACE-001"

    def test_promote_missing_item_returns_error(self, workspace):
        result = cmd_promote(workspace, "BL-999", None, None)
        assert "error" in result

    def test_promote_already_promoted_returns_error(self, workspace):
        cmd_promote(workspace, "BL-001", None, None)
        result = cmd_promote(workspace, "BL-001", None, None)
        assert "error" in result

    def test_valid_statuses_constant(self):
        assert "idea" in VALID_STATUSES
        assert "ready" in VALID_STATUSES
        assert "promoted" in VALID_STATUSES
        assert "abandoned" in VALID_STATUSES
