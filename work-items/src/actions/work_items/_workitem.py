"""
Work item classes for producer-consumer workflows.

Based on robocorp-workitems (Apache 2.0 License).
"""

import fnmatch
import glob as glob_module
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, TYPE_CHECKING, Union

from ._exceptions import BusinessException, ApplicationException
from ._types import Email, ExceptionType, JSONType, PathType, State
from ._utils import truncate

if TYPE_CHECKING:
    from ._adapters._base import BaseAdapter

log = logging.getLogger(__name__)


class WorkItem:
    """
    Represents a single work item.

    Work items are the units of work passed between producer and consumer
    tasks. They contain a payload (JSON data) and can have attached files.
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        item_id: str,
        payload: Optional[JSONType] = None,
    ):
        """
        Initialize a work item.

        Args:
            adapter: Storage adapter instance.
            item_id: Unique work item ID.
            payload: Initial payload data.
        """
        self._adapter = adapter
        self._id = item_id
        self._payload: JSONType = payload
        self._payload_modified = False
        self._released = False

    @property
    def id(self) -> str:
        """Work item ID."""
        return self._id

    @property
    def payload(self) -> JSONType:
        """
        Work item payload data.

        Lazy-loads from adapter if not already loaded.
        """
        if self._payload is None:
            self._payload = self._adapter.load_payload(self._id)
        return self._payload

    @payload.setter
    def payload(self, value: JSONType) -> None:
        """Set the payload data."""
        self._payload = value
        self._payload_modified = True

    def save(self) -> None:
        """Save the current payload to storage."""
        if self._payload_modified and self._payload is not None:
            self._adapter.save_payload(self._id, self._payload)
            self._payload_modified = False

    def list_files(self) -> List[str]:
        """
        List files attached to this work item.

        Returns:
            List of file names.
        """
        return self._adapter.list_files(self._id)

    def get_file(self, name: str, path: Optional[Path] = None) -> bytes:
        """
        Get file content from this work item.

        Args:
            name: File name.
            path: Optional path to save file to.

        Returns:
            File content as bytes.
        """
        content = self._adapter.get_file(self._id, name)
        if path:
            path.write_bytes(content)
        return content

    def add_file(
        self,
        path: Optional[Path] = None,
        name: Optional[str] = None,
        content: Optional[bytes] = None,
        original_name: Optional[str] = None,
    ) -> None:
        """
        Add a file to this work item.

        Either path or content must be provided.

        Args:
            path: Path to file to add.
            name: Name for file in work item.
            content: File content as bytes.
            original_name: Original file name.

        Raises:
            ValueError: If neither path nor content is provided.
        """
        if path is not None:
            file_path = Path(path)
            if content is None:
                content = file_path.read_bytes()
            if name is None:
                name = file_path.name
            if original_name is None:
                original_name = file_path.name
        elif content is not None:
            if name is None:
                raise ValueError("name must be provided when using content")
            if original_name is None:
                original_name = name
        else:
            raise ValueError("Either path or content must be provided")

        self._adapter.add_file(self._id, name, original_name, content)

    def remove_file(self, name: str, missing_ok: bool = False) -> None:
        """
        Remove a file from this work item.

        Args:
            name: File name.
            missing_ok: If True, don't raise error if file doesn't exist.
        """
        try:
            self._adapter.remove_file(self._id, name)
        except (ValueError, FileNotFoundError):
            if not missing_ok:
                raise

    def add_files(self, pattern: str) -> List[Path]:
        """
        Add multiple files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "*.pdf", "data/*.csv").

        Returns:
            List of paths that were added.
        """
        added = []
        for path_str in glob_module.glob(pattern, recursive=True):
            path = Path(path_str)
            if path.is_file():
                self.add_file(path=path)
                added.append(path)
        return added

    def remove_files(self, pattern: str, missing_ok: bool = True) -> List[str]:
        """
        Remove files matching a pattern.

        Args:
            pattern: Glob pattern to match against file names.
            missing_ok: If True, don't raise error if no files match.

        Returns:
            List of file names that were removed.
        """
        removed = []
        for name in self.list_files():
            if fnmatch.fnmatch(name, pattern):
                self.remove_file(name, missing_ok=True)
                removed.append(name)
        return removed

    def get_email(self, name: str = "email.eml") -> Email:
        """
        Parse an email attachment from this work item.

        Args:
            name: Name of the email file attachment.

        Returns:
            Parsed Email object.
        """
        content = self.get_file(name)
        return Email.from_bytes(content)


class Input(WorkItem):
    """
    Input work item for consumer tasks.

    Input work items are reserved from the input queue and must be
    released (done or failed) after processing.

    Can be used as a context manager for automatic release:

        with inputs.reserve() as item:
            # Process item
            pass  # Automatically marked as done on successful exit

    Or with exception-based release:

        for item in inputs:
            with item:
                if bad_data:
                    raise BusinessException("Invalid data format")
                # Process...
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        item_id: str,
        payload: Optional[JSONType] = None,
    ):
        super().__init__(adapter, item_id, payload)
        self._state = State.IN_PROGRESS
        self._exception: Optional[Exception] = None

    def __enter__(self) -> "Input":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit context manager with automatic release.

        If an exception occurred:
        - BusinessException -> fail with BUSINESS type
        - ApplicationException -> fail with APPLICATION type
        - Other exceptions -> fail with APPLICATION type

        If no exception and not already released -> done()
        """
        if self._released:
            return False

        if exc_val is not None:
            # Exception occurred
            self._exception = exc_val
            if isinstance(exc_val, BusinessException):
                self.fail(
                    exception_type=ExceptionType.BUSINESS,
                    code=getattr(exc_val, "code", None),
                    message=str(exc_val),
                )
            elif isinstance(exc_val, ApplicationException):
                self.fail(
                    exception_type=ExceptionType.APPLICATION,
                    code=getattr(exc_val, "code", None),
                    message=str(exc_val),
                )
            else:
                self.fail(
                    exception_type=ExceptionType.APPLICATION,
                    code=exc_type.__name__ if exc_type else "ERROR",
                    message=str(exc_val),
                )
            # Don't suppress the exception
            return False
        else:
            # No exception, mark as done
            self.done()
            return False

    @property
    def released(self) -> bool:
        """Whether this input has been released."""
        return self._released

    @property
    def state(self) -> State:
        """Current state of this input."""
        return self._state

    @property
    def exception(self) -> Optional[Exception]:
        """Exception that caused this input to fail, if any."""
        return self._exception

    def done(self) -> None:
        """
        Mark this input as successfully processed.

        After calling done(), the input is released and cannot be used.
        """
        if self._released:
            log.warning(f"Input {self._id} already released")
            return

        self.save()
        self._adapter.release_input(self._id, State.DONE)
        self._released = True
        self._state = State.DONE
        log.info(f"Input {self._id} marked as DONE")

    def fail(
        self,
        exception_type: ExceptionType = ExceptionType.APPLICATION,
        code: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Mark this input as failed.

        Args:
            exception_type: Type of failure (BUSINESS or APPLICATION).
            code: Error code.
            message: Error message.
        """
        if self._released:
            log.warning(f"Input {self._id} already released")
            return

        self.save()
        self._adapter.release_input(
            self._id,
            State.FAILED,
            exception_type=exception_type,
            code=code,
            message=truncate(message or "", 1000),
        )
        self._released = True
        self._state = State.FAILED
        log.info(f"Input {self._id} marked as FAILED: {message}")

    def create_output(self, payload: Optional[JSONType] = None) -> "Output":
        """
        Create an output work item from this input.

        Args:
            payload: Initial payload for output.

        Returns:
            New Output work item.
        """
        output_id = self._adapter.create_output(self._id, payload)
        return Output(self._adapter, output_id, payload)


class Output(WorkItem):
    """
    Output work item created by consumer tasks.

    Output work items are created from input work items and placed
    in the output queue for downstream processing.
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        item_id: str,
        payload: Optional[JSONType] = None,
    ):
        super().__init__(adapter, item_id, payload)
        # Mark as modified so initial payload gets saved
        if payload is not None:
            self._payload_modified = True

    def save(self) -> None:
        """Save the output work item."""
        super().save()
        log.debug(f"Output {self._id} saved")
