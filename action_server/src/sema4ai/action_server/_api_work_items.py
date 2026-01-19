"""
Work Items API endpoints for the Action Server.

Provides REST endpoints for managing work items that can be used
by producer-consumer automation workflows.
"""

import logging
from typing import Any, Dict, List, Optional

import fastapi
from fastapi import File, UploadFile
from fastapi.routing import APIRouter
from pydantic import BaseModel

from sema4ai.action_server._settings import get_settings

log = logging.getLogger(__name__)

work_items_api_router = APIRouter(prefix="/api/work-items")


# Pydantic models for API


class WorkItemCreate(BaseModel):
    """Request to create/seed a work item."""

    payload: Optional[Dict[str, Any]] = None
    queue_name: Optional[str] = None


class WorkItemResponse(BaseModel):
    """Response with work item details."""

    id: str
    queue_name: str
    state: str
    payload: Optional[Dict[str, Any]] = None
    parent_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    files: List[str] = []
    created_at: str
    updated_at: str


class WorkItemListResponse(BaseModel):
    """Response with list of work items."""

    items: List[WorkItemResponse]
    total: int


class QueueStatsResponse(BaseModel):
    """Response with queue statistics."""

    queue_name: str
    pending: int
    in_progress: int
    done: int
    failed: int
    total: int


# Lazy initialization of adapter
_adapter = None


def _get_adapter():
    """
    Get or create the SQLite adapter for work items.

    Uses the action server's datadir for storage.
    """
    global _adapter
    if _adapter is not None:
        return _adapter

    try:
        from actions.work_items import SQLiteAdapter
    except ImportError:
        log.warning("actions-work-items package not installed, work items API disabled")
        return None

    settings = get_settings()
    db_path = settings.datadir / "workitems.db"
    files_dir = settings.datadir / "work_item_files"

    _adapter = SQLiteAdapter(
        db_path=str(db_path),
        queue_name="default",
        files_dir=str(files_dir),
    )
    return _adapter


def _check_adapter():
    """Get adapter or raise 503 if not available."""
    adapter = _get_adapter()
    if adapter is None:
        raise fastapi.HTTPException(
            status_code=503,
            detail="Work items not available - actions-work-items package not installed",
        )
    return adapter


@work_items_api_router.post("", response_model=WorkItemResponse)
async def create_work_item(request: WorkItemCreate):
    """
    Seed a new input work item into the queue.

    This is typically used by producer tasks to create work for consumers.
    """
    adapter = _check_adapter()

    item_id = adapter.seed_input(
        payload=request.payload,
        queue_name=request.queue_name,
    )

    item = adapter.get_item(item_id)
    return WorkItemResponse(
        id=item["id"],
        queue_name=item["queue_name"],
        state=item["state"],
        payload=item.get("payload"),
        parent_id=item.get("parent_id"),
        error_code=item.get("error_code"),
        error_message=item.get("error_message"),
        files=item.get("files", []),
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


@work_items_api_router.get("", response_model=WorkItemListResponse)
async def list_work_items(
    queue_name: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 100,
):
    """
    List work items in a queue.

    Args:
        queue_name: Queue to list (default: default)
        state: Filter by state (PENDING, IN_PROGRESS, DONE, FAILED)
        limit: Maximum items to return
    """
    adapter = _check_adapter()

    # Convert state string to enum if provided
    state_enum = None
    if state:
        try:
            from actions.work_items import State

            state_enum = State(state.upper())
        except (ValueError, ImportError):
            raise fastapi.HTTPException(
                status_code=400, detail=f"Invalid state: {state}"
            )

    items = adapter.list_items(
        queue_name=queue_name,
        state=state_enum,
        limit=limit,
    )

    response_items = [
        WorkItemResponse(
            id=item["id"],
            queue_name=item["queue_name"],
            state=item["state"],
            payload=item.get("payload"),
            parent_id=item.get("parent_id"),
            error_code=item.get("error_code"),
            error_message=item.get("error_message"),
            files=item.get("files", []),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )
        for item in items
    ]

    return WorkItemListResponse(
        items=response_items,
        total=len(response_items),
    )


@work_items_api_router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats(queue_name: Optional[str] = None):
    """Get statistics for a queue."""
    adapter = _check_adapter()

    queue = queue_name or "default"
    stats = adapter.get_queue_stats(queue_name=queue)

    return QueueStatsResponse(
        queue_name=queue,
        **stats,
    )


@work_items_api_router.get("/{item_id}", response_model=WorkItemResponse)
async def get_work_item(item_id: str):
    """Get details of a specific work item."""
    adapter = _check_adapter()

    try:
        item = adapter.get_item(item_id)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=404, detail=f"Work item not found: {item_id}"
        )

    return WorkItemResponse(
        id=item["id"],
        queue_name=item["queue_name"],
        state=item["state"],
        payload=item.get("payload"),
        parent_id=item.get("parent_id"),
        error_code=item.get("error_code"),
        error_message=item.get("error_message"),
        files=item.get("files", []),
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


@work_items_api_router.delete("/{item_id}")
async def delete_work_item(item_id: str):
    """Delete a work item and its files."""
    adapter = _check_adapter()

    try:
        adapter.delete_item(item_id)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=404, detail=f"Work item not found: {item_id}"
        )

    return {"status": "deleted", "id": item_id}


@work_items_api_router.post("/{item_id}/files")
async def upload_file(
    item_id: str,
    file: UploadFile = File(...),
):
    """
    Upload a file attachment to a work item.
    """
    adapter = _check_adapter()

    try:
        adapter.get_item(item_id)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=404, detail=f"Work item not found: {item_id}"
        )

    content = await file.read()
    adapter.add_file(
        item_id=item_id,
        name=file.filename or "unnamed",
        original_name=file.filename or "unnamed",
        content=content,
    )

    return {
        "status": "uploaded",
        "item_id": item_id,
        "filename": file.filename,
        "size": len(content),
    }


@work_items_api_router.get("/{item_id}/files")
async def list_files(item_id: str):
    """List files attached to a work item."""
    adapter = _check_adapter()

    try:
        adapter.get_item(item_id)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=404, detail=f"Work item not found: {item_id}"
        )

    files = adapter.list_files(item_id)
    return {"item_id": item_id, "files": files}


@work_items_api_router.get("/{item_id}/files/{filename}")
async def download_file(item_id: str, filename: str):
    """Download a file from a work item."""
    adapter = _check_adapter()

    try:
        content = adapter.get_file(item_id, filename)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=404, detail=f"File not found: {filename} in work item {item_id}"
        )

    from fastapi.responses import Response

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@work_items_api_router.delete("/{item_id}/files/{filename}")
async def delete_file(item_id: str, filename: str):
    """Delete a file from a work item."""
    adapter = _check_adapter()

    try:
        adapter.get_item(item_id)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=404, detail=f"Work item not found: {item_id}"
        )

    adapter.remove_file(item_id, filename)
    return {
        "status": "deleted",
        "item_id": item_id,
        "filename": filename,
    }
