"""
SQLite adapter for work item storage.

This provides a file-based, cross-platform storage backend for work items
using SQLite. It supports multiple queues, file attachments, and full
work item lifecycle management.
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .._exceptions import EmptyQueue
from .._types import ExceptionType, JSONType, State
from ._base import BaseAdapter

log = logging.getLogger(__name__)


class SQLiteAdapter(BaseAdapter):
    """
    SQLite-based storage adapter for work items.

    This adapter stores work items in a SQLite database with file
    attachments stored on the filesystem. It supports:
    - Multiple queues
    - FIFO ordering
    - File attachments
    - Full lifecycle tracking
    """

    def __init__(
        self,
        db_path: str = "./workitems.db",
        queue_name: str = "default",
        output_queue_name: Optional[str] = None,
        files_dir: str = "./work_item_files",
    ):
        """
        Initialize the SQLite adapter.

        Args:
            db_path: Path to SQLite database file.
            queue_name: Name of the input queue.
            output_queue_name: Name of the output queue (default: {queue_name}_output).
            files_dir: Directory for file attachments.
        """
        self._db_path = Path(db_path)
        self._queue_name = queue_name
        self._output_queue_name = output_queue_name or f"{queue_name}_output"
        self._files_dir = Path(files_dir)

        # Ensure directories exist
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._files_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self._db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS work_items (
                    id TEXT PRIMARY KEY,
                    queue_name TEXT NOT NULL,
                    parent_id TEXT,
                    state TEXT NOT NULL DEFAULT 'PENDING',
                    payload TEXT,
                    exception_type TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    reserved_at TEXT,
                    completed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_work_items_queue_state
                ON work_items(queue_name, state);

                CREATE INDEX IF NOT EXISTS idx_work_items_parent
                ON work_items(parent_id);

                CREATE TABLE IF NOT EXISTS work_item_files (
                    id TEXT PRIMARY KEY,
                    work_item_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (work_item_id) REFERENCES work_items(id)
                );

                CREATE INDEX IF NOT EXISTS idx_work_item_files_item
                ON work_item_files(work_item_id);

                CREATE UNIQUE INDEX IF NOT EXISTS idx_work_item_files_name
                ON work_item_files(work_item_id, name);
            """)
            conn.commit()

    def _now(self) -> str:
        """Get current timestamp as ISO string."""
        return datetime.now(timezone.utc).isoformat()

    def reserve_input(self) -> str:
        """Reserve the next available input work item."""
        with self._get_conn() as conn:
            # Get next pending item (FIFO order)
            cursor = conn.execute(
                """
                SELECT id FROM work_items
                WHERE queue_name = ? AND state = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (self._queue_name, State.PENDING.value),
            )
            row = cursor.fetchone()

            if row is None:
                raise EmptyQueue(f"No work items available in queue: {self._queue_name}")

            item_id = row["id"]
            now = self._now()

            # Mark as in progress
            conn.execute(
                """
                UPDATE work_items
                SET state = ?, reserved_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (State.IN_PROGRESS.value, now, now, item_id),
            )
            conn.commit()

            log.debug(f"Reserved work item {item_id} from queue {self._queue_name}")
            return item_id

    def release_input(
        self,
        item_id: str,
        state: State,
        exception_type: Optional[ExceptionType] = None,
        code: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Release a reserved input work item."""
        now = self._now()

        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE work_items
                SET state = ?, exception_type = ?, error_code = ?, error_message = ?,
                    completed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    state.value,
                    exception_type.value if exception_type else None,
                    code,
                    message,
                    now,
                    now,
                    item_id,
                ),
            )
            conn.commit()

        log.debug(f"Released work item {item_id} with state {state.value}")

    def create_output(
        self,
        parent_id: str,
        payload: Optional[JSONType] = None,
    ) -> str:
        """Create a new output work item."""
        item_id = str(uuid.uuid4())
        now = self._now()

        payload_json = json.dumps(payload) if payload is not None else None

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO work_items
                (id, queue_name, parent_id, state, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    self._output_queue_name,
                    parent_id,
                    State.PENDING.value,
                    payload_json,
                    now,
                    now,
                ),
            )
            conn.commit()

        log.debug(f"Created output work item {item_id} in queue {self._output_queue_name}")
        return item_id

    def load_payload(self, item_id: str) -> JSONType:
        """Load the payload of a work item."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT payload FROM work_items WHERE id = ?",
                (item_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise ValueError(f"Work item not found: {item_id}")

            payload_json = row["payload"]
            if payload_json is None:
                return {}
            return json.loads(payload_json)

    def save_payload(self, item_id: str, payload: JSONType) -> None:
        """Save the payload of a work item."""
        payload_json = json.dumps(payload) if payload is not None else None
        now = self._now()

        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE work_items
                SET payload = ?, updated_at = ?
                WHERE id = ?
                """,
                (payload_json, now, item_id),
            )
            conn.commit()

        log.debug(f"Saved payload for work item {item_id}")

    def list_files(self, item_id: str) -> List[str]:
        """List files attached to a work item."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT name FROM work_item_files WHERE work_item_id = ?",
                (item_id,),
            )
            return [row["name"] for row in cursor.fetchall()]

    def get_file(self, item_id: str, name: str) -> bytes:
        """Get file content from a work item."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT file_path FROM work_item_files WHERE work_item_id = ? AND name = ?",
                (item_id, name),
            )
            row = cursor.fetchone()

            if row is None:
                raise ValueError(f"File not found: {name} in work item {item_id}")

            file_path = Path(row["file_path"])
            return file_path.read_bytes()

    def add_file(
        self,
        item_id: str,
        name: str,
        original_name: str,
        content: bytes,
    ) -> None:
        """Add a file to a work item."""
        file_id = str(uuid.uuid4())
        now = self._now()

        # Create item-specific directory
        item_dir = self._files_dir / item_id
        item_dir.mkdir(parents=True, exist_ok=True)

        # Save file to disk
        file_path = item_dir / f"{file_id}_{name}"
        file_path.write_bytes(content)

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO work_item_files
                (id, work_item_id, name, original_name, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (file_id, item_id, name, original_name, str(file_path), now),
            )
            conn.commit()

        log.debug(f"Added file {name} to work item {item_id}")

    def remove_file(self, item_id: str, name: str) -> None:
        """Remove a file from a work item."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT file_path FROM work_item_files WHERE work_item_id = ? AND name = ?",
                (item_id, name),
            )
            row = cursor.fetchone()

            if row is None:
                return

            # Delete file from disk
            file_path = Path(row["file_path"])
            if file_path.exists():
                file_path.unlink()

            # Delete database record
            conn.execute(
                "DELETE FROM work_item_files WHERE work_item_id = ? AND name = ?",
                (item_id, name),
            )
            conn.commit()

        log.debug(f"Removed file {name} from work item {item_id}")

    # Extended methods

    def seed_input(
        self,
        payload: Optional[JSONType] = None,
        files: Optional[Dict[str, bytes]] = None,
        queue_name: Optional[str] = None,
    ) -> str:
        """Seed a new input work item into the queue."""
        item_id = str(uuid.uuid4())
        now = self._now()
        target_queue = queue_name or self._queue_name

        payload_json = json.dumps(payload) if payload is not None else None

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO work_items
                (id, queue_name, state, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    target_queue,
                    State.PENDING.value,
                    payload_json,
                    now,
                    now,
                ),
            )
            conn.commit()

        # Add files if provided
        if files:
            for name, content in files.items():
                self.add_file(item_id, name, name, content)

        log.info(f"Seeded work item {item_id} into queue {target_queue}")
        return item_id

    def list_items(
        self,
        queue_name: Optional[str] = None,
        state: Optional[State] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List work items in a queue."""
        target_queue = queue_name or self._queue_name

        query = "SELECT * FROM work_items WHERE queue_name = ?"
        params: List[Any] = [target_queue]

        if state is not None:
            query += " AND state = ?"
            params.append(state.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # Parse JSON payload
                if item.get("payload"):
                    try:
                        item["payload"] = json.loads(item["payload"])
                    except json.JSONDecodeError:
                        pass
                items.append(item)
            return items

    def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get detailed info about a work item."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM work_items WHERE id = ?",
                (item_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise ValueError(f"Work item not found: {item_id}")

            item = dict(row)
            if item.get("payload"):
                try:
                    item["payload"] = json.loads(item["payload"])
                except json.JSONDecodeError:
                    pass

            # Include files
            item["files"] = self.list_files(item_id)

            return item

    def delete_item(self, item_id: str) -> None:
        """Delete a work item and its files."""
        # Delete files from disk
        item_dir = self._files_dir / item_id
        if item_dir.exists():
            import shutil
            shutil.rmtree(item_dir)

        with self._get_conn() as conn:
            # Delete file records
            conn.execute(
                "DELETE FROM work_item_files WHERE work_item_id = ?",
                (item_id,),
            )
            # Delete work item
            conn.execute(
                "DELETE FROM work_items WHERE id = ?",
                (item_id,),
            )
            conn.commit()

        log.info(f"Deleted work item {item_id}")

    def get_queue_stats(self, queue_name: Optional[str] = None) -> Dict[str, int]:
        """
        Get statistics for a queue.

        Args:
            queue_name: Queue name (None for default).

        Returns:
            Dict with counts by state.
        """
        target_queue = queue_name or self._queue_name

        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT state, COUNT(*) as count
                FROM work_items
                WHERE queue_name = ?
                GROUP BY state
                """,
                (target_queue,),
            )

            stats = {
                "pending": 0,
                "in_progress": 0,
                "done": 0,
                "failed": 0,
                "total": 0,
            }

            for row in cursor.fetchall():
                state = row["state"].lower()
                count = row["count"]
                if state in stats:
                    stats[state] = count
                stats["total"] += count

            return stats
