"""FastMCP server entrypoint."""

from __future__ import annotations

from .audit import invoke_tool
from .config import get_settings
from .logging_config import configure_logging
from .odoo_client import OdooClient
from .purchase_tools import PurchaseService
from .receivables import ReceivablesService
from .schemas import PurchaseOrderDetailInput, PurchaseOrderQueryInput, VendorSearchInput

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("The `mcp` package is required to run this server.") from exc


def create_server() -> FastMCP:
    """Create and configure the FastMCP server."""

    settings = get_settings()
    configure_logging(settings.log_level)
    service = PurchaseService(OdooClient(settings), settings)
    receivables = ReceivablesService(OdooClient(settings))
    server = FastMCP(name="OmniERP Agent Bridge")

    @server.tool()
    def health_check() -> dict:
        return invoke_tool(
            "health_check",
            settings,
            lambda: service.health_check().model_dump(mode="json"),
        )

    @server.tool()
    def find_vendor(query: str, limit: int = 10) -> list[dict]:
        arguments = {"query": query, "limit": limit}
        return invoke_tool(
            "find_vendor",
            settings,
            lambda: [
                vendor.model_dump(mode="json")
                for vendor in service.find_vendor(VendorSearchInput(**arguments))
            ],
            arguments=arguments,
        )

    @server.tool()
    def get_open_purchase_orders(
        vendor_name: str | None = None,
        vendor_id: int | None = None,
        limit: int = 20,
        include_lines: bool = True,
    ) -> list[dict]:
        arguments = {
            "vendor_name": vendor_name,
            "vendor_id": vendor_id,
            "limit": limit,
            "include_lines": include_lines,
        }
        return invoke_tool(
            "get_open_purchase_orders",
            settings,
            lambda: [
                order.model_dump(mode="json")
                for order in service.get_open_purchase_orders(PurchaseOrderQueryInput(**arguments))
            ],
            arguments=arguments,
        )

    @server.tool()
    def summarize_open_purchase_orders(vendor_name: str, include_lines: bool = True) -> dict:
        arguments = {"vendor_name": vendor_name, "include_lines": include_lines}
        return invoke_tool(
            "summarize_open_purchase_orders",
            settings,
            lambda: service.summarize_open_purchase_orders(
                PurchaseOrderQueryInput(
                    vendor_name=vendor_name,
                    limit=settings.max_result_limit,
                    include_lines=include_lines,
                )
            ).model_dump(mode="json"),
            arguments=arguments,
        )

    @server.tool()
    def get_purchase_order_details(po_name: str) -> dict:
        arguments = {"po_name": po_name}
        return invoke_tool(
            "get_purchase_order_details",
            settings,
            lambda: service.get_purchase_order_details(
                PurchaseOrderDetailInput(**arguments)
            ).model_dump(mode="json"),
            arguments=arguments,
        )

    @server.tool()
    def get_overdue_receivables(limit: int = 20) -> list[dict]:
        arguments = {"limit": max(1, min(limit, 50))}
        return invoke_tool(
            "get_overdue_receivables",
            settings,
            lambda: [
                receivable.model_dump(mode="json")
                for receivable in receivables.get_overdue_receivables(**arguments)
            ],
            arguments=arguments,
        )

    return server


def main() -> None:
    """Run the FastMCP server."""

    create_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()
