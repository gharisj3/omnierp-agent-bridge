"""Pydantic schemas for requests and responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HealthCheckOutput(BaseModel):
    config_loaded: bool
    odoo_reachable: bool
    open_po_states: list[str]
    max_result_limit: int


class VendorSearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1)

    @model_validator(mode="after")
    def cap_limit(self) -> Self:
        self.limit = min(self.limit, 20)
        return self


class VendorRecord(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    company_type: str | None = None
    active: bool | None = None


class PurchaseOrderQueryInput(BaseModel):
    vendor_name: str | None = Field(default=None, max_length=100)
    vendor_id: int | None = Field(default=None, ge=1)
    limit: int = Field(default=20, ge=1)
    include_lines: bool = True

    @model_validator(mode="after")
    def validate_vendor_reference(self) -> Self:
        if self.vendor_id is None and not self.vendor_name:
            raise ValueError("Either vendor_id or vendor_name must be provided.")
        self.limit = min(self.limit, 50)
        return self


class PurchaseOrderLineRecord(BaseModel):
    product_name: str | None = None
    description: str | None = None
    qty: Decimal | float | int | None = None
    uom: str | None = None
    unit_price: Decimal | float | int | None = None
    subtotal: Decimal | float | int | None = None


class PurchaseOrderRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    vendor: str | None = None
    state: str | None = None
    date_order: str | None = None
    currency: str | None = None
    amount_untaxed: Decimal | float | int | None = None
    amount_tax: Decimal | float | int | None = None
    amount_total: Decimal | float | int | None = None
    lines: list[PurchaseOrderLineRecord] = Field(default_factory=list)


class PurchaseOrderSummaryOutput(BaseModel):
    vendor: str
    open_po_count: int
    total_amount: Decimal | float | int
    currency_breakdown: dict[str, Decimal | float | int]
    purchase_orders: list[PurchaseOrderRecord]
    generated_at: datetime


class PurchaseOrderDetailInput(BaseModel):
    po_name: str = Field(min_length=1, max_length=64)
