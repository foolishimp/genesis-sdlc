# Implements: REQ-R-ABG2-CORRECTION
"""
correction — Correction and reset.

find_latest_reset implements ADR-026 scope containment rules.
"""
from __future__ import annotations


def find_latest_reset(
    all_events: list[dict],
    edge: str | None = None,
    work_key: str | None = None,
) -> dict | None:
    """
    Find the latest applicable reset event for a given scope query.

    ADR-026 scope containment rules:
      - Workspace resets (scope="workspace") contain everything
      - Work_key resets (scope="work_key") contain that lineage and descendants
      - Edge+work_key resets (scope="edge") contain that specific slice only

    Returns the most recent matching reset event, or None if no reset applies.
    """
    latest: dict | None = None

    for e in all_events:
        if e.get("event_type") != "reset":
            continue
        edata = e.get("data", {})
        reset_scope = edata.get("scope")

        if reset_scope == "workspace":
            pass

        elif reset_scope == "work_key":
            reset_wk = edata.get("work_key")
            if reset_wk is None:
                continue
            if work_key is None:
                continue
            if not (work_key == reset_wk or work_key.startswith(reset_wk + "/")):
                continue

        elif reset_scope == "edge":
            reset_edge = edata.get("edge")
            reset_wk = edata.get("work_key")
            if reset_edge is not None and reset_edge != edge:
                continue
            if reset_wk is not None:
                if work_key is None:
                    continue
                if not (work_key == reset_wk or work_key.startswith(reset_wk + "/")):
                    continue
        else:
            continue

        if latest is None or e.get("event_time", "") > latest.get("event_time", ""):
            latest = e

    return latest
