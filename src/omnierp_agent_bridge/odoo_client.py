"""Safe Odoo XML-RPC client."""

from __future__ import annotations

import logging
import socket
import xmlrpc.client
from collections.abc import Sequence
from typing import Any

from .config import Settings

LOGGER = logging.getLogger(__name__)


class OdooClientError(RuntimeError):
    """Sanitized Odoo client error."""


class OdooClient:
    """Read-only XML-RPC client for Odoo."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._uid: int | None = None
        self._common_proxy = xmlrpc.client.ServerProxy(
            f"{settings.odoo_url}/xmlrpc/2/common",
            allow_none=True,
        )
        self._object_proxy = xmlrpc.client.ServerProxy(
            f"{settings.odoo_url}/xmlrpc/2/object",
            allow_none=True,
        )

    def authenticate(self, force: bool = False) -> int:
        """Authenticate against Odoo and cache the uid."""

        if self._uid is not None and not force:
            return self._uid

        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.settings.odoo_xmlrpc_timeout)
        try:
            uid = self._common_proxy.authenticate(
                self.settings.odoo_db,
                self.settings.odoo_username,
                self.settings.odoo_password,
                {},
            )
        except OSError as exc:
            LOGGER.warning(
                "odoo_auth_network_error",
                extra={"event": "odoo_auth_network_error", "context": {"error": str(exc)}},
            )
            raise OdooClientError("Unable to reach Odoo.") from exc
        finally:
            socket.setdefaulttimeout(previous_timeout)

        if not uid:
            raise OdooClientError("Odoo authentication failed.")

        self._uid = int(uid)
        return self._uid

    def search_read(
        self,
        model: str,
        domain: list[list[Any]],
        fields: Sequence[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a safe `search_read` call."""

        params: dict[str, Any] = {"fields": list(fields)}
        if limit is not None:
            params["limit"] = limit
        if order:
            params["order"] = order
        result = self._execute_kw(model, "search_read", [domain], params)
        return self._normalize_false_values(result)

    def read(self, model: str, ids: Sequence[int], fields: Sequence[str]) -> list[dict[str, Any]]:
        """Execute a safe `read` call."""

        result = self._execute_kw(model, "read", [list(ids)], {"fields": list(fields)})
        return self._normalize_false_values(result)

    def _execute_kw(
        self,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any] | None = None,
        _retried: bool = False,
    ) -> Any:
        if method not in {"search_read", "read"}:
            raise OdooClientError("Unsupported Odoo method.")

        kwargs = kwargs or {}
        uid = self.authenticate()
        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.settings.odoo_xmlrpc_timeout)
        try:
            LOGGER.info(
                "odoo_execute",
                extra={
                    "event": "odoo_execute",
                    "context": {"model": model, "method": method},
                },
            )
            return self._object_proxy.execute_kw(
                self.settings.odoo_db,
                uid,
                self.settings.odoo_password,
                model,
                method,
                args,
                kwargs,
            )
        except xmlrpc.client.Fault as exc:
            if not _retried and self._is_auth_fault(exc):
                self._uid = None
                return self._execute_kw(model, method, args, kwargs, _retried=True)
            LOGGER.warning(
                "odoo_fault",
                extra={
                    "event": "odoo_fault",
                    "context": {"model": model, "method": method, "fault_code": exc.faultCode},
                },
            )
            raise OdooClientError("Odoo request failed.") from exc
        except OSError as exc:
            LOGGER.warning(
                "odoo_network_error",
                extra={"event": "odoo_network_error", "context": {"error": str(exc)}},
            )
            raise OdooClientError("Unable to reach Odoo.") from exc
        finally:
            socket.setdefaulttimeout(previous_timeout)

    @staticmethod
    def _is_auth_fault(exc: xmlrpc.client.Fault) -> bool:
        fault_text = f"{exc.faultCode} {exc.faultString}".lower()
        return "access" in fault_text or "auth" in fault_text or "session" in fault_text

    @classmethod
    def _normalize_false_values(cls, value: Any) -> Any:
        if value is False:
            return None
        if isinstance(value, list):
            return [cls._normalize_false_values(item) for item in value]
        if isinstance(value, tuple):
            return [cls._normalize_false_values(item) for item in value]
        if isinstance(value, dict):
            return {key: cls._normalize_false_values(item) for key, item in value.items()}
        return value

