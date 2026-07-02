from omnierp_agent_bridge.config import Settings


def test_open_po_states_parse_from_csv() -> None:
    settings = Settings(
        ODOO_URL="http://localhost:8069/",
        ODOO_DB="odoo18",
        ODOO_USERNAME="user@example.com",
        ODOO_PASSWORD="secret",
        OPEN_PO_STATES="purchase, to approve , ,done",
    )
    assert settings.odoo_url == "http://localhost:8069"
    assert settings.open_po_states == ("purchase", "to approve", "done")


def test_default_open_po_states_when_blank() -> None:
    settings = Settings(
        ODOO_URL="http://localhost:8069",
        ODOO_DB="odoo18",
        ODOO_USERNAME="user@example.com",
        ODOO_PASSWORD="secret",
        OPEN_PO_STATES="",
    )
    assert settings.open_po_states == ("purchase", "to approve")

