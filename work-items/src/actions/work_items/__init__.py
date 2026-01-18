"""
Actions Work Items - Producer/Consumer workflow support.

This module provides work item management for automation workflows,
enabling producer-consumer patterns where one task creates work items
and another processes them.

Based on robocorp-workitems (Apache 2.0 License), adapted for the
community edition action server.

Usage:
    from actions.work_items import inputs, create_output, init

    # Initialize with SQLite adapter
    init()

    # Process work items
    for item in inputs():
        data = item.payload
        # Process data...
        output = item.create_output({"result": "processed"})
        output.save()
        item.done()

Environment Variables:
    RC_WORKITEM_ADAPTER: Adapter class (default: actions.work_items.SQLiteAdapter)
    RC_WORKITEM_DB_PATH: SQLite database path (default: ./workitems.db)
    RC_WORKITEM_QUEUE_NAME: Input queue name (default: default)
    RC_WORKITEM_OUTPUT_QUEUE_NAME: Output queue name (default: {queue}_output)
    RC_WORKITEM_FILES_DIR: File attachments directory (default: ./work_item_files)
"""

from ._types import State, ExceptionType, JSONType
from ._exceptions import (
    EmptyQueue,
    WorkItemException,
    BusinessException,
    ApplicationException,
)
from ._workitem import WorkItem, Input, Output
from ._context import (
    WorkItemsContext,
    init,
    get_context,
    inputs,
    get_input,
    create_output,
    seed_input,
)
from ._adapters import BaseAdapter, SQLiteAdapter

__all__ = [
    # Types
    "State",
    "ExceptionType",
    "JSONType",
    # Exceptions
    "EmptyQueue",
    "WorkItemException",
    "BusinessException",
    "ApplicationException",
    # Work item classes
    "WorkItem",
    "Input",
    "Output",
    # Context
    "WorkItemsContext",
    "init",
    "get_context",
    # Convenience functions
    "inputs",
    "get_input",
    "create_output",
    "seed_input",
    # Adapters
    "BaseAdapter",
    "SQLiteAdapter",
]

__version__ = "0.1.0"
