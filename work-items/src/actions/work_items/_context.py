"""
Global context for work item management.

Based on robocorp-workitems (Apache 2.0 License).
"""

import logging
import os
from typing import Iterator, Optional, TYPE_CHECKING

from ._exceptions import EmptyQueue
from ._types import ExceptionType, JSONType, State
from ._workitem import Input, Output

if TYPE_CHECKING:
    from ._adapters._base import BaseAdapter

log = logging.getLogger(__name__)


class WorkItemsContext:
    """
    Context manager for work item input/output operations.

    This class manages the global state for work item processing,
    including the current input queue and adapter.
    """

    def __init__(self, adapter: "BaseAdapter"):
        """
        Initialize the context.

        Args:
            adapter: Storage adapter to use.
        """
        self._adapter = adapter
        self._current_input: Optional[Input] = None

    @property
    def adapter(self) -> "BaseAdapter":
        """The storage adapter."""
        return self._adapter

    @property
    def current_input(self) -> Optional[Input]:
        """The currently reserved input work item."""
        return self._current_input

    def inputs(self) -> Iterator[Input]:
        """
        Iterate over available input work items.

        Yields:
            Input work items.

        Example:
            for item in ctx.inputs():
                # Process item
                item.done()
        """
        while True:
            try:
                item_id = self._adapter.reserve_input()
                input_item = Input(self._adapter, item_id)
                self._current_input = input_item
                yield input_item
            except EmptyQueue:
                break
            finally:
                self._current_input = None

    def get_input(self) -> Input:
        """
        Get the next input work item.

        Returns:
            Input work item.

        Raises:
            EmptyQueue: If no work items are available.
        """
        item_id = self._adapter.reserve_input()
        input_item = Input(self._adapter, item_id)
        self._current_input = input_item
        return input_item

    def create_output(
        self,
        payload: Optional[JSONType] = None,
        files: Optional[dict] = None,
        save: bool = False,
    ) -> Output:
        """
        Create a new output work item.

        Args:
            payload: Initial payload data.
            files: Files to attach as {name: path_or_content}.
            save: Whether to immediately save the output.

        Returns:
            Output work item.

        Raises:
            RuntimeError: If no current input is set.
        """
        if self._current_input is None:
            raise RuntimeError("No current input - cannot create output")

        output = self._current_input.create_output(payload)

        if files:
            for name, value in files.items():
                if isinstance(value, (str, os.PathLike)):
                    output.add_file(path=value, name=name)
                else:
                    output.add_file(content=value, name=name)

        if save:
            output.save()

        return output

    def seed_input(
        self,
        payload: Optional[JSONType] = None,
        files: Optional[dict] = None,
        queue_name: Optional[str] = None,
    ) -> str:
        """
        Seed a new input work item.

        Args:
            payload: Initial payload data.
            files: Files to attach as {name: content}.
            queue_name: Optional queue name override.

        Returns:
            New work item ID.
        """
        files_bytes = None
        if files:
            files_bytes = {}
            for name, value in files.items():
                if isinstance(value, (str, os.PathLike)):
                    from pathlib import Path
                    files_bytes[name] = Path(value).read_bytes()
                else:
                    files_bytes[name] = value

        return self._adapter.seed_input(payload, files_bytes, queue_name)


# Global context instance
_context: Optional[WorkItemsContext] = None


def get_context() -> WorkItemsContext:
    """
    Get the global work items context.

    Returns:
        The global WorkItemsContext instance.

    Raises:
        RuntimeError: If context not initialized.
    """
    global _context
    if _context is None:
        raise RuntimeError(
            "Work items context not initialized. "
            "Call work_items.init() first or set environment variables."
        )
    return _context


def init(adapter: Optional["BaseAdapter"] = None) -> WorkItemsContext:
    """
    Initialize the global work items context.

    If no adapter is provided, one will be created based on
    environment variables.

    Args:
        adapter: Optional storage adapter.

    Returns:
        The initialized context.
    """
    global _context

    if adapter is None:
        adapter = _create_adapter_from_env()

    _context = WorkItemsContext(adapter)
    return _context


def _create_adapter_from_env() -> "BaseAdapter":
    """
    Create an adapter based on environment variables.

    Environment variables:
        RC_WORKITEM_ADAPTER: Adapter class path (default: SQLiteAdapter)
        RC_WORKITEM_DB_PATH: SQLite database path (default: ./workitems.db)
        RC_WORKITEM_QUEUE_NAME: Input queue name (default: default)
        RC_WORKITEM_OUTPUT_QUEUE_NAME: Output queue name (default: {queue}_output)
        RC_WORKITEM_FILES_DIR: Files directory (default: ./work_item_files)

    Returns:
        Configured adapter instance.
    """
    adapter_class = os.environ.get(
        "RC_WORKITEM_ADAPTER",
        "actions.work_items.SQLiteAdapter"
    )

    # Import the adapter class
    if adapter_class == "actions.work_items.SQLiteAdapter":
        from ._adapters._sqlite import SQLiteAdapter
        db_path = os.environ.get("RC_WORKITEM_DB_PATH", "./workitems.db")
        queue_name = os.environ.get("RC_WORKITEM_QUEUE_NAME", "default")
        output_queue_name = os.environ.get(
            "RC_WORKITEM_OUTPUT_QUEUE_NAME",
            f"{queue_name}_output"
        )
        files_dir = os.environ.get("RC_WORKITEM_FILES_DIR", "./work_item_files")

        return SQLiteAdapter(
            db_path=db_path,
            queue_name=queue_name,
            output_queue_name=output_queue_name,
            files_dir=files_dir,
        )
    else:
        # Dynamic import for custom adapters
        import importlib
        module_path, class_name = adapter_class.rsplit(".", 1)
        module = importlib.import_module(module_path)
        adapter_cls = getattr(module, class_name)
        return adapter_cls()


# Convenience functions for common operations

def inputs() -> Iterator[Input]:
    """
    Iterate over input work items.

    This is a convenience function that uses the global context.

    Yields:
        Input work items.
    """
    return get_context().inputs()


def get_input() -> Input:
    """
    Get the next input work item.

    This is a convenience function that uses the global context.

    Returns:
        Input work item.
    """
    return get_context().get_input()


def create_output(
    payload: Optional[JSONType] = None,
    files: Optional[dict] = None,
    save: bool = False,
) -> Output:
    """
    Create an output work item.

    This is a convenience function that uses the global context.

    Args:
        payload: Initial payload data.
        files: Files to attach.
        save: Whether to immediately save.

    Returns:
        Output work item.
    """
    return get_context().create_output(payload, files, save)


def seed_input(
    payload: Optional[JSONType] = None,
    files: Optional[dict] = None,
    queue_name: Optional[str] = None,
) -> str:
    """
    Seed a new input work item.

    This is a convenience function that uses the global context.

    Args:
        payload: Initial payload data.
        files: Files to attach.
        queue_name: Optional queue name override.

    Returns:
        New work item ID.
    """
    return get_context().seed_input(payload, files, queue_name)
