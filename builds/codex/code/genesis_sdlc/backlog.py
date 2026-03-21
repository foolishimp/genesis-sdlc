# Implements: REQ-F-BACKLOG-001
# Implements: REQ-F-BACKLOG-002
# Implements: REQ-F-BACKLOG-003
# Implements: REQ-F-BACKLOG-004
"""
genesis_sdlc backlog — pre-intent holding area for ideas in gestation.

BL-*.yml schema (.ai-workspace/backlog/):
    id:               BL-xxx
    title:            short description
    status:           idea | incubating | ready | promoted | abandoned
    created:          ISO date
    updated:          ISO date
    notes:            free-form prose (optional)
    promoted_to:      REQ-F-* (set on promotion)
    promotion_reason: free-form (set on promotion)

Usage:
    python -m genesis_sdlc.backlog list [--status STATUS] [--workspace DIR]
    python -m genesis_sdlc.backlog promote BL-xxx [--workspace DIR]
    python -m genesis_sdlc.backlog status [--workspace DIR]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


VALID_STATUSES = ("idea", "incubating", "ready", "promoted", "abandoned")
BACKLOG_DIR_REL = ".ai-workspace/backlog"


def _load_item(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if _HAS_YAML:
        data = yaml.safe_load(text) or {}
    else:
        data = {}
        for line in text.splitlines():
            if ":" in line and not line.startswith(" "):
                key, _, value = line.partition(":")
                data[key.strip()] = value.strip()
    data.setdefault("id", path.stem)
    data.setdefault("status", "idea")
    data.setdefault("title", "")
    return data


def _save_item(path: Path, data: dict) -> None:
    data["updated"] = datetime.now(timezone.utc).date().isoformat()
    if _HAS_YAML:
        import yaml as _yaml

        path.write_text(
            _yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return

    lines = []
    for key, value in data.items():
        if "\n" in str(value):
            lines.append(f"{key}: |")
            for sub in str(value).splitlines():
                lines.append(f"  {sub}")
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_all(workspace: Path) -> list[dict]:
    backlog_dir = workspace / BACKLOG_DIR_REL
    if not backlog_dir.exists():
        return []
    items = []
    for path in sorted(backlog_dir.glob("BL-*.yml")):
        try:
            items.append(_load_item(path))
        except Exception:
            pass
    return items


def cmd_list(workspace: Path, status_filter: str | None) -> dict:
    items = load_all(workspace)
    if status_filter:
        items = [item for item in items if item.get("status") == status_filter]
    by_status: dict[str, list] = {}
    for item in items:
        status = item.get("status", "idea")
        by_status.setdefault(status, []).append(item)
    return {
        "total": len(items),
        "filter": status_filter,
        "by_status": by_status,
        "items": items,
    }


def cmd_status(workspace: Path) -> dict:
    items = load_all(workspace)
    counts: dict[str, int] = {}
    for item in items:
        status = item.get("status", "idea")
        counts[status] = counts.get(status, 0) + 1
    ready = [item for item in items if item.get("status") == "ready"]
    return {
        "total": len(items),
        "counts": counts,
        "ready": ready,
        "attention_required": bool(ready),
    }


def cmd_promote(
    workspace: Path,
    bl_id: str,
    reason: str | None,
    feature: str | None,
) -> dict:
    backlog_dir = workspace / BACKLOG_DIR_REL
    candidates = list(backlog_dir.glob(f"{bl_id}.yml")) if backlog_dir.exists() else []
    if not candidates:
        return {"error": f"Item not found: {bl_id}", "id": bl_id}

    path = candidates[0]
    data = _load_item(path)
    if data.get("status") in {"promoted", "abandoned"}:
        return {"error": f"Cannot promote item with status={data['status']}", "id": bl_id}

    data["status"] = "promoted"
    if feature:
        data["promoted_to"] = feature
    if reason:
        data["promotion_reason"] = reason
    _save_item(path, data)

    event_data = {
        "signal_source": "backlog_promotion",
        "backlog_id": bl_id,
        "title": data.get("title", ""),
    }
    if feature:
        event_data["feature"] = feature
    if reason:
        event_data["reason"] = reason

    emit_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "genesis",
            "emit-event",
            "--type",
            "intent_raised",
            "--data",
            json.dumps(event_data),
        ],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        env=_genesis_env(workspace),
    )

    return {
        "id": bl_id,
        "title": data.get("title", ""),
        "status": "promoted",
        "promoted_to": feature,
        "promotion_reason": reason,
        "event_emitted": emit_result.returncode == 0,
        "emit_output": (
            emit_result.stdout.strip()
            if emit_result.returncode == 0
            else emit_result.stderr.strip()
        ),
    }


def _genesis_env(workspace: Path) -> dict:
    import os

    env = os.environ.copy()
    genesis_path = workspace / ".genesis"
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(genesis_path) + (":" + existing if existing else "")
    return env


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="genesis_sdlc.backlog",
        description="Backlog — pre-intent holding area for ideas in gestation",
    )
    parser.add_argument(
        "--workspace",
        metavar="DIR",
        default=".",
        help="Project workspace root (default: cwd)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List backlog items")
    p_list.add_argument(
        "--status",
        metavar="STATUS",
        default=None,
        choices=VALID_STATUSES,
        help="Filter by status",
    )

    sub.add_parser("status", help="Summarise the backlog")

    p_promote = sub.add_parser("promote", help="Promote item to intent layer")
    p_promote.add_argument("id", metavar="BL-xxx", help="Backlog item ID")
    p_promote.add_argument("--reason", metavar="TEXT", default=None)
    p_promote.add_argument("--feature", metavar="REQ-F-*", default=None)

    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()

    if args.cmd == "list":
        result = cmd_list(workspace, args.status)
    elif args.cmd == "status":
        result = cmd_status(workspace)
    else:
        result = cmd_promote(workspace, args.id, args.reason, args.feature)

    print(json.dumps(result, indent=2))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
