#!/usr/bin/env python3
# scripts/seed_redis_db.py
import os, sys, json, base64, argparse
from pathlib import Path

# Add project root to path so "custom_adapters" can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_env(env_json: Path):
    if env_json and env_json.exists():
        data = json.loads(env_json.read_text())
        for k, v in data.items():
            os.environ[k] = os.path.expandvars(v)

def main():
    ap = argparse.ArgumentParser(description="Seed Redis with initial work items (from work-items.json).")
    ap.add_argument("--env", default="devdata/env-redis-producer.json",
                    help="Env JSON that sets RC_WORKITEM_QUEUE_NAME, REDIS_HOST, etc.")
    ap.add_argument("--json", default="devdata/work-items-in/input-for-producer/work-items.json",
                    help="Path to work-items.json (array of objects with at least 'payload').")
    args = ap.parse_args()

    load_env(Path(args.env))

    # Import your adapter after env is loaded
    from robocorp_adapters_custom._redis import RedisAdapter

    queue = os.getenv("RC_WORKITEM_QUEUE_NAME", "default")
    print(f"Seeding Redis queue: {queue}")

    items = json.loads(Path(args.json).read_text())
    if isinstance(items, dict):
        # allow single object too
        items = [items]
    if not items:
        raise SystemExit("No work items found in JSON.")

    adapter = RedisAdapter()

    created = 0
    for wi in items:
        payload = wi.get("payload", wi)  # be generous: accept either {"payload":{...}} or just {...}
        item_id = adapter.seed_input(payload=payload)
        created += 1

        print(f"✓ seeded {item_id} payload keys={list(payload)[:6]}...")

    print(f"\nDone. Seeded {created} item(s) into {queue}:pending.")
    print("Next:")
    print("  rcc run -e devdata/env-redis-producer.json -t Producer")
    print("  rcc run -e devdata/env-redis-consumer.json -t Consumer")

if __name__ == "__main__":
    main()
