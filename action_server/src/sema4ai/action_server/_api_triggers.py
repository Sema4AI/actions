"""
Triggers API for the Action Server.

Provides REST endpoints for managing webhook triggers.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

triggers_api_router = APIRouter(prefix="/api/triggers")


# ============================================================================
# Pydantic Models
# ============================================================================


class TriggerCreateRequest(BaseModel):
    """Request to create a trigger."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    # Target
    action_id: Optional[str] = None
    execution_mode: str = Field(default="run", pattern="^(run|work_item)$")
    work_item_queue: Optional[str] = None
    inputs_template: Dict[str, Any] = Field(default_factory=dict)

    # Trigger type
    trigger_type: str = Field(default="webhook", pattern="^(webhook|email|file_watch)$")

    # Webhook config
    webhook_secret: Optional[str] = None  # If None, one will be generated
    webhook_method: str = Field(default="POST", pattern="^(POST|PUT)$")

    # State
    enabled: bool = True

    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_max_per_minute: int = Field(default=60, ge=1)


class TriggerUpdateRequest(BaseModel):
    """Request to update a trigger."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None

    # Target
    action_id: Optional[str] = None
    execution_mode: Optional[str] = Field(default=None, pattern="^(run|work_item)$")
    work_item_queue: Optional[str] = None
    inputs_template: Optional[Dict[str, Any]] = None

    # Webhook config
    webhook_secret: Optional[str] = None
    webhook_method: Optional[str] = Field(default=None, pattern="^(POST|PUT)$")

    # State
    enabled: Optional[bool] = None

    # Rate limiting
    rate_limit_enabled: Optional[bool] = None
    rate_limit_max_per_minute: Optional[int] = Field(default=None, ge=1)


class TriggerResponse(BaseModel):
    """Response with trigger details."""

    id: str
    name: str
    description: Optional[str] = None

    # Target
    action_id: Optional[str] = None
    action_name: Optional[str] = None
    execution_mode: str
    work_item_queue: Optional[str] = None
    inputs_template: Dict[str, Any]

    # Trigger type
    trigger_type: str

    # Webhook config
    webhook_url: str  # Full URL for invoking the trigger
    webhook_secret_configured: bool  # Don't expose actual secret
    webhook_method: str

    # State
    enabled: bool
    created_at: str
    updated_at: str
    last_triggered_at: Optional[str] = None
    trigger_count: int

    # Rate limiting
    rate_limit_enabled: bool
    rate_limit_max_per_minute: int


class TriggerListResponse(BaseModel):
    """Response with list of triggers."""

    triggers: List[TriggerResponse]
    total: int


class InvocationResponse(BaseModel):
    """Response for trigger invocation."""

    id: str
    trigger_id: str
    invoked_at: str
    source_ip: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    status: str
    run_id: Optional[str] = None
    work_item_id: Optional[str] = None
    error_message: Optional[str] = None


class WebhookInvokeResponse(BaseModel):
    """Response for webhook invocation."""

    status: str  # 'accepted', 'rejected', 'rate_limited', 'error'
    invocation_id: Optional[str] = None
    run_id: Optional[str] = None
    work_item_id: Optional[str] = None
    message: Optional[str] = None


class SecretResponse(BaseModel):
    """Response with webhook secret."""

    webhook_secret: str


# ============================================================================
# Helper Functions
# ============================================================================


def _get_webhook_base_url() -> str:
    """Get the base URL for webhook endpoints."""
    from sema4ai.action_server._settings import get_settings

    settings = get_settings()
    base_url = settings.base_url or settings.server_url
    return base_url


def _trigger_to_response(
    trigger: "Trigger",
    action_name: Optional[str] = None,
) -> TriggerResponse:
    """Convert a Trigger model to a response."""
    base_url = _get_webhook_base_url()
    webhook_url = f"{base_url}/api/triggers/webhook/{trigger.id}"

    return TriggerResponse(
        id=trigger.id,
        name=trigger.name,
        description=trigger.description,
        action_id=trigger.action_id,
        action_name=action_name,
        execution_mode=trigger.execution_mode,
        work_item_queue=trigger.work_item_queue,
        inputs_template=(
            json.loads(trigger.inputs_template_json)
            if trigger.inputs_template_json
            else {}
        ),
        trigger_type=trigger.trigger_type,
        webhook_url=webhook_url,
        webhook_secret_configured=bool(trigger.webhook_secret),
        webhook_method=trigger.webhook_method,
        enabled=trigger.enabled,
        created_at=trigger.created_at,
        updated_at=trigger.updated_at,
        last_triggered_at=trigger.last_triggered_at,
        trigger_count=trigger.trigger_count,
        rate_limit_enabled=trigger.rate_limit_enabled,
        rate_limit_max_per_minute=trigger.rate_limit_max_per_minute,
    )


# ============================================================================
# Trigger CRUD Endpoints
# ============================================================================


@triggers_api_router.get("", response_model=TriggerListResponse)
async def list_triggers(
    enabled: Optional[bool] = None,
    trigger_type: Optional[str] = None,
    action_id: Optional[str] = None,
):
    """List all triggers with optional filters."""
    from sema4ai.action_server._models import Action, Trigger, get_db

    db = get_db()
    with db.connect():
        # Build query
        conditions = []
        values = []

        if enabled is not None:
            conditions.append("enabled = ?")
            values.append(1 if enabled else 0)

        if trigger_type:
            conditions.append("trigger_type = ?")
            values.append(trigger_type)

        if action_id:
            conditions.append("action_id = ?")
            values.append(action_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        triggers = db.select(
            Trigger,
            f"SELECT * FROM trigger WHERE {where_clause} ORDER BY created_at DESC",
            values if values else None,
        )

        # Get action names
        responses = []
        for trigger in triggers:
            action_name = None
            if trigger.action_id:
                try:
                    action = db.first(
                        Action,
                        "SELECT * FROM action WHERE id = ?",
                        [trigger.action_id],
                    )
                    action_name = action.name
                except KeyError:
                    pass

            responses.append(_trigger_to_response(trigger, action_name))

    return TriggerListResponse(triggers=responses, total=len(responses))


@triggers_api_router.post("", response_model=TriggerResponse)
async def create_trigger(request: TriggerCreateRequest):
    """Create a new trigger."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._gen_ids import gen_uuid
    from sema4ai.action_server._models import Action, Trigger, get_db
    from sema4ai.action_server._triggers import get_trigger_engine

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        # Verify action exists if specified
        action_name = None
        if request.action_id:
            try:
                action = db.first(
                    Action,
                    "SELECT * FROM action WHERE id = ?",
                    [request.action_id],
                )
                action_name = action.name
            except KeyError:
                raise HTTPException(
                    status_code=404, detail=f"Action not found: {request.action_id}"
                )

        trigger_id = gen_uuid("trigger")

        # Generate webhook secret if not provided
        webhook_secret = request.webhook_secret
        if webhook_secret is None:
            engine = get_trigger_engine()
            webhook_secret = engine.generate_webhook_secret()

        trigger = Trigger(
            id=trigger_id,
            name=request.name,
            description=request.description,
            action_id=request.action_id,
            execution_mode=request.execution_mode,
            work_item_queue=request.work_item_queue,
            inputs_template_json=json.dumps(request.inputs_template),
            trigger_type=request.trigger_type,
            webhook_secret=webhook_secret,
            webhook_method=request.webhook_method,
            enabled=request.enabled,
            created_at=datetime_to_str(now),
            updated_at=datetime_to_str(now),
            rate_limit_enabled=request.rate_limit_enabled,
            rate_limit_max_per_minute=request.rate_limit_max_per_minute,
        )

        with db.transaction():
            db.insert(trigger)

    log.info(f"Created trigger {trigger_id}: {request.name}")

    return _trigger_to_response(trigger, action_name)


@triggers_api_router.get("/{trigger_id}", response_model=TriggerResponse)
async def get_trigger(trigger_id: str):
    """Get a specific trigger by ID."""
    from sema4ai.action_server._models import Action, Trigger, get_db

    db = get_db()
    with db.connect():
        try:
            trigger = db.first(
                Trigger, "SELECT * FROM trigger WHERE id = ?", [trigger_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Trigger not found: {trigger_id}"
            )

        action_name = None
        if trigger.action_id:
            try:
                action = db.first(
                    Action,
                    "SELECT * FROM action WHERE id = ?",
                    [trigger.action_id],
                )
                action_name = action.name
            except KeyError:
                pass

    return _trigger_to_response(trigger, action_name)


@triggers_api_router.patch("/{trigger_id}", response_model=TriggerResponse)
async def update_trigger(trigger_id: str, request: TriggerUpdateRequest):
    """Update an existing trigger."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._models import Action, Trigger, get_db

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        try:
            trigger = db.first(
                Trigger, "SELECT * FROM trigger WHERE id = ?", [trigger_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Trigger not found: {trigger_id}"
            )

        updates = {"updated_at": datetime_to_str(now)}

        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.action_id is not None:
            if request.action_id:
                try:
                    db.first(
                        Action,
                        "SELECT * FROM action WHERE id = ?",
                        [request.action_id],
                    )
                except KeyError:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Action not found: {request.action_id}",
                    )
            updates["action_id"] = request.action_id or None
        if request.execution_mode is not None:
            updates["execution_mode"] = request.execution_mode
        if request.work_item_queue is not None:
            updates["work_item_queue"] = request.work_item_queue
        if request.inputs_template is not None:
            updates["inputs_template_json"] = json.dumps(request.inputs_template)
        if request.webhook_secret is not None:
            updates["webhook_secret"] = request.webhook_secret
        if request.webhook_method is not None:
            updates["webhook_method"] = request.webhook_method
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        if request.rate_limit_enabled is not None:
            updates["rate_limit_enabled"] = request.rate_limit_enabled
        if request.rate_limit_max_per_minute is not None:
            updates["rate_limit_max_per_minute"] = request.rate_limit_max_per_minute

        with db.transaction():
            db.update_by_id(Trigger, trigger_id, updates)

        # Refresh
        trigger = db.first(
            Trigger, "SELECT * FROM trigger WHERE id = ?", [trigger_id]
        )

        action_name = None
        if trigger.action_id:
            try:
                action = db.first(
                    Action,
                    "SELECT * FROM action WHERE id = ?",
                    [trigger.action_id],
                )
                action_name = action.name
            except KeyError:
                pass

    log.info(f"Updated trigger {trigger_id}")

    return _trigger_to_response(trigger, action_name)


@triggers_api_router.delete("/{trigger_id}")
async def delete_trigger(trigger_id: str):
    """Delete a trigger."""
    from sema4ai.action_server._models import Trigger, TriggerInvocation, get_db

    db = get_db()
    with db.connect():
        try:
            db.first(Trigger, "SELECT * FROM trigger WHERE id = ?", [trigger_id])
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Trigger not found: {trigger_id}"
            )

        with db.transaction():
            # Delete invocations first (foreign key constraint)
            db.execute(
                "DELETE FROM trigger_invocation WHERE trigger_id = ?", [trigger_id]
            )
            db.execute("DELETE FROM trigger WHERE id = ?", [trigger_id])

    log.info(f"Deleted trigger {trigger_id}")

    return {"status": "deleted", "id": trigger_id}


@triggers_api_router.get(
    "/{trigger_id}/invocations", response_model=List[InvocationResponse]
)
async def list_invocations(trigger_id: str, limit: int = 50, offset: int = 0):
    """Get invocation history for a trigger."""
    from sema4ai.action_server._models import Trigger, TriggerInvocation, get_db

    db = get_db()
    with db.connect():
        # Verify trigger exists
        try:
            db.first(Trigger, "SELECT * FROM trigger WHERE id = ?", [trigger_id])
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Trigger not found: {trigger_id}"
            )

        invocations = db.select(
            TriggerInvocation,
            """
            SELECT * FROM trigger_invocation
            WHERE trigger_id = ?
            ORDER BY invoked_at DESC
            LIMIT ? OFFSET ?
            """,
            [trigger_id, limit, offset],
        )

    return [
        InvocationResponse(
            id=inv.id,
            trigger_id=inv.trigger_id,
            invoked_at=inv.invoked_at,
            source_ip=inv.source_ip,
            payload=json.loads(inv.payload_json) if inv.payload_json else None,
            status=inv.status,
            run_id=inv.run_id,
            work_item_id=inv.work_item_id,
            error_message=inv.error_message,
        )
        for inv in invocations
    ]


@triggers_api_router.get("/{trigger_id}/secret", response_model=SecretResponse)
async def get_trigger_secret(trigger_id: str):
    """Get the webhook secret for a trigger."""
    from sema4ai.action_server._models import Trigger, get_db

    db = get_db()
    with db.connect():
        try:
            trigger = db.first(
                Trigger, "SELECT * FROM trigger WHERE id = ?", [trigger_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Trigger not found: {trigger_id}"
            )

    if not trigger.webhook_secret:
        raise HTTPException(
            status_code=404, detail="Trigger has no webhook secret configured"
        )

    return SecretResponse(webhook_secret=trigger.webhook_secret)


@triggers_api_router.post("/{trigger_id}/regenerate-secret", response_model=SecretResponse)
async def regenerate_trigger_secret(trigger_id: str):
    """Regenerate the webhook secret for a trigger."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._models import Trigger, get_db
    from sema4ai.action_server._triggers import get_trigger_engine

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        try:
            db.first(Trigger, "SELECT * FROM trigger WHERE id = ?", [trigger_id])
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Trigger not found: {trigger_id}"
            )

        engine = get_trigger_engine()
        new_secret = engine.generate_webhook_secret()

        with db.transaction():
            db.update_by_id(
                Trigger,
                trigger_id,
                {
                    "webhook_secret": new_secret,
                    "updated_at": datetime_to_str(now),
                },
            )

    log.info(f"Regenerated secret for trigger {trigger_id}")

    return SecretResponse(webhook_secret=new_secret)


# ============================================================================
# Webhook Endpoint (Public)
# ============================================================================


@triggers_api_router.post("/webhook/{trigger_id}", response_model=WebhookInvokeResponse)
@triggers_api_router.put("/webhook/{trigger_id}", response_model=WebhookInvokeResponse)
async def invoke_webhook(trigger_id: str, request: Request):
    """
    Public webhook endpoint for triggering actions.

    This endpoint is called by external systems to invoke a trigger.
    """
    from sema4ai.action_server._triggers import get_trigger_engine

    # Get payload
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = None
    else:
        body = await request.body()
        payload = body.decode("utf-8") if body else None

    # Get headers
    headers = dict(request.headers)

    # Get source IP
    source_ip = request.client.host if request.client else None
    # Check for forwarded IP
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        source_ip = forwarded.split(",")[0].strip()

    # Handle webhook
    engine = get_trigger_engine()
    result = await engine.handle_webhook(
        trigger_id=trigger_id,
        payload=payload,
        headers=headers,
        source_ip=source_ip,
    )

    # Map status to HTTP response
    status = result.get("status", "error")

    if status == "rejected":
        raise HTTPException(status_code=401, detail=result.get("message", "Rejected"))
    elif status == "rate_limited":
        raise HTTPException(
            status_code=429, detail=result.get("message", "Rate limited")
        )
    elif status == "error":
        raise HTTPException(
            status_code=500, detail=result.get("message", "Internal error")
        )

    return WebhookInvokeResponse(
        status=status,
        invocation_id=result.get("invocation_id"),
        run_id=result.get("run_id"),
        work_item_id=result.get("work_item_id"),
        message=result.get("message"),
    )


# ============================================================================
# Test Endpoint
# ============================================================================


@triggers_api_router.post("/{trigger_id}/test", response_model=WebhookInvokeResponse)
async def test_trigger(trigger_id: str, payload: Optional[Dict[str, Any]] = None):
    """
    Test a trigger with a sample payload.

    This is for testing triggers from the UI without needing external calls.
    """
    from sema4ai.action_server._triggers import get_trigger_engine

    engine = get_trigger_engine()
    result = await engine.handle_webhook(
        trigger_id=trigger_id,
        payload=payload or {},
        headers={"x-test-invocation": "true"},
        source_ip="127.0.0.1",
    )

    return WebhookInvokeResponse(
        status=result.get("status", "error"),
        invocation_id=result.get("invocation_id"),
        run_id=result.get("run_id"),
        work_item_id=result.get("work_item_id"),
        message=result.get("message"),
    )
