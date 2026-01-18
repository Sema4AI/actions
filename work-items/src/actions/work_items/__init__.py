"""
Actions Work Items - Producer/Consumer workflow support.

This module provides work item management for automation workflows,
enabling producer-consumer patterns where one task creates work items
and another processes them.

Based on robocorp-workitems (Apache 2.0 License), adapted for the
community edition action server with broader applicability beyond
just robots (microservices, ETL pipelines, async job queues, etc.).

Usage (robocorp-compatible API):
    from actions.work_items import inputs, outputs

    # Process work items (singleton pattern)
    for item in inputs:
        data = item.payload
        # Process data...
        outputs.create({"result": "processed"})
        item.done()

Usage (context manager pattern):
    from actions.work_items import inputs

    for item in inputs:
        with item:
            # Process item
            # Automatically done() on success, fail() on exception
            pass

Usage (explicit initialization):
    from actions.work_items import init, inputs, outputs, create_adapter

    # Auto-detect adapter from environment
    adapter = create_adapter()
    init(adapter)

    for item in inputs:
        # Process...
        outputs.create(payload=item.payload)
        item.done()

Environment Variables:
    RC_WORKITEM_ADAPTER: Adapter class (default: auto-detect)

    For SQLiteAdapter:
        RC_WORKITEM_DB_PATH: SQLite database path (default: ./workitems.db)
        RC_WORKITEM_QUEUE_NAME: Input queue name (default: default)
        RC_WORKITEM_OUTPUT_QUEUE_NAME: Output queue name (default: {queue}_output)
        RC_WORKITEM_FILES_DIR: File attachments directory (default: ./work_item_files)

    For FileAdapter:
        RC_WORKITEM_INPUT_PATH: Input directory (default: ./output/work-items-in)
        RC_WORKITEM_OUTPUT_PATH: Output directory (default: ./output/work-items-out)
"""

import logging
import os
from typing import Optional, TYPE_CHECKING

from ._types import State, ExceptionType, JSONType, PathType, Address, Email
from ._exceptions import (
    EmptyQueue,
    WorkItemException,
    BusinessException,
    ApplicationException,
)
from ._workitem import WorkItem, Input, Output
from ._collections import Inputs, Outputs
from ._context import (
    WorkItemsContext,
    init as _init,
    get_context,
    inputs as _inputs_func,
    get_input,
    create_output,
    seed_input,
)
from ._adapters import BaseAdapter, FileAdapter, SQLiteAdapter

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

__version__ = "0.2.0"


# ============================================================================
# Adapter Factory
# ============================================================================

def create_adapter(
    adapter_type: Optional[str] = None,
    **kwargs,
) -> BaseAdapter:
    """
    Create a storage adapter based on environment or explicit type.

    Auto-detection priority:
    1. Explicit adapter_type parameter
    2. RC_WORKITEM_ADAPTER environment variable
    3. If RC_WORKITEM_INPUT_PATH or RC_WORKITEM_OUTPUT_PATH set -> FileAdapter
    4. If RC_WORKITEM_DB_PATH set -> SQLiteAdapter
    5. Default -> SQLiteAdapter

    Args:
        adapter_type: Explicit adapter type ("sqlite", "file", or full class path)
        **kwargs: Additional arguments passed to adapter constructor

    Returns:
        Configured adapter instance.
    """
    # Check explicit type
    if adapter_type is None:
        adapter_type = os.environ.get("RC_WORKITEM_ADAPTER", "").lower()

    # Normalize type names
    adapter_type = adapter_type.lower() if adapter_type else ""

    # Map common names
    if adapter_type in ("file", "fileadapter", "actions.work_items.fileadapter"):
        return FileAdapter(**kwargs)
    elif adapter_type in ("sqlite", "sqliteadapter", "actions.work_items.sqliteadapter"):
        return _create_sqlite_adapter(**kwargs)
    elif adapter_type:
        # Try dynamic import for custom adapters
        try:
            import importlib
            module_path, class_name = adapter_type.rsplit(".", 1)
            module = importlib.import_module(module_path)
            adapter_cls = getattr(module, class_name)
            return adapter_cls(**kwargs)
        except Exception as e:
            log.warning(f"Failed to load custom adapter {adapter_type}: {e}")

    # Auto-detect based on environment variables
    if os.environ.get("RC_WORKITEM_INPUT_PATH") or os.environ.get("RC_WORKITEM_OUTPUT_PATH"):
        log.debug("Auto-detected FileAdapter from environment")
        return FileAdapter(**kwargs)

    # Default to SQLite
    log.debug("Using default SQLiteAdapter")
    return _create_sqlite_adapter(**kwargs)


def _create_sqlite_adapter(**kwargs) -> SQLiteAdapter:
    """Create SQLite adapter with environment defaults."""
    db_path = kwargs.pop("db_path", None) or os.environ.get("RC_WORKITEM_DB_PATH", "./workitems.db")
    queue_name = kwargs.pop("queue_name", None) or os.environ.get("RC_WORKITEM_QUEUE_NAME", "default")
    output_queue_name = kwargs.pop("output_queue_name", None) or os.environ.get(
        "RC_WORKITEM_OUTPUT_QUEUE_NAME", f"{queue_name}_output"
    )
    files_dir = kwargs.pop("files_dir", None) or os.environ.get("RC_WORKITEM_FILES_DIR", "./work_item_files")

    return SQLiteAdapter(
        db_path=db_path,
        queue_name=queue_name,
        output_queue_name=output_queue_name,
        files_dir=files_dir,
        **kwargs,
    )


# ============================================================================
# Singleton Instances (robocorp-workitems compatible)
# ============================================================================

class _InputsSingleton:
    """
    Lazy-initialized Inputs singleton.

    Provides robocorp-compatible `inputs` singleton that auto-initializes
    on first access.
    """

    _instance: Optional[Inputs] = None

    def __iter__(self):
        return iter(self._get_instance())

    def __len__(self):
        return len(self._get_instance())

    def __getitem__(self, index):
        return self._get_instance()[index]

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)

    def _get_instance(self) -> Inputs:
        if self._instance is None:
            _auto_init()
            ctx = get_context()
            self._instance = Inputs(ctx.adapter)
        return self._instance

    def _reset(self):
        """Reset singleton for testing."""
        self._instance = None


class _OutputsSingleton:
    """
    Lazy-initialized Outputs singleton.

    Provides robocorp-compatible `outputs` singleton that auto-initializes
    on first access.
    """

    _instance: Optional[Outputs] = None
    _inputs_singleton: _InputsSingleton

    def __init__(self, inputs_singleton: _InputsSingleton):
        self._inputs_singleton = inputs_singleton

    def __iter__(self):
        return iter(self._get_instance())

    def __len__(self):
        return len(self._get_instance())

    def __getitem__(self, index):
        return self._get_instance()[index]

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)

    def _get_instance(self) -> Outputs:
        if self._instance is None:
            _auto_init()
            ctx = get_context()
            # Ensure inputs singleton is initialized
            inputs_instance = self._inputs_singleton._get_instance()
            self._instance = Outputs(ctx.adapter, inputs_instance)
        return self._instance

    def _reset(self):
        """Reset singleton for testing."""
        self._instance = None


# Create singleton instances
inputs: Inputs = _InputsSingleton()  # type: ignore
outputs: Outputs = _OutputsSingleton(inputs)  # type: ignore


def _auto_init():
    """Auto-initialize context if not already done."""
    try:
        get_context()
    except RuntimeError:
        adapter = create_adapter()
        _init(adapter)


def init(adapter: Optional[BaseAdapter] = None) -> WorkItemsContext:
    """
    Initialize the work items context.

    If no adapter is provided, one will be created using create_adapter().

    Args:
        adapter: Optional storage adapter.

    Returns:
        Initialized context.
    """
    if adapter is None:
        adapter = create_adapter()

    # Reset singletons
    inputs._reset()  # type: ignore
    outputs._reset()  # type: ignore

    return _init(adapter)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Types
    "State",
    "ExceptionType",
    "JSONType",
    "PathType",
    "Address",
    "Email",
    # Exceptions
    "EmptyQueue",
    "WorkItemException",
    "BusinessException",
    "ApplicationException",
    # Work item classes
    "WorkItem",
    "Input",
    "Output",
    # Collection classes
    "Inputs",
    "Outputs",
    # Singletons (robocorp-compatible)
    "inputs",
    "outputs",
    # Context
    "WorkItemsContext",
    "init",
    "get_context",
    # Factory
    "create_adapter",
    # Convenience functions
    "get_input",
    "create_output",
    "seed_input",
    # Adapters
    "BaseAdapter",
    "FileAdapter",
    "SQLiteAdapter",
]
