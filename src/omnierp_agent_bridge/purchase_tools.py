"""Scoped purchase-order query logic."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from .config import Settings
from .odoo_client import OdooClient, OdooClientError
from .schemas import (
    HealthCheckOutput,
    PurchaseOrderDetailInput,
    PurchaseOrderLineRecord,
    PurchaseOrderQueryInput,
    PurchaseOrderRecord,
    PurchaseOrderSummaryOutput,
    VendorRecord,
    VendorSearchInput,
)

PARTNER_FIELDS = ["id", "name", "email", "phone", "company_type", "active"]
PO_FIELDS = [
    "id",
    "name",
    "partner_id",
    "state",
    "date_order",
    "currency_id",
    "amount_untaxed",
    "amount_tax",
    "amount_total",
    "order_line",
]
PO_LINE_FIELDS = [
    "name",
    "product_qty",
    "price_unit",
    "price_subtotal",
    "product_id",
    "product_uom",
]


class PurchaseService:
    """Business logic for vendor and purchase-order reporting."""

    def __init__(self, client: OdooClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    def health_check(self, verify_odoo: bool = True) -> HealthCheckOutput:
        reachable = False
        if verify_odoo:
            try:
                self.client.authenticate()
                reachable = True
            except OdooClientError:
                reachable = False
        return HealthCheckOutput(
            config_loaded=True,
            odoo_reachable=reachable,
            open_po_states=list(self.settings.open_po_states),
            max_result_limit=self.settings.max_result_limit,
        )

    def find_vendor(self, payload: VendorSearchInput) -> list[VendorRecord]:
        limit = min(payload.limit, 20)
        term = self._sanitize_search_term(payload.query)
        rows = self.client.search_read(
            "res.partner",
            [["name", "ilike", term]],
            PARTNER_FIELDS,
            limit=limit,
            order="name asc",
        )
        return [VendorRecord(**row) for row in rows]

    def get_open_purchase_orders(
        self,
        payload: PurchaseOrderQueryInput,
    ) -> list[PurchaseOrderRecord]:
        vendor = self._resolve_vendor(payload.vendor_id, payload.vendor_name)
        limit = min(payload.limit, self.settings.max_result_limit, 50)
        domain = [
            ["partner_id", "=", vendor.id],
            ["state", "in", list(self.settings.open_po_states)],
        ]
        orders = self.client.search_read(
            "purchase.order",
            domain,
            PO_FIELDS,
            limit=limit,
            order="date_order desc",
        )
        return self._build_purchase_orders(orders, include_lines=payload.include_lines)

    def summarize_open_purchase_orders(
        self,
        payload: PurchaseOrderQueryInput,
    ) -> PurchaseOrderSummaryOutput:
        vendor = self._resolve_vendor(payload.vendor_id, payload.vendor_name)
        orders = self.get_open_purchase_orders(payload)
        currency_breakdown: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        total_amount = Decimal("0")
        for order in orders:
            order_total = Decimal(str(order.amount_total or 0))
            total_amount += order_total
            currency_breakdown[order.currency or "UNKNOWN"] += order_total
        return PurchaseOrderSummaryOutput(
            vendor=vendor.name,
            open_po_count=len(orders),
            total_amount=total_amount,
            currency_breakdown=dict(currency_breakdown),
            purchase_orders=orders,
            generated_at=datetime.now(UTC),
        )

    def get_purchase_order_details(self, payload: PurchaseOrderDetailInput) -> PurchaseOrderRecord:
        orders = self.client.search_read(
            "purchase.order",
            [["name", "=", payload.po_name.strip()]],
            PO_FIELDS,
            limit=1,
        )
        if not orders:
            raise OdooClientError("Purchase order not found.")
        return self._build_purchase_orders(orders, include_lines=True)[0]

    def _resolve_vendor(self, vendor_id: int | None, vendor_name: str | None) -> VendorRecord:
        if vendor_id is not None:
            vendors = self.client.read("res.partner", [vendor_id], PARTNER_FIELDS)
        else:
            search_payload = VendorSearchInput(query=vendor_name or "", limit=1)
            vendors = [vendor.model_dump() for vendor in self.find_vendor(search_payload)]
        if not vendors:
            raise OdooClientError("Vendor not found.")
        return VendorRecord(**vendors[0])

    def _build_purchase_orders(
        self,
        rows: list[dict[str, Any]],
        include_lines: bool,
    ) -> list[PurchaseOrderRecord]:
        line_map: dict[int, list[PurchaseOrderLineRecord]] = {}
        if include_lines:
            order_line_ids = [
                line_id for row in rows for line_id in (row.get("order_line", []) or [])
            ]
            if order_line_ids:
                line_rows = self.client.read("purchase.order.line", order_line_ids, PO_LINE_FIELDS)
                line_map = self._index_lines(order_line_ids, line_rows)

        orders: list[PurchaseOrderRecord] = []
        for row in rows:
            vendor_name = self._extract_relation_name(row.get("partner_id"))
            currency = self._extract_relation_name(row.get("currency_id"))
            lines = []
            if include_lines:
                for line_id in row.get("order_line", []) or []:
                    lines.extend(line_map.get(line_id, []))
            orders.append(
                PurchaseOrderRecord(
                    id=row["id"],
                    name=row["name"],
                    vendor=vendor_name,
                    state=row.get("state"),
                    date_order=row.get("date_order"),
                    currency=currency,
                    amount_untaxed=row.get("amount_untaxed"),
                    amount_tax=row.get("amount_tax"),
                    amount_total=row.get("amount_total"),
                    lines=lines,
                )
            )
        return orders

    @staticmethod
    def _index_lines(
        line_ids: list[int],
        line_rows: list[dict[str, Any]],
    ) -> dict[int, list[PurchaseOrderLineRecord]]:
        return {
            line_id: [
                PurchaseOrderLineRecord(
                    product_name=PurchaseService._extract_relation_name(line_row.get("product_id")),
                    description=line_row.get("name"),
                    qty=line_row.get("product_qty"),
                    uom=PurchaseService._extract_relation_name(line_row.get("product_uom")),
                    unit_price=line_row.get("price_unit"),
                    subtotal=line_row.get("price_subtotal"),
                )
            ]
            for line_id, line_row in zip(line_ids, line_rows, strict=False)
        }

    @staticmethod
    def _extract_relation_name(value: Any) -> str | None:
        if isinstance(value, list) and len(value) >= 2:
            return str(value[1])
        if isinstance(value, tuple) and len(value) >= 2:
            return str(value[1])
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _sanitize_search_term(value: str) -> str:
        return " ".join(value.replace("%", " ").replace("_", " ").split())
