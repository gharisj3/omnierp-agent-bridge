# OmniERP Agent Bridge

**Stop clicking through your ERP. Start asking it questions.**

OmniERP Agent Bridge is a portfolio-grade MCP server that lets an LLM ask scoped, read-only questions against live Odoo Community 18 data over XML-RPC.

## Problem

ERP users waste time navigating modules, filters, exports, and Excel just to answer simple business questions.

## Solution

This project exposes a tightly allowlisted set of MCP tools for conversational purchase-order reporting:

- `health_check`
- `find_vendor`
- `get_open_purchase_orders`
- `summarize_open_purchase_orders`
- `get_purchase_order_details`

The bridge does not expose arbitrary Odoo model access, arbitrary domains, write operations, scraping, or a sync database.

## Demo Question

> What are the open POs for Wood Corner?

## Example Response

```json
{
  "vendor": "Wood Corner",
  "open_po_count": 3,
  "total_amount": 15705.73,
  "currency_breakdown": {
    "USD": 15705.73
  },
  "purchase_orders": [
    {
      "name": "PO02451",
      "vendor": "Wood Corner",
      "state": "purchase",
      "date_order": "2026-06-20T09:15:00",
      "currency": "USD",
      "amount_untaxed": 4200.0,
      "amount_tax": 336.0,
      "amount_total": 4536.0
    },
    {
      "name": "PO02468",
      "vendor": "Wood Corner",
      "state": "to approve",
      "date_order": "2026-06-25T14:40:00",
      "currency": "USD",
      "amount_untaxed": 5100.0,
      "amount_tax": 408.0,
      "amount_total": 5508.0
    },
    {
      "name": "PO02472",
      "vendor": "Wood Corner",
      "state": "purchase",
      "date_order": "2026-06-27T11:00:00",
      "currency": "USD",
      "amount_untaxed": 5242.34,
      "amount_tax": 419.39,
      "amount_total": 5661.73
    }
  ],
  "generated_at": "2026-07-02T12:00:00Z"
}
```

## Architecture

`LLM client -> MCP server -> scoped tool -> Odoo XML-RPC -> live ERP data`

See [docs/architecture.md](/E:/AI%20Agents/omnierp-agent-bridge/docs/architecture.md) for the full flow.

## Security Model

- Scoped tools only
- No arbitrary model access
- No arbitrary domain access from the LLM
- No create, write, or unlink operations
- Read-only Odoo user strongly recommended
- No stored data
- No scraping
- No sync database

See [SECURITY.md](/E:/AI%20Agents/omnierp-agent-bridge/SECURITY.md) for the threat model.

## Supported Queries

- Find vendors by name
- List open purchase orders for a vendor
- Summarize open purchase orders into structured totals
- Retrieve purchase order details by PO number

## Project Layout

```text
omnierp-agent-bridge/
  src/omnierp_agent_bridge/
  tests/
  docs/
  examples/
  README.md
  SECURITY.md
  LIMITATIONS.md
  pyproject.toml
  mcp_config.example.json
```

## Setup

```bash
git clone <your-repo-url>
cd omnierp-agent-bridge
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .[dev]
copy .env.example .env
```

Then edit `.env` with your Odoo connection details. Use a read-only Odoo user where possible.

## Run The MCP Server

```bash
python -m omnierp_agent_bridge.server
```

## MCP Client Config Example

Use [mcp_config.example.json](/E:/AI%20Agents/omnierp-agent-bridge/mcp_config.example.json) as a starting point.

## Tests

```bash
pytest
```

All tests use mocked XML-RPC behavior. No real client data or credentials are required.

## Roadmap

- Sales order summary
- Inventory availability
- Customer receivables
- Invoice aging
- Delivery status
- Multi-ERP adapter interface
- Role-based tool scopes
- Audit logs

## Positioning

Built for Odoo Community 18, designed to extend to any ERP with an API.

