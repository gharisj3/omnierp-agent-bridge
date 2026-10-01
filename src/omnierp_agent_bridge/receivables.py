"""Read-only overdue customer invoice queries."""

from __future__ import annotations

from datetime import date
from typing import Any

from .odoo_client import OdooClient
from .schemas import OverdueReceivable


class ReceivablesService:
    """Read posted, unpaid customer invoices past their due date."""

    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def get_overdue_receivables(
        self, limit: int = 20, *, today: date | None = None
    ) -> list[OverdueReceivable]:
        today = today or date.today()
        rows = self.client.search_read(
            "account.move",
            [
                ["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["payment_state", "!=", "paid"],
                ["invoice_date_due", "<", today.isoformat()],
            ],
            ["name", "partner_id", "invoice_date_due", "currency_id", "amount_residual"],
            limit=max(1, min(limit, 50)),
            order="invoice_date_due asc",
        )
        return [
            OverdueReceivable(
                invoice_number=str(row["name"]),
                customer=self._relation_name(row.get("partner_id")),
                due_date=row.get("invoice_date_due"),
                currency=self._relation_name(row.get("currency_id")),
                amount_due=row.get("amount_residual") or 0,
            )
            for row in rows
        ]

    @staticmethod
    def _relation_name(value: Any) -> str | None:
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return str(value[1])
        return value if isinstance(value, str) else None
