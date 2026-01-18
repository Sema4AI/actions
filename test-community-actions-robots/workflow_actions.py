"""
Producer-Consumer Workflow Actions for Community Action Server.

These actions demonstrate the work-items pattern using the new
actions.work_items package - a drop-in replacement for robocorp.workitems.

Usage:
    1. Call `producer` action with an org name to create work items
    2. Call `consumer` action to process work items (clone repos)
    3. Call `get_queue_status` to monitor progress

The work-items package provides:
    - robocorp-compatible API: `inputs`, `outputs` singletons
    - Context managers for automatic release
    - Multiple adapters: SQLite, FileAdapter (Control Room compatible)
    - Email parsing, glob file patterns, and more
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional

import requests
from sema4ai.actions import action, Response

# Import the new work-items package (robocorp-compatible API)
from actions.work_items import (
    inputs,
    outputs,
    seed_input,
    get_context,
    init,
    create_adapter,
    EmptyQueue,
    BusinessException,
)


def _ensure_init():
    """Initialize work items context if not already done."""
    try:
        get_context()
    except RuntimeError:
        # Set defaults if env vars not set
        if not os.environ.get("RC_WORKITEM_DB_PATH"):
            # Use action server datadir if available
            datadir = os.environ.get("SEMA4AI_ACTION_SERVER_DATADIR", ".")
            os.environ["RC_WORKITEM_DB_PATH"] = str(Path(datadir) / "workitems.db")
        init()


@action
def producer(org_name: str) -> Response[dict]:
    """
    Fetch repositories from a GitHub organization and create work items.

    This is the producer step - it queries GitHub for repositories and
    creates a work item for each one that the consumer will process.

    Args:
        org_name: GitHub organization name (e.g., "sema4ai", "joshyorko")

    Returns:
        Summary of created work items including count and repository names.
    """
    _ensure_init()

    # Fetch repositories from GitHub API
    url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {"Accept": "application/vnd.github.v3+json"}

    # Add token if available
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers, params={"per_page": 100})

    if response.status_code != 200:
        return Response(
            result={
                "status": "error",
                "error": f"GitHub API error: {response.status_code}",
                "message": response.text,
            }
        )

    repos = response.json()
    created_items = []

    for repo in repos:
        # Create a work item for each repository
        payload = {
            "org": org_name,
            "name": repo["name"],
            "url": repo["clone_url"],
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "is_fork": repo.get("fork", False),
        }

        item_id = seed_input(payload=payload, queue_name="repos")
        created_items.append({
            "id": item_id,
            "name": repo["name"],
        })

    return Response(
        result={
            "status": "success",
            "org": org_name,
            "items_created": len(created_items),
            "repositories": [item["name"] for item in created_items],
        }
    )


@action
def consumer(max_items: int = 10) -> Response[dict]:
    """
    Process work items by cloning repositories.

    This is the consumer step - it processes work items created by the
    producer, cloning each repository.

    Uses the robocorp-compatible API with context managers for automatic
    release on success/failure.

    Args:
        max_items: Maximum number of items to process in this run.

    Returns:
        Summary of processed work items with success/failure counts.
    """
    _ensure_init()

    # Set queue to repos
    os.environ["RC_WORKITEM_QUEUE_NAME"] = "repos"
    init()  # Re-init with new queue

    processed = []
    success_count = 0
    fail_count = 0

    try:
        from git import Repo
    except ImportError:
        return Response(
            result={
                "status": "error",
                "error": "GitPython not installed",
            }
        )

    # Create temp directory for clones
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Use robocorp-compatible singleton iteration
        for item in inputs:
            if len(processed) >= max_items:
                break

            payload = item.payload
            repo_name = payload.get("name", "unknown")
            clone_url = payload.get("url")

            # Use context manager for automatic release
            with item:
                if not clone_url:
                    raise BusinessException(
                        "No clone URL in work item",
                        code="MISSING_URL",
                    )

                # Clone the repository (shallow clone for efficiency)
                repo_path = temp_path / repo_name

                # Inject token if available
                token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
                actual_url = clone_url
                if token and clone_url.startswith("https://"):
                    scheme, rest = clone_url.split("//", 1)
                    actual_url = f"{scheme}//{token}@{rest}"

                Repo.clone_from(actual_url, repo_path, depth=1)

                # Create output using outputs singleton
                outputs.create({
                    "name": repo_name,
                    "org": payload.get("org"),
                    "status": "cloned",
                    "path": str(repo_path),
                })

                success_count += 1
                processed.append({
                    "name": repo_name,
                    "status": "success",
                })
                # item.done() called automatically by context manager

    # Count failures from released items
    fail_count = len([i for i in inputs.released if i.state.value == "FAILED"])

    return Response(
        result={
            "status": "completed",
            "processed": len(processed) + fail_count,
            "success": success_count,
            "failed": fail_count,
            "items": processed,
        }
    )


@action
def get_queue_status(queue_name: str = "repos") -> Response[dict]:
    """
    Get the status of a work items queue.

    Use this to monitor the progress of producer-consumer workflows.

    Args:
        queue_name: Name of the queue to check (default: "repos")

    Returns:
        Queue statistics including pending, in-progress, done, and failed counts.
    """
    _ensure_init()

    ctx = get_context()
    adapter = ctx.adapter

    stats = adapter.get_queue_stats(queue_name=queue_name)

    return Response(
        result={
            "queue": queue_name,
            **stats,
        }
    )


@action
def seed_work_item(
    payload: str,
    queue_name: str = "default",
) -> Response[dict]:
    """
    Seed a single work item into a queue.

    This is a utility action to manually add work items.

    Args:
        payload: JSON string with the work item payload
        queue_name: Queue to add the item to (default: "default")

    Returns:
        The created work item ID.
    """
    _ensure_init()

    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError as e:
        return Response(
            result={
                "status": "error",
                "error": f"Invalid JSON: {e}",
            }
        )

    item_id = seed_input(payload=payload_dict, queue_name=queue_name)

    return Response(
        result={
            "status": "success",
            "item_id": item_id,
            "queue": queue_name,
        }
    )


@action
def list_work_items(
    queue_name: str = "default",
    state: Optional[str] = None,
    limit: int = 50,
) -> Response[dict]:
    """
    List work items in a queue.

    Args:
        queue_name: Queue to list items from (default: "default")
        state: Filter by state (PENDING, IN_PROGRESS, DONE, FAILED)
        limit: Maximum items to return (default: 50)

    Returns:
        List of work items with their details.
    """
    _ensure_init()

    ctx = get_context()
    adapter = ctx.adapter

    # Import State enum
    from actions.work_items import State

    state_enum = None
    if state:
        try:
            state_enum = State(state.upper())
        except ValueError:
            return Response(
                result={
                    "status": "error",
                    "error": f"Invalid state: {state}. Use PENDING, IN_PROGRESS, DONE, or FAILED",
                }
            )

    items = adapter.list_items(
        queue_name=queue_name,
        state=state_enum,
        limit=limit,
    )

    return Response(
        result={
            "status": "success",
            "queue": queue_name,
            "count": len(items),
            "items": items,
        }
    )
