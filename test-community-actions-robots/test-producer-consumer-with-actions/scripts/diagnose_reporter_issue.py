#!/usr/bin/env python3
"""Diagnose why Reporter is showing incorrect statistics."""

import json
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
print(f"Reporter Issue Diagnosis")
print(f"{'='*80}\n")

# Get all work items in the Consumer's output queue
cursor = conn.execute("""
    SELECT id, queue_name, state, payload
    FROM work_items
    WHERE queue_name LIKE '%output%'
    ORDER BY created_at DESC
""")

print("Work Items in Output Queues:")
print("-" * 80)

producer_format_count = 0
consumer_format_count = 0
reporter_items = 0

for row in cursor:
    payload = json.loads(row['payload'])
    print(f"\nID: {row['id']}")
    print(f"  Queue: {row['queue_name']}")
    print(f"  State: {row['state']}")
    print(f"  Payload keys: {list(payload.keys())}")

    # Check format
    if payload.get("TYPE") == "Reporter":
        reporter_items += 1
        print(f"  Format: Reporter metadata item")
    elif payload.get("callid") and payload.get("evaluationTemplateId"):
        producer_format_count += 1
        print(f"  Format: Producer format (callid + evaluationTemplateId)")
    elif payload.get("contact_id"):
        consumer_format_count += 1
        print(f"  Format: Consumer format (contact_id)")
    else:
        print(f"  Format: Unknown")

print(f"\n{'='*80}")
print("Summary:")
print("-" * 80)
print(f"  Reporter metadata items: {reporter_items}")
print(f"  Producer format items: {producer_format_count}")
print(f"  Consumer format items: {consumer_format_count}")
print(f"\n{'='*80}")

print("\nDiagnosis:")
print("-" * 80)
if producer_format_count == 0 and consumer_format_count > 0:
    print("❌ ISSUE FOUND: Reporter is looking for producer format items,")
    print("   but only consumer format items exist in the output queue.")
    print("   The Consumer task consumes producer items and creates new outputs.")
    print("\n✅ SOLUTION: Reporter should count consumer format items instead.")
else:
    print("✅ No obvious format mismatch detected.")

conn.close()
