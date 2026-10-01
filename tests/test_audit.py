import json

import pytest

from omnierp_agent_bridge.audit import ToolPermissionError, invoke_tool
from omnierp_agent_bridge.config import Settings


def settings_for(tmp_path, tools="read_report"):
    return Settings(
        ODOO_URL="http://localhost:8069",
        ODOO_DB="fixture",
        ODOO_USERNAME="reader",
        ODOO_PASSWORD="fixture-only",
        ALLOWED_TOOLS=tools,
        AUDIT_LOG_PATH=str(tmp_path / "audit.jsonl"),
    )


def test_allowed_action_writes_success_audit_row(tmp_path):
    settings = settings_for(tmp_path)
    result = invoke_tool("read_report", settings, lambda: {"count": 1}, arguments={"limit": 10})

    row = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8"))
    assert result == {"count": 1}
    assert row["tool"] == "read_report"
    assert row["outcome"] == "success"
    assert row["arguments"] == {"limit": 10}


def test_write_attempt_is_denied_and_logged(tmp_path):
    settings = settings_for(tmp_path)
    called = False

    def write_operation():
        nonlocal called
        called = True

    with pytest.raises(ToolPermissionError):
        invoke_tool(
            "create_invoice",
            settings,
            write_operation,
            arguments={"invoice_number": "INV/TEST"},
            write=True,
        )

    row = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8"))
    assert not called
    assert row["outcome"] == "denied"
    assert row["reason"] == "write operations are disabled"
