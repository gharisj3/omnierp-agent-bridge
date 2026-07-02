from decimal import Decimal

import pytest

from omnierp_agent_bridge.config import Settings
from omnierp_agent_bridge.odoo_client import OdooClientError
from omnierp_agent_bridge.purchase_tools import PurchaseService
from omnierp_agent_bridge.schemas import (
    PurchaseOrderDetailInput,
    PurchaseOrderQueryInput,
    VendorSearchInput,
)


class FakeClient:
    def authenticate(self) -> int:
        return 4

    def search_read(self, model, domain, fields, limit=None, order=None):
        if model == "res.partner":
            return [
                {
                    "id": 11,
                    "name": "Wood Corner",
                    "email": "buyer@wood.example",
                    "phone": None,
                    "company_type": "company",
                    "active": True,
                }
            ][:limit]
        if model == "purchase.order":
            partner_filter = next((item for item in domain if item[0] == "partner_id"), None)
            state_filter = next((item for item in domain if item[0] == "state"), None)
            name_filter = next((item for item in domain if item[0] == "name"), None)
            if name_filter is not None:
                if name_filter[2] == "PO02472":
                    return [
                        {
                            "id": 101,
                            "name": "PO02472",
                            "partner_id": [11, "Wood Corner"],
                            "state": "purchase",
                            "date_order": "2026-06-27 11:00:00",
                            "currency_id": [1, "USD"],
                            "amount_untaxed": 5242.34,
                            "amount_tax": 419.39,
                            "amount_total": 5661.73,
                            "order_line": [501],
                        }
                    ]
                return []
            assert state_filter[2] == ["purchase", "to approve"]
            if partner_filter and partner_filter[2] == 11:
                return [
                    {
                        "id": 101,
                        "name": "PO02472",
                        "partner_id": [11, "Wood Corner"],
                        "state": "purchase",
                        "date_order": "2026-06-27 11:00:00",
                        "currency_id": [1, "USD"],
                        "amount_untaxed": 5242.34,
                        "amount_tax": 419.39,
                        "amount_total": 5661.73,
                        "order_line": [501],
                    },
                    {
                        "id": 102,
                        "name": "PO02468",
                        "partner_id": [11, "Wood Corner"],
                        "state": "to approve",
                        "date_order": "2026-06-25 14:40:00",
                        "currency_id": [1, "USD"],
                        "amount_untaxed": 5100.0,
                        "amount_tax": 408.0,
                        "amount_total": 5508.0,
                        "order_line": [],
                    },
                ][:limit]
            return []
        raise AssertionError(f"Unexpected model: {model}")

    def read(self, model, ids, fields):
        if model == "res.partner":
            return [
                {
                    "id": 11,
                    "name": "Wood Corner",
                    "email": "buyer@wood.example",
                    "phone": None,
                    "company_type": "company",
                    "active": True,
                }
            ]
        if model == "purchase.order.line":
            return [
                {
                    "name": "Premium oak plank",
                    "product_qty": 40.0,
                    "price_unit": 105.0,
                    "price_subtotal": 4200.0,
                    "product_id": [31, "Oak Plank"],
                    "product_uom": [1, "Units"],
                }
            ]
        raise AssertionError(f"Unexpected model: {model}")


def build_settings() -> Settings:
    return Settings(
        ODOO_URL="http://localhost:8069",
        ODOO_DB="odoo18",
        ODOO_USERNAME="user@example.com",
        ODOO_PASSWORD="secret",
        OPEN_PO_STATES="purchase,to approve",
        MAX_RESULT_LIMIT=50,
    )


def test_vendor_search_returns_scoped_fields() -> None:
    service = PurchaseService(FakeClient(), build_settings())
    vendors = service.find_vendor(VendorSearchInput(query="wood", limit=10))

    assert vendors[0].name == "Wood Corner"
    assert vendors[0].company_type == "company"


def test_limit_is_capped() -> None:
    service = PurchaseService(FakeClient(), build_settings())
    orders = service.get_open_purchase_orders(
        PurchaseOrderQueryInput(vendor_id=11, limit=999, include_lines=False)
    )
    assert len(orders) == 2


def test_summary_calculates_totals() -> None:
    service = PurchaseService(FakeClient(), build_settings())
    summary = service.summarize_open_purchase_orders(
        PurchaseOrderQueryInput(vendor_name="Wood Corner", include_lines=True)
    )

    assert summary.vendor == "Wood Corner"
    assert summary.open_po_count == 2
    assert summary.total_amount == Decimal("11169.73")
    assert summary.currency_breakdown == {"USD": Decimal("11169.73")}
    assert summary.purchase_orders[0].lines[0].product_name == "Oak Plank"


def test_unsupported_states_not_included() -> None:
    service = PurchaseService(FakeClient(), build_settings())
    orders = service.get_open_purchase_orders(
        PurchaseOrderQueryInput(vendor_name="Wood Corner", include_lines=False)
    )
    assert {order.state for order in orders} <= {"purchase", "to approve"}


def test_purchase_order_not_found() -> None:
    service = PurchaseService(FakeClient(), build_settings())
    with pytest.raises(OdooClientError):
        service.get_purchase_order_details(PurchaseOrderDetailInput(po_name="PO404"))
