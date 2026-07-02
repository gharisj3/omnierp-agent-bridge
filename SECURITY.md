# Security Policy

## Threat Model

This bridge sits between an LLM-capable MCP client and a live Odoo ERP instance. The main risks are over-broad data access, credential leakage, and accidental mutation of ERP records.

## Controls In This MVP

- Scoped MCP tools only
- No generic `execute_kw` MCP tool
- No arbitrary Odoo model names from the LLM
- No arbitrary domains from the LLM
- Read-only query paths only
- No `create`, `write`, `unlink`, or server actions
- No secret values returned by tools
- Sanitized error messages
- Structured logs without credential values
- Configurable query limits with hard caps

## Safe Usage Guidance

- Use a dedicated read-only Odoo account whenever possible.
- Restrict network access so only the bridge can reach the intended Odoo instance.
- Review model-level Odoo permissions for the read-only user.
- Start with non-production data and validate results before production rollout.
- Log access at the infrastructure level if audit requirements apply.

## Out Of Scope For This MVP

- Row-level access enforcement by business role
- Full audit trails
- Multi-tenant isolation controls
- Per-tool approval workflows
- Secret rotation automation

## Reporting

If you identify a security issue in this repository, avoid posting sensitive details in a public issue. Share a sanitized report through your normal responsible-disclosure channel.

