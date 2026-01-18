#!/usr/bin/env python3
# scripts/seed_docdb.py
import os, sys, json, argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_env(env_json: Path):
    if env_json and env_json.exists():
        data = json.loads(env_json.read_text())
        for k, v in data.items():
            os.environ[k] = os.path.expandvars(v)

def main():
    ap = argparse.ArgumentParser(description="Seed DocumentDB/MongoDB with initial work items.")
    ap.add_argument("--env", default="devdata/env-docdb-local-producer.json",
                    help="Env JSON that sets DOCDB_* vars.")
    ap.add_argument("--json", default="devdata/work-items-in/input-for-producer/work-items.json",
                    help="Path to work-items.json.")
    args = ap.parse_args()

    load_env(Path(args.env))

    # Import your adapter after env is loaded
    from robocorp_adapters_custom._docdb import DocumentDBAdapter

    queue = os.getenv("RC_WORKITEM_QUEUE_NAME", "default")
    print(f"Seeding DocumentDB queue: {queue}")

    items = json.loads(Path(args.json).read_text())
    if isinstance(items, dict):
        items = [items]
    if not items:
        raise SystemExit("No work items found in JSON.")

    adapter = DocumentDBAdapter()

    created = 0
    for wi in items:
        payload = wi.get("payload", wi)
        item_id = adapter.seed_input(payload=payload)
        created += 1
        print(f"✓ seeded {item_id} payload keys={list(payload)[:6]}...")

    print(f"\nDone. Seeded {created} item(s) into {queue}.")
    print("Next:")
    print("  rcc run -e devdata/env-docdb-local-producer.json -t Producer")

if __name__ == "__main__":
    main()
