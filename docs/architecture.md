# Architecture

## Flow

1. An MCP-capable LLM client invokes a scoped tool such as `summarize_open_purchase_orders`.
2. The MCP server validates inputs with Pydantic v2 schemas.
3. The purchase service builds a fixed Odoo query against allowlisted models and fields.
4. The Odoo XML-RPC client authenticates and performs read-only `search_read` or `read` calls.
5. Results are normalized, summarized, and returned as structured JSON.

## Design Principles

- Read-only by default
- Small allowlisted tool surface
- No generic model passthrough
- Real-time live ERP queries
- Testable service layer independent from transport
- Sanitized operational errors

## Components

- `config.py`: environment-backed settings
- `logging_config.py`: structured logging setup
- `odoo_client.py`: safe XML-RPC adapter
- `purchase_tools.py`: business logic for vendor and PO queries
- `schemas.py`: request and response models
- `server.py`: FastMCP tool registration

