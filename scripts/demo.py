"""Show scoped receivables access and a denied write using synthetic fixture data."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from omnierp_agent_bridge.audit import ToolPermissionError, invoke_tool
from omnierp_agent_bridge.config import Settings
from omnierp_agent_bridge.receivables import ReceivablesService

ROOT = Path(__file__).resolve().parents[1]


class FixtureClient:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def search_read(self, model, domain, fields, limit=None, order=None):
        assert model == "account.move"
        assert any(item[0] == "payment_state" and item[2] == "paid" for item in domain)
        assert "amount_residual" in fields
        return self.rows[:limit]


def main() -> None:
    rows = json.loads(
        (ROOT / "fixtures" / "overdue_receivables.json").read_text(encoding="utf-8-sig")
    )
    with tempfile.TemporaryDirectory(prefix="omnierp-demo-") as folder:
        audit_path = Path(folder) / "audit.jsonl"
        settings = Settings(
            ODOO_URL="http://fixture.invalid",
            ODOO_DB="fixture",
            ODOO_USERNAME="fixture-user",
            ODOO_PASSWORD="fixture-password",
            ALLOWED_TOOLS="get_overdue_receivables",
            AUDIT_LOG_PATH=str(audit_path),
        )
        service = ReceivablesService(FixtureClient(rows))
        result = invoke_tool(
            "get_overdue_receivables",
            settings,
            lambda: [item.model_dump(mode="json") for item in service.get_overdue_receivables()],
            arguments={"limit": 20},
        )
        print("Fixture mode: no Odoo instance or model API is called.")
        print('Agent request: "show overdue receivables"')
        print("Scoped tool: get_overdue_receivables")
        print(json.dumps(result, indent=2))
        try:
            invoke_tool(
                "create_invoice",
                settings,
                lambda: None,
                arguments={"invoice_number": "INV/2026/0060"},
                write=True,
            )
        except ToolPermissionError as exc:
            print(f"Denied write: {exc}")
        print("Audit rows:")
        print(audit_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
