# Implements: REQ-R-ABG2-EVENTS
"""
events — EventStream, emit, init_stream, init_snapshot.

Append-only event substrate. The foundational medium.

Rules (ADR-005):
  - emit() is the only write path to events.jsonl
  - event_time is system-assigned — no caller can pass it
  - Corrupted event log lines fail visibly — no silent skipping
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ── EventStream ──────────────────────────────────────────────────────────────

class EventStream:
    """
    Append-only event log. The foundational medium.

    Assets are projections of this stream — never stored objects.
    System assigns event_time at append — no caller can override it.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.workflow_version: str = "unknown"
        self.work_key: Optional[str] = None
        self.run_id: Optional[str] = None

    @classmethod
    def open(cls, workspace: Path) -> "EventStream":
        """Open (or create) the canonical event log for a workspace."""
        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        return cls(events_path)

    def append(self, event_type: str, data: dict) -> dict:
        """
        Write one event. Returns the written record.

        event_time is assigned from the system clock — not from the caller.
        Business times (effective_at, completed_at) live in data.
        """
        record_data = {**data}
        if self.workflow_version != "unknown":
            record_data.setdefault("workflow_version", self.workflow_version)
        if self.work_key is not None:
            record_data.setdefault("work_key", self.work_key)
        if self.run_id is not None:
            record_data.setdefault("run_id", self.run_id)
        record = {
            "event_time": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": record_data,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def all_events(self) -> list[dict]:
        """
        Read all events from the log.

        Fails visibly on corrupted lines — corrupted event logs are not
        silently skipped. Replay integrity depends on every line being valid.
        """
        if not self.path.exists():
            return []

        events: list[dict] = []
        with self.path.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Corrupted event log at {self.path}:{lineno}: {exc}\n"
                        f"  line: {line!r}\n"
                        "Replay is not possible until the corrupted line is repaired."
                    ) from exc
        return events

    def replay(self, asset_type: str, instance_id: str) -> dict:
        """Reconstruct asset state from the event stream. Convenience wrapper."""
        from .projection import project
        return project(self, asset_type, instance_id)


# ── emit — the only write path ───────────────────────────────────────────────

# Module-level stream reference. Set by workspace_bootstrap() or init_stream().
_stream: Optional[EventStream] = None

# Module-level snapshot ID. Set by init_snapshot() at engine startup.
_active_snapshot_id: Optional[str] = None

# Work event types that must carry package_snapshot_id (PackageSnapshot.work_binding).
_WORK_EVENT_TYPES = frozenset({
    "edge_started", "edge_converged", "assessed", "approved", "revoked",
})


def init_stream(stream: EventStream) -> None:
    """Bind the module-level stream. Called by workspace_bootstrap."""
    global _stream
    _stream = stream


def init_snapshot(snapshot_id: str) -> None:
    """Bind the active package snapshot ID. Called at engine startup."""
    global _active_snapshot_id
    _active_snapshot_id = snapshot_id


def emit(event_type: str, data: dict) -> None:
    """
    F_D event logger. The ONLY admissible write to events.jsonl.

    event_time is assigned from the system clock — no caller can pass it.
    F_P constructs content; the F_D engine calls emit(). Never the reverse.

    REQ-F-EVAL-005: assessed{kind: fp} events must carry spec_hash.
    Prime event validation: approved and revoked must carry kind.

    Raises RuntimeError if workspace_bootstrap() has not been called.
    Raises ValueError if a prime event payload fails validation.
    """
    if _stream is None:
        raise RuntimeError(
            "emit() called before workspace_bootstrap(). "
            "Call workspace_bootstrap(path) first to initialise the stream."
        )
    if event_type == "assessed" and data.get("kind") == "fp" and "spec_hash" not in data:
        raise ValueError(
            "assessed{kind: fp} events must include 'spec_hash'. "
            "Use bind.req_hash(package.requirements) to compute it."
        )
    if event_type in ("approved", "revoked") and "kind" not in data:
        raise ValueError(
            f"{event_type} events must include 'kind' field. "
            "Without kind, the event is silently ignored by the projection layer."
        )
    if event_type == "reset":
        scope = data.get("scope")
        if scope not in ("workspace", "work_key", "edge"):
            raise ValueError(
                f"reset events must include 'scope' field with value "
                f"workspace, work_key, or edge — got {scope!r}"
            )
        if scope in ("work_key", "edge") and "work_key" not in data:
            raise ValueError(
                f"reset with scope={scope!r} requires 'work_key' field"
            )
        if scope == "edge" and "edge" not in data:
            raise ValueError(
                "reset with scope='edge' requires 'edge' field"
            )
    # PackageSnapshot carrier enforcement
    if event_type in _WORK_EVENT_TYPES and _active_snapshot_id is not None:
        data.setdefault("package_snapshot_id", _active_snapshot_id)
    _stream.append(event_type, data)
