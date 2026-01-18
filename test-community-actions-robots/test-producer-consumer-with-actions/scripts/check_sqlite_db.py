#!/usr/bin/env python3
"""Check contents of SQLite work items database."""

import json
import os
import sqlite3
import sys
from pathlib import Path

db_path = sys.argv[1] if len(sys.argv) > 1 else "devdata/work_items.db"

if not Path(db_path).exists():
    print(f"Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print(f"\n{'='*80}")
print(f"Database: {db_path}")
print(f"{'='*80}\n")

# Count work items by state
cursor = conn.execute("""
    SELECT state, COUNT(*) as count
    FROM work_items
    GROUP BY state
    ORDER BY state
""")

print("Work Items by State:")
print("-" * 40)
for row in cursor:
    print(f"  {row['state']:10s}: {row['count']:3d}")

# Show all work items
cursor = conn.execute("""
    SELECT id, queue_name, parent_id, state,
           SUBSTR(payload, 1, 100) as payload_preview,
           created_at, reserved_at, released_at
    FROM work_items
    ORDER BY created_at DESC
    LIMIT 20
""")

print(f"\n{'='*80}")
print("Recent Work Items (last 20):")
print(f"{'='*80}\n")

for row in cursor:
    print(f"ID: {row['id']}")
    print(f"  Queue: {row['queue_name']}")
    print(f"  State: {row['state']}")
    print(f"  Parent: {row['parent_id'] or 'None (root)'}")
    print(f"  Payload: {row['payload_preview']}...")
    print(f"  Created: {row['created_at']}")
    if row['reserved_at']:
        print(f"  Reserved: {row['reserved_at']}")
    if row['released_at']:
        print(f"  Released: {row['released_at']}")
    print()

conn.close()
