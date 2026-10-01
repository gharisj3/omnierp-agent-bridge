from datetime import date

from omnierp_agent_bridge.receivables import ReceivablesService


class FakeReceivablesClient:
    def __init__(self):
        self.call = None

    def search_read(self, model, domain, fields, limit=None, order=None):
        self.call = (model, domain, fields, limit, order)
        return [
            {
                "name": "INV/2026/0042",
                "partner_id": [41, "Cedar & Finch Market"],
                "invoice_date_due": "2026-08-15",
                "currency_id": [1, "USD"],
                "amount_residual": 1250.0,
            }
        ]


def test_overdue_receivables_uses_fixed_read_only_query():
    client = FakeReceivablesClient()
    service = ReceivablesService(client)

    rows = service.get_overdue_receivables(limit=1000, today=date(2026, 10, 1))

    model, domain, fields, limit, order = client.call
    assert model == "account.move"
    assert ["state", "=", "posted"] in domain
    assert ["payment_state", "!=", "paid"] in domain
    assert ["invoice_date_due", "<", "2026-10-01"] in domain
    assert "amount_residual" in fields
    assert limit == 50
    assert order == "invoice_date_due asc"
    assert rows[0].customer == "Cedar & Finch Market"
    assert rows[0].amount_due == 1250.0
