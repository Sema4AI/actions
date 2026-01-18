"""Configuration helpers for this repository.

This module exposes only the adapter configuration helpers used by the
robot tasks. Project-specific parameter loading was removed to keep the
module focused and portable.
"""
from __future__ import annotations

import os
import logging
from typing import Dict

LOGGER = logging.getLogger(__name__)


# T012: Adapter configuration loading
def get_adapter_config() -> Dict[str, object]:
    """Load adapter configuration from environment variables.

    Returns a dictionary with adapter selection and connection settings. The
    function intentionally reads from environment variables (not files) so
    Robocorp tasks can configure adapters via the environment.
    """
    config: Dict[str, object] = {
        # Adapter selection (required)
        "adapter_class": os.getenv("RC_WORKITEM_ADAPTER", ""),

        # Common configuration
        "queue_name": os.getenv("RC_WORKITEM_QUEUE_NAME", "default"),
        "files_dir": os.getenv("RC_WORKITEM_FILES_DIR", "devdata/work_item_files"),
        "orphan_timeout_minutes": int(os.getenv("RC_WORKITEM_ORPHAN_TIMEOUT_MINUTES", "30")),

        # SQLite configuration
        "db_path": os.getenv("RC_WORKITEM_DB_PATH", ""),

        # Redis configuration
        "redis_host": os.getenv("REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("REDIS_PORT", "6379")),
        "redis_db": int(os.getenv("REDIS_DB", "0")),
        "redis_password": os.getenv("REDIS_PASSWORD"),
        "redis_max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),

        # PostgreSQL configuration
        "postgres_connection_string": os.getenv("POSTGRES_CONNECTION_STRING", ""),
        "postgres_pool_size": int(os.getenv("POSTGRES_POOL_SIZE", "10")),
        "postgres_max_overflow": int(os.getenv("POSTGRES_MAX_OVERFLOW", "20")),
    }

    # Validate required configuration early for clarity
    if not config["adapter_class"]:
        raise ValueError(
            "RC_WORKITEM_ADAPTER environment variable is required. "
            "Example: custom_adapters.sqlite_adapter.SQLiteAdapter"
        )

    return config


def validate_adapter_config(adapter_class: str, config: Dict[str, object]) -> None:
    """Validate adapter configuration for specific adapter type.

    Raises ValueError when required settings for the selected adapter type are
    missing. Keeps checks minimal and focused on what runtime needs.
    """
    acl = adapter_class.lower()

    if "sqlite" in acl:
        if not config.get("db_path"):
            raise ValueError(
                "RC_WORKITEM_DB_PATH environment variable required for SQLite adapter. "
                "Example: devdata/work_items.db"
            )

    elif "redis" in acl:
        if not config.get("redis_host"):
            raise ValueError(
                "REDIS_HOST environment variable required for Redis adapter. "
                "Example: localhost"
            )

    elif "postgres" in acl or "postgresql" in acl:
        if not config.get("postgres_connection_string"):
            raise ValueError(
                "POSTGRES_CONNECTION_STRING environment variable required for PostgreSQL adapter. "
                "Example: postgresql://user:password@localhost:5432/workitems"
            )


if __name__ == "__main__":
    # Example usage for local debugging: only exercise adapter helpers
    try:
        adapter_config = get_adapter_config()
        print(f"Adapter configuration: {adapter_config}")
    except Exception as e:
        print(f"Adapter configuration error: {e}")
