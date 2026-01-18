"""
File-based adapter for work items.

Stores work items in JSON files compatible with Robocorp Control Room
format. This adapter is useful for local development and testing.

Based on robocorp-workitems (Apache 2.0 License).
"""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .._exceptions import EmptyQueue
from .._types import ExceptionType, JSONType, State
from ._base import BaseAdapter

log = logging.getLogger(__name__)


class FileAdapter(BaseAdapter):
    """
    File-based work item adapter using JSON files.

    Compatible with Robocorp Control Room work item format:
    - Input items: {input_path}/work-items.json
    - Output items: {output_path}/work-items.json
    - Files stored alongside in numbered directories

    Directory structure:
        work-items-in/
            work-items.json
            1/
                file1.txt
            2/
                file2.pdf
        work-items-out/
            work-items.json
            1/
                output1.csv

    Environment variables:
        RC_WORKITEM_INPUT_PATH: Input directory (default: ./output/work-items-in)
        RC_WORKITEM_OUTPUT_PATH: Output directory (default: ./output/work-items-out)
    """

    def __init__(
        self,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ):
        """
        Initialize file adapter.

        Args:
            input_path: Directory containing input work items.
            output_path: Directory for output work items.
        """
        self._input_path = Path(
            input_path
            or os.environ.get("RC_WORKITEM_INPUT_PATH")
            or os.environ.get("RPA_INPUT_WORKITEM_PATH")
            or "./output/work-items-in"
        )
        self._output_path = Path(
            output_path
            or os.environ.get("RC_WORKITEM_OUTPUT_PATH")
            or os.environ.get("RPA_OUTPUT_WORKITEM_PATH")
            or "./output/work-items-out"
        )

        # Ensure directories exist
        self._input_path.mkdir(parents=True, exist_ok=True)
        self._output_path.mkdir(parents=True, exist_ok=True)

        # Load or initialize work items
        self._input_items = self._load_items(self._input_path)
        self._output_items = self._load_items(self._output_path)

        # Track reservation state
        self._reserved: Dict[str, bool] = {}
        self._current_index = 0

    def _load_items(self, path: Path) -> List[Dict[str, Any]]:
        """Load work items from JSON file."""
        items_file = path / "work-items.json"
        if items_file.exists():
            with open(items_file, "r") as f:
                data = json.load(f)
                return data.get("workItems", data.get("items", []))
        return []

    def _save_items(self, path: Path, items: List[Dict[str, Any]]) -> None:
        """Save work items to JSON file."""
        items_file = path / "work-items.json"
        with open(items_file, "w") as f:
            json.dump({"workItems": items}, f, indent=2, default=str)

    def _get_files_dir(self, path: Path, index: int) -> Path:
        """Get directory for work item files."""
        files_dir = path / str(index + 1)  # 1-indexed directories
        files_dir.mkdir(parents=True, exist_ok=True)
        return files_dir

    def _find_item_index(self, items: List[Dict], item_id: str) -> int:
        """Find item index by ID."""
        for i, item in enumerate(items):
            if item.get("id") == item_id:
                return i
        raise ValueError(f"Work item not found: {item_id}")

    def reserve_input(self) -> str:
        """Reserve next available input work item."""
        while self._current_index < len(self._input_items):
            item = self._input_items[self._current_index]
            item_id = item.get("id", str(self._current_index))

            # Ensure item has ID
            if "id" not in item:
                item["id"] = item_id
                self._save_items(self._input_path, self._input_items)

            if not self._reserved.get(item_id):
                self._reserved[item_id] = True
                self._current_index += 1
                log.debug(f"Reserved input work item: {item_id}")
                return item_id

            self._current_index += 1

        raise EmptyQueue("No more input work items available")

    def release_input(
        self,
        item_id: str,
        state: State,
        exception_type: Optional[ExceptionType] = None,
        code: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Release a reserved input work item."""
        try:
            index = self._find_item_index(self._input_items, item_id)
            item = self._input_items[index]

            item["state"] = state.value
            if exception_type:
                item["exception"] = {
                    "type": exception_type.value,
                    "code": code,
                    "message": message,
                }

            self._save_items(self._input_path, self._input_items)
            log.debug(f"Released input work item {item_id} with state {state.value}")
        except ValueError:
            log.warning(f"Could not find input item to release: {item_id}")

    def create_output(
        self,
        parent_id: str,
        payload: Optional[JSONType] = None,
    ) -> str:
        """Create a new output work item."""
        item_id = str(uuid.uuid4())
        index = len(self._output_items)

        item = {
            "id": item_id,
            "payload": payload or {},
            "files": [],
            "parentId": parent_id,
            "state": State.PENDING.value,
            "createdAt": datetime.utcnow().isoformat(),
        }

        self._output_items.append(item)
        self._save_items(self._output_path, self._output_items)

        log.debug(f"Created output work item: {item_id}")
        return item_id

    def load_payload(self, item_id: str) -> JSONType:
        """Load payload from work item."""
        # Check inputs first
        for item in self._input_items:
            if item.get("id") == item_id:
                return item.get("payload", {})

        # Then check outputs
        for item in self._output_items:
            if item.get("id") == item_id:
                return item.get("payload", {})

        raise ValueError(f"Work item not found: {item_id}")

    def save_payload(self, item_id: str, payload: JSONType) -> None:
        """Save payload to work item."""
        # Check inputs
        for item in self._input_items:
            if item.get("id") == item_id:
                item["payload"] = payload
                self._save_items(self._input_path, self._input_items)
                return

        # Check outputs
        for item in self._output_items:
            if item.get("id") == item_id:
                item["payload"] = payload
                self._save_items(self._output_path, self._output_items)
                return

        raise ValueError(f"Work item not found: {item_id}")

    def list_files(self, item_id: str) -> List[str]:
        """List files attached to work item."""
        # Check inputs
        for i, item in enumerate(self._input_items):
            if item.get("id") == item_id:
                files_dir = self._get_files_dir(self._input_path, i)
                if files_dir.exists():
                    return [f.name for f in files_dir.iterdir() if f.is_file()]
                return item.get("files", [])

        # Check outputs
        for i, item in enumerate(self._output_items):
            if item.get("id") == item_id:
                files_dir = self._get_files_dir(self._output_path, i)
                if files_dir.exists():
                    return [f.name for f in files_dir.iterdir() if f.is_file()]
                return item.get("files", [])

        raise ValueError(f"Work item not found: {item_id}")

    def get_file(self, item_id: str, name: str) -> bytes:
        """Get file content from work item."""
        # Check inputs
        for i, item in enumerate(self._input_items):
            if item.get("id") == item_id:
                file_path = self._get_files_dir(self._input_path, i) / name
                if file_path.exists():
                    return file_path.read_bytes()
                raise ValueError(f"File not found: {name}")

        # Check outputs
        for i, item in enumerate(self._output_items):
            if item.get("id") == item_id:
                file_path = self._get_files_dir(self._output_path, i) / name
                if file_path.exists():
                    return file_path.read_bytes()
                raise ValueError(f"File not found: {name}")

        raise ValueError(f"Work item not found: {item_id}")

    def add_file(
        self,
        item_id: str,
        name: str,
        original_name: str,
        content: bytes,
    ) -> None:
        """Add file to work item."""
        # Check inputs
        for i, item in enumerate(self._input_items):
            if item.get("id") == item_id:
                file_path = self._get_files_dir(self._input_path, i) / name
                file_path.write_bytes(content)
                if "files" not in item:
                    item["files"] = []
                if name not in item["files"]:
                    item["files"].append(name)
                self._save_items(self._input_path, self._input_items)
                return

        # Check outputs
        for i, item in enumerate(self._output_items):
            if item.get("id") == item_id:
                file_path = self._get_files_dir(self._output_path, i) / name
                file_path.write_bytes(content)
                if "files" not in item:
                    item["files"] = []
                if name not in item["files"]:
                    item["files"].append(name)
                self._save_items(self._output_path, self._output_items)
                return

        raise ValueError(f"Work item not found: {item_id}")

    def remove_file(self, item_id: str, name: str) -> None:
        """Remove file from work item."""
        # Check inputs
        for i, item in enumerate(self._input_items):
            if item.get("id") == item_id:
                file_path = self._get_files_dir(self._input_path, i) / name
                if file_path.exists():
                    file_path.unlink()
                if "files" in item and name in item["files"]:
                    item["files"].remove(name)
                self._save_items(self._input_path, self._input_items)
                return

        # Check outputs
        for i, item in enumerate(self._output_items):
            if item.get("id") == item_id:
                file_path = self._get_files_dir(self._output_path, i) / name
                if file_path.exists():
                    file_path.unlink()
                if "files" in item and name in item["files"]:
                    item["files"].remove(name)
                self._save_items(self._output_path, self._output_items)
                return

        raise ValueError(f"Work item not found: {item_id}")

    # Extended methods

    def seed_input(
        self,
        payload: Optional[JSONType] = None,
        files: Optional[Dict[str, bytes]] = None,
        queue_name: Optional[str] = None,
    ) -> str:
        """Seed a new input work item."""
        item_id = str(uuid.uuid4())
        index = len(self._input_items)

        item = {
            "id": item_id,
            "payload": payload or {},
            "files": [],
            "state": State.PENDING.value,
            "createdAt": datetime.utcnow().isoformat(),
        }

        self._input_items.append(item)

        # Add files if provided
        if files:
            files_dir = self._get_files_dir(self._input_path, index)
            for name, content in files.items():
                (files_dir / name).write_bytes(content)
                item["files"].append(name)

        self._save_items(self._input_path, self._input_items)

        log.debug(f"Seeded input work item: {item_id}")
        return item_id

    def list_items(
        self,
        queue_name: Optional[str] = None,
        state: Optional[State] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List work items."""
        items = self._input_items + self._output_items

        if state:
            items = [i for i in items if i.get("state") == state.value]

        return items[:limit]

    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get work item details."""
        for item in self._input_items:
            if item.get("id") == item_id:
                return item

        for item in self._output_items:
            if item.get("id") == item_id:
                return item

        raise ValueError(f"Work item not found: {item_id}")

    def delete_item(self, item_id: str) -> None:
        """Delete a work item."""
        # Check inputs
        for i, item in enumerate(self._input_items):
            if item.get("id") == item_id:
                files_dir = self._get_files_dir(self._input_path, i)
                if files_dir.exists():
                    shutil.rmtree(files_dir)
                self._input_items.pop(i)
                self._save_items(self._input_path, self._input_items)
                return

        # Check outputs
        for i, item in enumerate(self._output_items):
            if item.get("id") == item_id:
                files_dir = self._get_files_dir(self._output_path, i)
                if files_dir.exists():
                    shutil.rmtree(files_dir)
                self._output_items.pop(i)
                self._save_items(self._output_path, self._output_items)
                return

        raise ValueError(f"Work item not found: {item_id}")

    def get_queue_stats(self, queue_name: Optional[str] = None) -> Dict[str, int]:
        """Get queue statistics."""
        all_items = self._input_items + self._output_items

        pending = sum(1 for i in all_items if i.get("state") == State.PENDING.value)
        in_progress = sum(
            1 for i in all_items if i.get("state") == State.IN_PROGRESS.value
        )
        done = sum(1 for i in all_items if i.get("state") == State.DONE.value)
        failed = sum(1 for i in all_items if i.get("state") == State.FAILED.value)

        return {
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "failed": failed,
            "total": len(all_items),
        }
