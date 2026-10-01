"""Application configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    odoo_url: str = Field(alias="ODOO_URL")
    odoo_db: str = Field(alias="ODOO_DB")
    odoo_username: str = Field(alias="ODOO_USERNAME")
    odoo_password: str = Field(alias="ODOO_PASSWORD")
    open_po_states: Annotated[tuple[str, ...], NoDecode] = Field(
        default=("purchase", "to approve"),
        alias="OPEN_PO_STATES",
    )
    max_result_limit: int = Field(default=50, alias="MAX_RESULT_LIMIT", ge=1, le=200)
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    odoo_xmlrpc_timeout: int = Field(default=15, alias="ODOO_XMLRPC_TIMEOUT", ge=1, le=120)
    allowed_tools: Annotated[tuple[str, ...], NoDecode] = Field(
        default=(
            "health_check",
            "find_vendor",
            "get_open_purchase_orders",
            "summarize_open_purchase_orders",
            "get_purchase_order_details",
            "get_overdue_receivables",
        ),
        alias="ALLOWED_TOOLS",
    )
    audit_log_path: str = Field(default="logs/agent-audit.jsonl", alias="AUDIT_LOG_PATH")

    @field_validator("odoo_url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("open_po_states", mode="before")
    @classmethod
    def parse_open_po_states(cls, value: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
        if isinstance(value, tuple):
            return tuple(item.strip() for item in value if item and item.strip())
        if isinstance(value, list):
            return tuple(item.strip() for item in value if item and item.strip())
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",")]
            cleaned = tuple(item for item in items if item)
            if cleaned:
                return cleaned
        return ("purchase", "to approve")

    @field_validator("allowed_tools", mode="before")
    @classmethod
    def parse_allowed_tools(cls, value: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
        if isinstance(value, (tuple, list)):
            return tuple(item.strip() for item in value if item and item.strip())
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return ()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
