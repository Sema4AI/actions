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
import pandas as pd
from sema4ai.actions import action, Response

# Import robocorp log for structured logging
from robocorp import log

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


# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 10


def get_org_name() -> Optional[str]:
    """Get organization name from environment variable."""
    return os.getenv("ORG_NAME")


def repos(org_name: str) -> pd.DataFrame:
    """
    Fetch repositories from a GitHub organization or user.

    Args:
        org_name: The name of the organization or user

    Returns:
        pandas.DataFrame: DataFrame containing repository information
    """
    if not org_name:
        raise ValueError("Organization name is required.")
    
    log.info(f"Fetching repositories for organization: {org_name}")
    
    # Read token from environment (support both common names)
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    
    # Auto-detect entity type
    test_url = f"https://api.github.com/orgs/{org_name}"
    try:
        test_response = requests.get(test_url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        log.warn("Request timed out while determining entity type.")
        return pd.DataFrame()
    
    entity_type = "org" if test_response.status_code == 200 else "user"
    
    # Set the appropriate API endpoint
    base_url = "https://api.github.com"
    url = f"{base_url}/{'orgs' if entity_type == 'org' else 'users'}/{org_name}/repos"
    
    per_page = 100
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "fetch-repos-bot/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    repo_list = []
    page = 1

    while True:
        params = {
            "per_page": per_page,
            "page": page,
            "sort": "updated",
            "direction": "desc"
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            log.warn(f"Request timed out while fetching page {page}.")
            break
        
        # Handle rate limiting
        if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
            log.warn("Rate limit exceeded. Please try again later.")
            break
            
        if response.status_code != 200:
            log.warn(f"Failed to fetch repositories on page {page}: {response.status_code}")
            break

        fetched_repos = response.json()
        if not fetched_repos:
            break

        for repo in fetched_repos:
            if repo.get("private", False) and not token:
                continue

            repo_list.append({
                "Name": repo.get("name"),
                "Description": repo.get("description"),
                "Language": repo.get("language"),
                "Stars": repo.get("stargazers_count"),
                "URL": repo.get("clone_url"),
                "Created": repo.get("created_at"),
                "Last Updated": repo.get("updated_at"),
                "Is Fork": repo.get("fork", False),
                "Private": repo.get("private", False)
            })

        log.info(f"Fetched page {page} with {len(fetched_repos)} repositories. Total: {len(repo_list)}")
        
        if len(fetched_repos) < per_page:
            break
        page += 1

    log.info(f"Total repositories found: {len(repo_list)}")
    
    # Sort by stars
    repo_list.sort(key=lambda x: x["Stars"] or 0, reverse=True)
    
    return pd.DataFrame(repo_list)


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

    # Process input work items to get organization name
    for item in inputs:
        try:
            payload = item.payload
            if not isinstance(payload, dict):
                item.fail(
                    "APPLICATION",
                    code="INVALID_PAYLOAD",
                    message="Payload must be a dictionary",
                )
                continue

            # Use org_name from parameter, fall back to payload, then env var
            effective_org_name = org_name
            if not effective_org_name:
                effective_org_name = payload.get("org")
            if not effective_org_name:
                effective_org_name = get_org_name()

            if not effective_org_name:
                item.fail(
                    "APPLICATION",
                    code="MISSING_ORG_NAME",
                    message="Organization name is required in work item payload 'org' field or ORG_NAME environment variable.",
                )
                continue

            log.info(f"Processing organization: {effective_org_name}")

            # Get the DataFrame from repos() function with retry logic
            try:
                df = repos(effective_org_name)
            except Exception as e:
                error_msg = f"Failed to fetch repositories for {effective_org_name}: {str(e)}"
                log.exception(error_msg)
                item.fail("BUSINESS", code="FETCH_ERROR", message=error_msg)
                continue

            if df is not None and not df.empty:
                log.info(f"Processing {len(df)} repositories from DataFrame")
                rows = df.to_dict(orient="records")
                created_count = 0

                for row in rows:
                    try:
                        repo_payload = {
                            "org": effective_org_name,
                            "Name": row.get("Name"),
                            "URL": row.get("URL"),
                            "Description": row.get("Description"),
                            "Created": row.get("Created"),
                            "Last Updated": row.get("Last Updated"),
                            "Language": row.get("Language"),
                            "Stars": row.get("Stars"),
                            "Is Fork": row.get("Is Fork"),
                        }

                        # Validate required fields
                        if not repo_payload.get("URL") or not repo_payload.get("Name"):
                            log.warn(
                                f"Skipping repository with missing URL or Name: {repo_payload}"
                            )
                            continue

                        # Create work item (seed as new input for consumer)
                        seed_input(payload=repo_payload, queue_name="repos")
                        created_count += 1

                    except Exception as e:
                        log.critical(
                            f"Error creating work item for repository {row.get('Name', 'unknown')}: {str(e)}"
                        )
                        # Continue processing other repositories
                        continue

                log.info(
                    f"Created {created_count} work items out of {len(rows)} repositories"
                )

                # Mark the input item as done only after all work items are created
                item.done()

                return Response(
                    result={
                        "status": "success",
                        "org": effective_org_name,
                        "items_created": created_count,
                        "total_repos": len(rows),
                    }
                )
            else:
                log.warn("No data received from repos() function")
                item.fail(
                    "BUSINESS",
                    code="NO_DATA",
                    message="No repositories found for organization",
                )

        except Exception as e:
            error_msg = f"Unexpected error in producer task: {str(e)}"
            log.exception(error_msg)
            item.fail("APPLICATION", code="UNEXPECTED_ERROR", message=error_msg)

    # If no input work items, fetch directly using the org_name parameter
    if org_name:
        log.info(f"No input work items, fetching directly for: {org_name}")
        
        try:
            df = repos(org_name)
        except Exception as e:
            error_msg = f"Failed to fetch repositories for {org_name}: {str(e)}"
            log.exception(error_msg)
            return Response(
                result={
                    "status": "error",
                    "error": error_msg,
                }
            )

        if df is not None and not df.empty:
            rows = df.to_dict(orient="records")
            created_count = 0

            for row in rows:
                try:
                    repo_payload = {
                        "org": org_name,
                        "Name": row.get("Name"),
                        "URL": row.get("URL"),
                        "Description": row.get("Description"),
                        "Created": row.get("Created"),
                        "Last Updated": row.get("Last Updated"),
                        "Language": row.get("Language"),
                        "Stars": row.get("Stars"),
                        "Is Fork": row.get("Is Fork"),
                    }

                    if not repo_payload.get("URL") or not repo_payload.get("Name"):
                        log.warn(
                            f"Skipping repository with missing URL or Name: {repo_payload}"
                        )
                        continue

                    # Seed as new input for consumer
                    seed_input(payload=repo_payload, queue_name="repos")
                    created_count += 1

                except Exception as e:
                    log.critical(
                        f"Error creating work item for repository {row.get('Name', 'unknown')}: {str(e)}"
                    )
                    continue

            log.info(f"Created {created_count} work items out of {len(rows)} repositories")

            return Response(
                result={
                    "status": "success",
                    "org": org_name,
                    "items_created": created_count,
                    "total_repos": len(rows),
                }
            )
        else:
            return Response(
                result={
                    "status": "error",
                    "error": "No repositories found for organization",
                }
            )

    return Response(
        result={
            "status": "error",
            "error": "No organization name provided",
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
