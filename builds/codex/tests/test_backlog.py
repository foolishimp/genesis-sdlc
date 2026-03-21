# Validates: REQ-F-BACKLOG-001
# Validates: REQ-F-BACKLOG-002
# Validates: REQ-F-BACKLOG-003
# Validates: REQ-F-BACKLOG-004
"""Tests for the Codex genesis_sdlc backlog module."""

from __future__ import annotations

import pytest

from genesis_sdlc.backlog import BACKLOG_DIR_REL, VALID_STATUSES, _load_item, cmd_list, cmd_promote, cmd_status, load_all


@pytest.fixture()
def workspace(tmp_path):
    backlog_dir = tmp_path / ".ai-workspace" / "backlog"
    backlog_dir.mkdir(parents=True)
    (backlog_dir / "BL-001.yml").write_text(
        "id: BL-001\ntitle: Explore distributed tracing\nstatus: idea\ncreated: 2026-03-16\n",
        encoding="utf-8",
    )
    (backlog_dir / "BL-002.yml").write_text(
        "id: BL-002\ntitle: Add multi-worker consensus\nstatus: ready\ncreated: 2026-03-16\n",
        encoding="utf-8",
    )
    return tmp_path


def test_load_all_returns_items(workspace):
    assert len(load_all(workspace)) == 2


def test_cmd_list_filters_by_status(workspace):
    result = cmd_list(workspace, "ready")
    assert result["total"] == 1
    assert result["items"][0]["id"] == "BL-002"


def test_cmd_status_surfaces_ready_items(workspace):
    result = cmd_status(workspace)
    assert result["attention_required"] is True
    assert result["ready"][0]["id"] == "BL-002"


def test_cmd_promote_updates_item(workspace):
    result = cmd_promote(workspace, "BL-001", "capacity freed up", "REQ-F-TRACE-001")
    assert result["status"] == "promoted"
    data = _load_item(workspace / BACKLOG_DIR_REL / "BL-001.yml")
    assert data["status"] == "promoted"
    assert data["promotion_reason"] == "capacity freed up"
    assert data["promoted_to"] == "REQ-F-TRACE-001"


def test_valid_statuses_constant():
    assert {"idea", "ready", "promoted", "abandoned"}.issubset(set(VALID_STATUSES))
