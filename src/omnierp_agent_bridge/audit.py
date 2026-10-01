"""Append-only tool audit records and deterministic permission checks."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any, TypeVar

from .config import Settings

T = TypeVar("T")
_AUDIT_LOCK = Lock()


class ToolPermissionError(PermissionError):
    """Raised when a requested tool is not allowed or attempts a write."""


def append_audit_event(
    path: str | Path,
    *,
    tool: str,
    outcome: str,
    arguments: dict[str, Any],
    reason: str | None = None,
) -> dict[str, Any]:
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "tool": tool,
        "outcome": outcome,
        "arguments": arguments,
    }
    if reason:
        event["reason"] = reason
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_LOCK, audit_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    return event


def invoke_tool(
    tool: str,
    settings: Settings,
    operation: Callable[[], T],
    *,
    arguments: dict[str, Any] | None = None,
    write: bool = False,
) -> T:
    """Enforce the tool allowlist and log every allowed or denied invocation."""
    args = arguments or {}
    if write or tool not in settings.allowed_tools:
        reason = "write operations are disabled" if write else "tool is not in the allowlist"
        append_audit_event(
            settings.audit_log_path,
            tool=tool,
            outcome="denied",
            arguments=args,
            reason=reason,
        )
        raise ToolPermissionError(reason)

    try:
        result = operation()
    except Exception as exc:
        append_audit_event(
            settings.audit_log_path,
            tool=tool,
            outcome="error",
            arguments=args,
            reason=type(exc).__name__,
        )
        raise
    append_audit_event(
        settings.audit_log_path,
        tool=tool,
        outcome="success",
        arguments=args,
    )
    return result
