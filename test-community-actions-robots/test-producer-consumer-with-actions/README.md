# Python Work Items with Custom Adapters

A producer-consumer automation template demonstrating scalable work item processing with pluggable database backends.

## Overview

This template showcases the [robocorp-adapters-custom](https://pypi.org/project/robocorp-adapters-custom/) library, which provides custom adapters for Robocorp's work items system. Instead of being limited to Robocorp Control Room, you can use **Redis**, **MongoDB**, or **SQLite** as your work item backend—perfect for self-hosted deployments, local development, and CI/CD pipelines.

## Setup

1. **Install RCC** (if not already installed):
   - Download from [RCC releases](https://github.com/joshyorko/rcc/releases)

2. **Start the backend services** (optional - for Redis/MongoDB):
   ```bash
   docker-compose up -d
   ```
   This starts:
   - **Redis** on port `6379` (with RedisInsight UI on `5540`)
   - **MongoDB** on port `27017` (with Mongo Express UI on `8081`)

3. **Configure your adapter** by setting environment variables or using the provided env files in `devdata/`

## Supported Adapters

| Adapter | Environment Variable | Use Case |
|---------|---------------------|----------|
| **SQLite** | `RC_WORKITEM_ADAPTER=robocorp_adapters_custom._sqlite.SQLiteAdapter` | Local development, single-machine workflows |
| **Redis** | `RC_WORKITEM_ADAPTER=robocorp_adapters_custom._redis.RedisAdapter` | Distributed workflows, high throughput |
| **MongoDB** | `RC_WORKITEM_ADAPTER=robocorp_adapters_custom._docdb.DocumentDBAdapter` | Document storage, AWS DocumentDB compatible |

## Usage

Run the producer (creates work items):
```bash
rcc run -t Producer -e devdata/env-sqlite-producer.json
# or with Redis:
rcc run -t Producer -e devdata/env-redis-producer.json
# or with MongoDB:
rcc run -t Producer -e devdata/env-docdb-producer.json
```

Run the consumer (processes work items):
```bash
rcc run -t Consumer -e devdata/env-sqlite-consumer.json
```

Run the reporter (generates summary):
```bash
rcc run -t Reporter -e devdata/env-sqlite-for-reporter.json
```

Run the interactive assistant:
```bash
rcc run -t AssistantOrg
```

To activate the environment for development:
```bash
rcc ht vars
```

## Configuration

Environment variables for each adapter:

### SQLite
```json
{
  "RC_WORKITEM_ADAPTER": "robocorp_adapters_custom._sqlite.SQLiteAdapter",
  "RC_WORKITEM_DB_PATH": "devdata/work_items.db",
  "RC_WORKITEM_QUEUE_NAME": "my_queue"
}
```

### Redis
```json
{
  "RC_WORKITEM_ADAPTER": "robocorp_adapters_custom._redis.RedisAdapter",
  "REDIS_HOST": "localhost",
  "REDIS_PORT": "6379",
  "RC_WORKITEM_QUEUE_NAME": "my_queue"
}
```

### MongoDB/DocumentDB
```json
{
  "RC_WORKITEM_ADAPTER": "robocorp_adapters_custom._docdb.DocumentDBAdapter",
  "DOCDB_HOSTNAME": "localhost",
  "DOCDB_PORT": "27017",
  "DOCDB_USERNAME": "user",
  "DOCDB_PASSWORD": "password",
  "DOCDB_DATABASE": "workitems"
}
```

## Project Structure

```
├── tasks.py                 # Main producer/consumer/reporter tasks
├── assistant.py             # Interactive GUI launcher
├── robot.yaml               # Task definitions
├── conda.yaml               # Python dependencies
├── docker-compose.yml       # Redis & MongoDB services
├── devdata/                 # Environment configs & test data
│   ├── env-sqlite-*.json    # SQLite adapter configs
│   ├── env-redis-*.json     # Redis adapter configs
│   └── env-docdb-*.json     # MongoDB adapter configs
├── scripts/                 # Helper utilities
│   ├── seed_sqlite_db.py    # Seed SQLite with test data
│   ├── seed_redis_db.py     # Seed Redis with test data
│   └── seed_docdb.py        # Seed MongoDB with test data
└── dashboard/               # Dashboard generation
```

## GitHub Actions

The included workflow supports matrix-based parallel execution with caching for faster builds. Each consumer job processes a shard of work items independently.

## Documentation Resources

* [robocorp-adapters-custom](https://pypi.org/project/robocorp-adapters-custom/) - Custom work item adapters
* [RCC Documentation](https://github.com/joshyorko/rcc/blob/master/docs/README.md)
* [Robocorp Documentation](https://robocorp.com/docs) - RPA patterns and examples
* [Robocorp Work Items](https://sema4.ai/docs/automation/python/robocorp/robocorp-workitems)

