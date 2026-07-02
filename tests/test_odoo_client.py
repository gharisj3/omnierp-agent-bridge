import xmlrpc.client

import pytest

from omnierp_agent_bridge.config import Settings
from omnierp_agent_bridge.odoo_client import OdooClient, OdooClientError


class FakeCommonProxy:
    def __init__(self) -> None:
        self.calls = 0

    def authenticate(self, db: str, username: str, password: str, context: dict) -> int:
        self.calls += 1
        return 7


class FakeObjectProxy:
    def __init__(self, fail_once: bool = False) -> None:
        self.fail_once = fail_once
        self.calls = 0

    def execute_kw(self, *args, **kwargs):
        self.calls += 1
        if self.fail_once and self.calls == 1:
            raise xmlrpc.client.Fault(100, "Access denied")
        return [{"name": False, "amount_total": 12.5, "nested": [False, {"value": False}]}]


def build_settings() -> Settings:
    return Settings(
        ODOO_URL="http://localhost:8069",
        ODOO_DB="odoo18",
        ODOO_USERNAME="user@example.com",
        ODOO_PASSWORD="secret",
    )


def test_normalize_false_values_to_none() -> None:
    client = OdooClient(build_settings())
    client._common_proxy = FakeCommonProxy()
    client._object_proxy = FakeObjectProxy()

    rows = client.search_read("purchase.order", [["state", "=", "purchase"]], ["name"])

    assert rows == [{"name": None, "amount_total": 12.5, "nested": [None, {"value": None}]}]


def test_retry_once_on_auth_fault() -> None:
    client = OdooClient(build_settings())
    client._common_proxy = FakeCommonProxy()
    client._object_proxy = FakeObjectProxy(fail_once=True)

    rows = client.search_read("purchase.order", [["state", "=", "purchase"]], ["name"])

    assert rows[0]["amount_total"] == 12.5
    assert client._common_proxy.calls == 2


def test_unsupported_method_rejected() -> None:
    client = OdooClient(build_settings())
    with pytest.raises(OdooClientError):
        client._execute_kw("purchase.order", "unlink", [], {})

