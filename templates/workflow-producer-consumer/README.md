# Workflow Producer-Consumer Template

This template demonstrates the producer-consumer workflow pattern using the `actions-work-items` package.

## Overview

The producer-consumer pattern is useful for:
- Processing batches of items asynchronously
- Distributing work across multiple runs
- Maintaining state between action invocations

## Actions

### `producer`
Creates work items from input data. Customize this to fetch data from your source (API, database, file, etc.).

### `consumer`
Processes work items one at a time. Customize this with your business logic.

### `queue_status`
Returns statistics about the work items queue.

## Usage

1. Start the action server:
   ```bash
   action-server start
   ```

2. Call the producer to create work items:
   ```bash
   curl -X POST http://localhost:8080/api/actions/producer/invoke \
     -H "Content-Type: application/json" \
     -d '{"items": "[{\"name\": \"item1\"}, {\"name\": \"item2\"}]"}'
   ```

3. Call the consumer to process items:
   ```bash
   curl -X POST http://localhost:8080/api/actions/consumer/invoke \
     -H "Content-Type: application/json" \
     -d '{"max_items": 10}'
   ```

4. Check queue status:
   ```bash
   curl -X POST http://localhost:8080/api/actions/queue_status/invoke \
     -H "Content-Type: application/json" \
     -d '{"queue_name": "default"}'
   ```

## Customization

- Modify `producer` to fetch data from your actual source
- Modify `consumer` to implement your processing logic
- Add error handling with `BusinessException` for expected failures
- Use `outputs.create()` to pass results between workflow steps
