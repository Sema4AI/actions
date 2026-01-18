"""
Producer-Consumer Workflow Actions Template.

This template demonstrates the work-items pattern for batch processing.
Customize the producer to fetch your data and the consumer to process it.

Usage:
    1. Call `producer` to create work items from your data source
    2. Call `consumer` to process work items
    3. Call `queue_status` to monitor progress
"""

import os
import json
from pathlib import Path
from typing import Optional

from sema4ai.actions import action, Response

from actions.work_items import (
    inputs,
    outputs,
    seed_input,
    get_context,
    init,
    BusinessException,
    State,
)


def _ensure_init():
    """Initialize work items context if not already done."""
    try:
        get_context()
    except RuntimeError:
        if not os.environ.get("RC_WORKITEM_DB_PATH"):
            # Support both neutral and legacy env var names
            datadir = os.environ.get("ACTION_SERVER_DATADIR") or os.environ.get("SEMA4AI_ACTION_SERVER_DATADIR", ".")
            os.environ["RC_WORKITEM_DB_PATH"] = str(Path(datadir) / "workitems.db")
        init()


@action
def producer(items: str) -> Response[dict]:
    """
    Create work items from input data.

    Customize this action to fetch data from your source (API, database, etc.)
    and create work items for the consumer to process.

    Args:
        items: JSON array of items to process. Each item becomes a work item.
               Example: '[{"name": "item1", "data": "value1"}]'

    Returns:
        Summary of created work items.
    """
    _ensure_init()

    try:
        items_list = json.loads(items)
    except json.JSONDecodeError as e:
        return Response(result={"status": "error", "error": f"Invalid JSON: {e}"})

    if not isinstance(items_list, list):
        return Response(result={"status": "error", "error": "Items must be a JSON array"})

    created = []
    for item in items_list:
        item_id = seed_input(payload=item, queue_name="default")
        created.append({"id": item_id, "payload": item})

    return Response(result={
        "status": "success",
        "items_created": len(created),
        "items": created,
    })


@action
def consumer(max_items: int = 10) -> Response[dict]:
    """
    Process work items from the queue.

    Customize this action with your processing logic.
    Uses context managers for automatic item release on success/failure.

    Args:
        max_items: Maximum number of items to process in this run.

    Returns:
        Summary of processed work items.
    """
    _ensure_init()

    os.environ["RC_WORKITEM_QUEUE_NAME"] = "default"
    init()

    processed = []
    success_count = 0

    for item in inputs:
        if len(processed) >= max_items:
            break

        payload = item.payload

        with item:  # Auto-releases on success, fails on exception
            # === CUSTOMIZE YOUR PROCESSING LOGIC HERE ===
            # Example: process the item payload
            result = {
                "processed": True,
                "input": payload,
                # Add your processing results here
            }

            # Create output for downstream steps
            outputs.create(result)

            success_count += 1
            processed.append({
                "id": item.id,
                "status": "success",
                "result": result,
            })

    fail_count = len([i for i in inputs.released if i.state == State.FAILED])

    return Response(result={
        "status": "completed",
        "processed": len(processed) + fail_count,
        "success": success_count,
        "failed": fail_count,
        "items": processed,
    })


@action
def queue_status(queue_name: str = "default") -> Response[dict]:
    """
    Get the status of a work items queue.

    Args:
        queue_name: Name of the queue to check.

    Returns:
        Queue statistics including pending, in-progress, done, and failed counts.
    """
    _ensure_init()

    ctx = get_context()
    stats = ctx.adapter.get_queue_stats(queue_name=queue_name)

    return Response(result={"queue": queue_name, **stats})
