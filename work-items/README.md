# actions-work-items

A drop-in replacement for `robocorp-workitems` with broader applicability beyond robots.

## Overview

`actions-work-items` provides work item management for producer-consumer workflows. It enables:

- **Robots/Automations**: Traditional RPA producer-consumer patterns
- **Microservices**: Async job queues with persistent state
- **ETL Pipelines**: Data processing with tracking and error handling
- **Action Server Integration**: Native REST API for work items

## Installation

```bash
pip install actions-work-items
```

## Quick Start

### robocorp-workitems Compatible API

```python
from actions.work_items import inputs, outputs

# Process work items using singleton pattern
for item in inputs:
    data = item.payload
    # Process...
    outputs.create({"result": "processed"})
    item.done()
```

### Context Manager Pattern (Recommended)

```python
from actions.work_items import inputs, outputs, BusinessException

for item in inputs:
    with item:  # Auto-release on exit
        if not item.payload.get("required_field"):
            raise BusinessException("Missing required field")

        # Process item...
        outputs.create({"status": "success"})
        # item.done() called automatically
```

### Explicit Initialization

```python
from actions.work_items import init, create_adapter, inputs, outputs

# Create specific adapter
adapter = create_adapter("sqlite", db_path="./my-workitems.db")
init(adapter)

for item in inputs:
    # Process...
```

## Adapters

### SQLiteAdapter (Default)

Persistent local storage using SQLite database.

```python
from actions.work_items import SQLiteAdapter, init

adapter = SQLiteAdapter(
    db_path="./workitems.db",
    queue_name="default",
    files_dir="./work_item_files",
)
init(adapter)
```

Environment variables:
- `RC_WORKITEM_DB_PATH`: Database path (default: `./workitems.db`)
- `RC_WORKITEM_QUEUE_NAME`: Input queue (default: `default`)
- `RC_WORKITEM_OUTPUT_QUEUE_NAME`: Output queue (default: `{queue}_output`)
- `RC_WORKITEM_FILES_DIR`: Files directory (default: `./work_item_files`)

### FileAdapter

JSON file-based storage compatible with Robocorp Control Room format.

```python
from actions.work_items import FileAdapter, init

adapter = FileAdapter(
    input_path="./output/work-items-in",
    output_path="./output/work-items-out",
)
init(adapter)
```

Environment variables:
- `RC_WORKITEM_INPUT_PATH`: Input directory
- `RC_WORKITEM_OUTPUT_PATH`: Output directory

## Features

### Producer Pattern

```python
from actions.work_items import seed_input, init

init()

# Create work items for processing
for data in fetch_data():
    seed_input(
        payload={"url": data["url"], "name": data["name"]},
        queue_name="downloads",
    )
```

### File Attachments

```python
from actions.work_items import inputs, outputs

for item in inputs:
    with item:
        # List files
        files = item.list_files()

        # Get file content
        content = item.get_file("data.csv")

        # Add files (single or glob pattern)
        item.add_file(path="./report.pdf")
        item.add_files("./output/*.csv")

        # Remove files
        item.remove_file("temp.txt", missing_ok=True)
        item.remove_files("*.tmp")
```

### Email Parsing

```python
from actions.work_items import inputs

for item in inputs:
    with item:
        # Parse email attachment
        email = item.get_email("message.eml")

        print(f"From: {email.sender}")
        print(f"Subject: {email.subject}")
        print(f"Body: {email.body}")
```

### Error Handling

```python
from actions.work_items import (
    inputs,
    BusinessException,
    ApplicationException,
)

for item in inputs:
    with item:
        try:
            process(item.payload)
        except ValidationError as e:
            # Business error - don't retry
            raise BusinessException(str(e), code="VALIDATION_ERROR")
        except ConnectionError as e:
            # Application error - may retry
            raise ApplicationException(str(e), code="CONNECTION_ERROR")
```

## Action Server Integration

The Action Server provides REST endpoints at `/api/work-items`:

```bash
# Create work item
curl -X POST http://localhost:8080/api/work-items \
  -H "Content-Type: application/json" \
  -d '{"payload": {"org": "sema4ai"}, "queue_name": "repos"}'

# List work items
curl http://localhost:8080/api/work-items?queue_name=repos&state=PENDING

# Get queue stats
curl http://localhost:8080/api/work-items/stats?queue_name=repos
```

## API Reference

### Singletons

- `inputs` - Inputs collection singleton
- `outputs` - Outputs collection singleton

### Functions

- `init(adapter=None)` - Initialize context
- `create_adapter(type=None, **kwargs)` - Create adapter
- `seed_input(payload, files, queue_name)` - Seed new input
- `get_context()` - Get current context
- `get_input()` - Get next input
- `create_output(payload, files, save)` - Create output

### Classes

- `Input` - Input work item with `done()`, `fail()`, context manager
- `Output` - Output work item with `save()`
- `Inputs` - Collection with iteration, indexing, `current`, `released`
- `Outputs` - Collection with `create()`, `last`

### Adapters

- `BaseAdapter` - Abstract interface
- `SQLiteAdapter` - SQLite storage
- `FileAdapter` - JSON file storage

### Types

- `State` - PENDING, IN_PROGRESS, DONE, FAILED
- `ExceptionType` - BUSINESS, APPLICATION
- `Email` - Parsed email dataclass
- `Address` - Email address dataclass

### Exceptions

- `EmptyQueue` - No items available
- `BusinessException` - Expected failure (no retry)
- `ApplicationException` - Unexpected failure (may retry)

## Migration from robocorp-workitems

```python
# Before (robocorp-workitems)
from robocorp import workitems

for item in workitems.inputs:
    workitems.outputs.create(payload=item.payload)
    item.done()

# After (actions-work-items) - same API!
from actions.work_items import inputs, outputs

for item in inputs:
    outputs.create(payload=item.payload)
    item.done()
```

## License

Apache 2.0 - Based on robocorp-workitems
