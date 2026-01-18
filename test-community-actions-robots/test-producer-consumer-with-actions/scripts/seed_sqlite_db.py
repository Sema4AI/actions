#!/usr/bin/env python3
"""Seed SQLite database with initial work items for testing.

This script creates initial work items in the SQLite database for the producer task to process.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from robocorp_adapters_custom._sqlite import SQLiteAdapter


def seed_producer_workitem():
    """Create initial S3 trigger work item for producer."""

    # Set environment for SQLite adapter
    os.environ["RC_WORKITEM_DB_PATH"] = "devdata/work_items.db"
    os.environ["RC_WORKITEM_QUEUE_NAME"] = "fetch_repos"

    # Initialize adapter
    adapter = SQLiteAdapter()

    # Load test input payload
    test_input_path = Path("devdata/work-items-in/input-for-producer/work-items.json")

    if not test_input_path.exists():
        print(f"Error: Test input file not found: {test_input_path}")
        sys.exit(1)

    with open(test_input_path) as f:
        work_items = json.load(f)

    if not work_items:
        print("Error: No work items found in test input")
        sys.exit(1)

    # Create initial work item for producer directly in the INPUT queue
    # Note: create_output() creates items in {queue}_output queue, but Producer needs input queue
    payload = work_items[0]["payload"]
    import uuid as uuid_module
    item_id = str(uuid_module.uuid4())

    # Insert directly into input queue (not output queue)
    with adapter._pool.acquire() as conn:
        conn.execute("""
            INSERT INTO work_items (id, queue_name, parent_id, payload, state, created_at)
            VALUES (?, ?, ?, ?, 'PENDING', CURRENT_TIMESTAMP)
        """, (item_id, adapter.queue_name, None, json.dumps(payload)))
        conn.commit()

    print(f"✓ Created producer work item: {item_id}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    print(f"\nDatabase: {os.environ['RC_WORKITEM_DB_PATH']}")
    print(f"Queue: {os.environ['RC_WORKITEM_QUEUE_NAME']}")
    print(f"\nNow run: rcc run -t Producer -e devdata/env-sqlite-producer.json")


if __name__ == "__main__":
    seed_producer_workitem()
