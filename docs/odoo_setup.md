# Odoo Setup

## Recommended Odoo User

Create a dedicated user for the bridge with the minimum read permissions required for:

- `res.partner`
- `purchase.order`
- `purchase.order.line`
- `res.currency`
- `uom.uom` if needed by your configuration

Use a read-only user where possible.

## Required Configuration

Set the following values in `.env`:

- `ODOO_URL`
- `ODOO_DB`
- `ODOO_USERNAME`
- `ODOO_PASSWORD`
- `OPEN_PO_STATES`
- `ODOO_XMLRPC_TIMEOUT`

## Validation Tips

- Confirm XML-RPC is reachable from the machine running the MCP server.
- Confirm purchase order states match your Odoo workflow.
- Test vendor lookup first before PO summary queries.
- Review whether order-line descriptions contain any data you do not want surfaced to LLM users.

