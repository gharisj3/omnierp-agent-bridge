# Limitations

This repository is an MVP focused on safe, read-only conversational purchase-order reporting for Odoo Community 18.

## Current Limitations

- Purchase-order use case only
- XML-RPC adapter only
- Assumes Odoo Community 18-compatible models and fields
- No write operations
- No per-user authorization mapping from the LLM client
- No built-in audit log persistence
- No pagination cursor support beyond capped limits
- Vendor resolution by name is best-effort and may require using `vendor_id` for precision

## Production Readiness Notes

- Validate the bridge against your exact Odoo modules and customizations.
- Confirm that purchase-order states match your workflow configuration.
- Use a read-only Odoo user where possible.
- Perform security and permission testing before production use.
- Review whether returned order-line details are appropriate for your data-governance requirements.

