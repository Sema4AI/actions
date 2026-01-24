"""
Schedules API for the Action Server.

Provides REST endpoints for managing scheduled action executions.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field, field_validator

log = logging.getLogger(__name__)

schedules_api_router = APIRouter(prefix="/api/schedules")
schedule_groups_api_router = APIRouter(prefix="/api/schedule-groups")


# ============================================================================
# Pydantic Models
# ============================================================================


class ScheduleCreateRequest(BaseModel):
    """Request to create a schedule."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    # Target
    action_id: Optional[str] = None
    execution_mode: str = Field(default="run", pattern="^(run|work_item)$")
    work_item_queue: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)

    # Schedule type and config
    schedule_type: str = Field(..., pattern="^(cron|interval|weekday|once)$")
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = Field(default=None, ge=1)
    weekday_config: Optional[Dict[str, Any]] = None
    once_at: Optional[str] = None

    timezone: str = Field(default="UTC")
    enabled: bool = True

    # Execution settings
    skip_if_running: bool = False
    max_concurrent: int = Field(default=1, ge=1)
    timeout_seconds: int = Field(default=3600, ge=1)

    # Retry policy
    retry_enabled: bool = False
    retry_max_attempts: int = Field(default=3, ge=1)
    retry_delay_seconds: int = Field(default=60, ge=1)
    retry_backoff_multiplier: float = Field(default=2.0, ge=1.0)

    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_max_per_hour: Optional[int] = Field(default=None, ge=1)
    rate_limit_max_per_day: Optional[int] = Field(default=None, ge=1)

    # Dependencies
    depends_on_schedule_id: Optional[str] = None
    dependency_mode: str = Field(
        default="after_success", pattern="^(after_success|after_any)$"
    )

    # Notifications
    notify_on_failure: bool = False
    notify_on_success: bool = False
    notification_webhook_url: Optional[str] = None
    notification_email: Optional[str] = None

    # Organization
    group_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0)

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v, info):
        if info.data.get("schedule_type") == "cron" and v:
            try:
                from croniter import croniter

                croniter(v)
            except ImportError:
                pass  # croniter not available, skip validation
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")
        return v


class ScheduleUpdateRequest(BaseModel):
    """Request to update a schedule."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None

    # Target
    action_id: Optional[str] = None
    execution_mode: Optional[str] = Field(default=None, pattern="^(run|work_item)$")
    work_item_queue: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None

    # Schedule type and config
    schedule_type: Optional[str] = Field(
        default=None, pattern="^(cron|interval|weekday|once)$"
    )
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = Field(default=None, ge=1)
    weekday_config: Optional[Dict[str, Any]] = None
    once_at: Optional[str] = None

    timezone: Optional[str] = None
    enabled: Optional[bool] = None

    # Execution settings
    skip_if_running: Optional[bool] = None
    max_concurrent: Optional[int] = Field(default=None, ge=1)
    timeout_seconds: Optional[int] = Field(default=None, ge=1)

    # Retry policy
    retry_enabled: Optional[bool] = None
    retry_max_attempts: Optional[int] = Field(default=None, ge=1)
    retry_delay_seconds: Optional[int] = Field(default=None, ge=1)
    retry_backoff_multiplier: Optional[float] = Field(default=None, ge=1.0)

    # Rate limiting
    rate_limit_enabled: Optional[bool] = None
    rate_limit_max_per_hour: Optional[int] = Field(default=None, ge=1)
    rate_limit_max_per_day: Optional[int] = Field(default=None, ge=1)

    # Dependencies
    depends_on_schedule_id: Optional[str] = None
    dependency_mode: Optional[str] = Field(
        default=None, pattern="^(after_success|after_any)$"
    )

    # Notifications
    notify_on_failure: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notification_webhook_url: Optional[str] = None
    notification_email: Optional[str] = None

    # Organization
    group_id: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = Field(default=None, ge=0)


class ScheduleResponse(BaseModel):
    """Response with schedule details."""

    id: str
    name: str
    description: Optional[str] = None

    # Target
    action_id: Optional[str] = None
    action_name: Optional[str] = None
    execution_mode: str
    work_item_queue: Optional[str] = None
    inputs: Dict[str, Any]

    # Schedule type and config
    schedule_type: str
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    weekday_config: Optional[Dict[str, Any]] = None
    once_at: Optional[str] = None

    timezone: str
    enabled: bool

    # Timestamps
    created_at: str
    updated_at: str
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None

    # Execution settings
    skip_if_running: bool
    max_concurrent: int
    timeout_seconds: int

    # Retry policy
    retry_enabled: bool
    retry_max_attempts: int
    retry_delay_seconds: int
    retry_backoff_multiplier: float

    # Rate limiting
    rate_limit_enabled: bool
    rate_limit_max_per_hour: Optional[int] = None
    rate_limit_max_per_day: Optional[int] = None

    # Dependencies
    depends_on_schedule_id: Optional[str] = None
    depends_on_schedule_name: Optional[str] = None
    dependency_mode: str

    # Notifications
    notify_on_failure: bool
    notify_on_success: bool
    notification_webhook_url: Optional[str] = None
    notification_email: Optional[str] = None

    # Organization
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    tags: List[str]
    priority: int


class ScheduleListResponse(BaseModel):
    """Response with list of schedules."""

    schedules: List[ScheduleResponse]
    total: int


class ScheduleStatsResponse(BaseModel):
    """Response with schedule statistics."""

    total: int
    active: int
    paused: int
    running: int
    failed_24h: int
    success_rate_7d: float
    executions_24h: int


class ExecutionResponse(BaseModel):
    """Response for schedule execution."""

    id: str
    schedule_id: str
    run_id: Optional[str] = None
    work_item_id: Optional[str] = None
    scheduled_time: str
    actual_start_time: str
    actual_end_time: Optional[str] = None
    duration_ms: Optional[int] = None
    status: str
    attempt_number: int
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    skip_reason: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    notification_sent: bool
    notification_error: Optional[str] = None


class CronValidateRequest(BaseModel):
    """Request to validate a cron expression."""

    cron_expression: str
    timezone: str = "UTC"


class CronValidateResponse(BaseModel):
    """Response for cron validation."""

    valid: bool
    error: Optional[str] = None
    human_readable: Optional[str] = None
    next_runs: List[str] = Field(default_factory=list)


class PreviewRunsRequest(BaseModel):
    """Request to preview next run times."""

    schedule_type: str
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    weekday_config: Optional[Dict[str, Any]] = None
    once_at: Optional[str] = None
    timezone: str = "UTC"
    count: int = Field(default=10, ge=1, le=100)


class PreviewRunsResponse(BaseModel):
    """Response with next run times."""

    next_runs: List[str]


class GroupCreateRequest(BaseModel):
    """Request to create a schedule group."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None


class GroupUpdateRequest(BaseModel):
    """Request to update a schedule group."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None


class GroupResponse(BaseModel):
    """Response with group details."""

    id: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None
    created_at: str
    schedule_count: int = 0


class GroupListResponse(BaseModel):
    """Response with list of groups."""

    groups: List[GroupResponse]
    total: int


# ============================================================================
# Helper Functions
# ============================================================================


def _schedule_to_response(
    schedule: "Schedule",
    action_name: Optional[str] = None,
    depends_on_name: Optional[str] = None,
    group_name: Optional[str] = None,
) -> ScheduleResponse:
    """Convert a Schedule model to a response."""
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        description=schedule.description,
        action_id=schedule.action_id,
        action_name=action_name,
        execution_mode=schedule.execution_mode,
        work_item_queue=schedule.work_item_queue,
        inputs=json.loads(schedule.inputs_json) if schedule.inputs_json else {},
        schedule_type=schedule.schedule_type,
        cron_expression=schedule.cron_expression,
        interval_seconds=schedule.interval_seconds,
        weekday_config=(
            json.loads(schedule.weekday_config_json)
            if schedule.weekday_config_json
            else None
        ),
        once_at=schedule.once_at,
        timezone=schedule.timezone,
        enabled=schedule.enabled,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        skip_if_running=schedule.skip_if_running,
        max_concurrent=schedule.max_concurrent,
        timeout_seconds=schedule.timeout_seconds,
        retry_enabled=schedule.retry_enabled,
        retry_max_attempts=schedule.retry_max_attempts,
        retry_delay_seconds=schedule.retry_delay_seconds,
        retry_backoff_multiplier=schedule.retry_backoff_multiplier,
        rate_limit_enabled=schedule.rate_limit_enabled,
        rate_limit_max_per_hour=schedule.rate_limit_max_per_hour,
        rate_limit_max_per_day=schedule.rate_limit_max_per_day,
        depends_on_schedule_id=schedule.depends_on_schedule_id,
        depends_on_schedule_name=depends_on_name,
        dependency_mode=schedule.dependency_mode,
        notify_on_failure=schedule.notify_on_failure,
        notify_on_success=schedule.notify_on_success,
        notification_webhook_url=schedule.notification_webhook_url,
        notification_email=schedule.notification_email,
        group_id=schedule.group_id,
        group_name=group_name,
        tags=json.loads(schedule.tags_json) if schedule.tags_json else [],
        priority=schedule.priority,
    )


def _get_related_names(
    db, schedule: "Schedule"
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Get related entity names for a schedule."""
    from sema4ai.action_server._models import Action, Schedule, ScheduleGroup

    action_name = None
    depends_on_name = None
    group_name = None

    if schedule.action_id:
        try:
            action = db.first(
                Action, "SELECT * FROM action WHERE id = ?", [schedule.action_id]
            )
            action_name = action.name
        except KeyError:
            pass

    if schedule.depends_on_schedule_id:
        try:
            depends = db.first(
                Schedule,
                "SELECT * FROM schedule WHERE id = ?",
                [schedule.depends_on_schedule_id],
            )
            depends_on_name = depends.name
        except KeyError:
            pass

    if schedule.group_id:
        try:
            group = db.first(
                ScheduleGroup,
                "SELECT * FROM schedule_group WHERE id = ?",
                [schedule.group_id],
            )
            group_name = group.name
        except KeyError:
            pass

    return action_name, depends_on_name, group_name


# ============================================================================
# Schedule Endpoints
# ============================================================================


@schedules_api_router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    enabled: Optional[bool] = None,
    action_id: Optional[str] = None,
    group_id: Optional[str] = None,
    schedule_type: Optional[str] = None,
):
    """List all schedules with optional filters."""
    from sema4ai.action_server._models import Action, Schedule, ScheduleGroup, get_db

    db = get_db()
    with db.connect():
        # Build query
        conditions = []
        values = []

        if enabled is not None:
            conditions.append("enabled = ?")
            values.append(1 if enabled else 0)

        if action_id:
            conditions.append("action_id = ?")
            values.append(action_id)

        if group_id:
            conditions.append("group_id = ?")
            values.append(group_id)

        if schedule_type:
            conditions.append("schedule_type = ?")
            values.append(schedule_type)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        schedules = db.select(
            Schedule,
            f"SELECT * FROM schedule WHERE {where_clause} ORDER BY priority DESC, created_at DESC",
            values if values else None,
        )

        # Get related names for all schedules
        responses = []
        for schedule in schedules:
            action_name, depends_on_name, group_name = _get_related_names(db, schedule)
            responses.append(
                _schedule_to_response(schedule, action_name, depends_on_name, group_name)
            )

    return ScheduleListResponse(schedules=responses, total=len(responses))


@schedules_api_router.get("/stats", response_model=ScheduleStatsResponse)
async def get_schedule_stats():
    """Get schedule statistics for dashboard."""
    from datetime import timedelta

    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._models import (
        Schedule,
        ScheduleExecution,
        ScheduleExecutionStatus,
        get_db,
    )

    db = get_db()
    now = datetime.now(timezone.utc)
    day_ago = datetime_to_str(now - timedelta(days=1))
    week_ago = datetime_to_str(now - timedelta(days=7))

    with db.connect():
        # Count schedules
        all_schedules = db.all(Schedule)
        total = len(all_schedules)
        active = sum(1 for s in all_schedules if s.enabled)
        paused = total - active

        # Count running (executions with status 'running')
        with db.cursor() as cursor:
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM schedule_execution WHERE status = ?",
                [ScheduleExecutionStatus.RUNNING],
            )
            running = cursor.fetchone()[0]

        # Count failed in last 24h
        with db.cursor() as cursor:
            db.execute_query(
                cursor,
                """
                SELECT COUNT(*) FROM schedule_execution
                WHERE status = ? AND actual_start_time >= ?
                """,
                [ScheduleExecutionStatus.FAILED, day_ago],
            )
            failed_24h = cursor.fetchone()[0]

        # Success rate in last 7 days
        with db.cursor() as cursor:
            db.execute_query(
                cursor,
                """
                SELECT
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as success_count,
                    COUNT(*) as total_count
                FROM schedule_execution
                WHERE actual_start_time >= ?
                  AND status IN (?, ?)
                """,
                [
                    ScheduleExecutionStatus.COMPLETED,
                    week_ago,
                    ScheduleExecutionStatus.COMPLETED,
                    ScheduleExecutionStatus.FAILED,
                ],
            )
            row = cursor.fetchone()
            success_count = row[0] or 0
            total_count = row[1] or 0
            success_rate_7d = (
                (success_count / total_count * 100) if total_count > 0 else 100.0
            )

        # Executions in last 24h
        with db.cursor() as cursor:
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM schedule_execution WHERE actual_start_time >= ?",
                [day_ago],
            )
            executions_24h = cursor.fetchone()[0]

    return ScheduleStatsResponse(
        total=total,
        active=active,
        paused=paused,
        running=running,
        failed_24h=failed_24h,
        success_rate_7d=round(success_rate_7d, 1),
        executions_24h=executions_24h,
    )


@schedules_api_router.post("", response_model=ScheduleResponse)
async def create_schedule(request: ScheduleCreateRequest):
    """Create a new schedule."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._gen_ids import gen_uuid
    from sema4ai.action_server._models import Action, Schedule, ScheduleGroup, get_db
    from sema4ai.action_server._scheduler import get_scheduler

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

        # Verify group exists if specified
        group_name = None
        if request.group_id:
            try:
                group = db.first(
                    ScheduleGroup,
                    "SELECT * FROM schedule_group WHERE id = ?",
                    [request.group_id],
                )
                group_name = group.name
            except KeyError:
                raise HTTPException(
                    status_code=404, detail=f"Group not found: {request.group_id}"
                )

        # Verify dependency exists if specified
        depends_on_name = None
        if request.depends_on_schedule_id:
            try:
                depends = db.first(
                    Schedule,
                    "SELECT * FROM schedule WHERE id = ?",
                    [request.depends_on_schedule_id],
                )
                depends_on_name = depends.name
            except KeyError:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dependency schedule not found: {request.depends_on_schedule_id}",
                )

        schedule_id = gen_uuid("schedule")

        # Create schedule object
        schedule = Schedule(
            id=schedule_id,
            name=request.name,
            description=request.description,
            action_id=request.action_id,
            execution_mode=request.execution_mode,
            work_item_queue=request.work_item_queue,
            inputs_json=json.dumps(request.inputs),
            schedule_type=request.schedule_type,
            cron_expression=request.cron_expression,
            interval_seconds=request.interval_seconds,
            weekday_config_json=(
                json.dumps(request.weekday_config) if request.weekday_config else None
            ),
            once_at=request.once_at,
            timezone=request.timezone,
            enabled=request.enabled,
            created_at=datetime_to_str(now),
            updated_at=datetime_to_str(now),
            skip_if_running=request.skip_if_running,
            max_concurrent=request.max_concurrent,
            timeout_seconds=request.timeout_seconds,
            retry_enabled=request.retry_enabled,
            retry_max_attempts=request.retry_max_attempts,
            retry_delay_seconds=request.retry_delay_seconds,
            retry_backoff_multiplier=request.retry_backoff_multiplier,
            rate_limit_enabled=request.rate_limit_enabled,
            rate_limit_max_per_hour=request.rate_limit_max_per_hour,
            rate_limit_max_per_day=request.rate_limit_max_per_day,
            depends_on_schedule_id=request.depends_on_schedule_id,
            dependency_mode=request.dependency_mode,
            notify_on_failure=request.notify_on_failure,
            notify_on_success=request.notify_on_success,
            notification_webhook_url=request.notification_webhook_url,
            notification_email=request.notification_email,
            group_id=request.group_id,
            tags_json=json.dumps(request.tags),
            priority=request.priority,
        )

        # Compute next run if enabled
        if request.enabled:
            scheduler = get_scheduler()
            if scheduler:
                next_run = scheduler.compute_next_run(schedule, now)
                if next_run:
                    schedule.next_run_at = datetime_to_str(next_run)

        with db.transaction():
            db.insert(schedule)

    log.info(f"Created schedule {schedule_id}: {request.name}")

    return _schedule_to_response(schedule, action_name, depends_on_name, group_name)


@schedules_api_router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get a specific schedule by ID."""
    from sema4ai.action_server._models import Schedule, get_db

    db = get_db()
    with db.connect():
        try:
            schedule = db.first(
                Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        action_name, depends_on_name, group_name = _get_related_names(db, schedule)

    return _schedule_to_response(schedule, action_name, depends_on_name, group_name)


@schedules_api_router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: str, request: ScheduleUpdateRequest):
    """Update an existing schedule."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._models import Action, Schedule, ScheduleGroup, get_db
    from sema4ai.action_server._scheduler import get_scheduler

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        # Get existing schedule
        try:
            schedule = db.first(
                Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        # Build update dict
        updates = {"updated_at": datetime_to_str(now)}

        # Handle each field
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.action_id is not None:
            # Verify action exists
            try:
                db.first(Action, "SELECT * FROM action WHERE id = ?", [request.action_id])
            except KeyError:
                raise HTTPException(
                    status_code=404, detail=f"Action not found: {request.action_id}"
                )
            updates["action_id"] = request.action_id
        if request.execution_mode is not None:
            updates["execution_mode"] = request.execution_mode
        if request.work_item_queue is not None:
            updates["work_item_queue"] = request.work_item_queue
        if request.inputs is not None:
            updates["inputs_json"] = json.dumps(request.inputs)
        if request.schedule_type is not None:
            updates["schedule_type"] = request.schedule_type
        if request.cron_expression is not None:
            updates["cron_expression"] = request.cron_expression
        if request.interval_seconds is not None:
            updates["interval_seconds"] = request.interval_seconds
        if request.weekday_config is not None:
            updates["weekday_config_json"] = json.dumps(request.weekday_config)
        if request.once_at is not None:
            updates["once_at"] = request.once_at
        if request.timezone is not None:
            updates["timezone"] = request.timezone
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        if request.skip_if_running is not None:
            updates["skip_if_running"] = request.skip_if_running
        if request.max_concurrent is not None:
            updates["max_concurrent"] = request.max_concurrent
        if request.timeout_seconds is not None:
            updates["timeout_seconds"] = request.timeout_seconds
        if request.retry_enabled is not None:
            updates["retry_enabled"] = request.retry_enabled
        if request.retry_max_attempts is not None:
            updates["retry_max_attempts"] = request.retry_max_attempts
        if request.retry_delay_seconds is not None:
            updates["retry_delay_seconds"] = request.retry_delay_seconds
        if request.retry_backoff_multiplier is not None:
            updates["retry_backoff_multiplier"] = request.retry_backoff_multiplier
        if request.rate_limit_enabled is not None:
            updates["rate_limit_enabled"] = request.rate_limit_enabled
        if request.rate_limit_max_per_hour is not None:
            updates["rate_limit_max_per_hour"] = request.rate_limit_max_per_hour
        if request.rate_limit_max_per_day is not None:
            updates["rate_limit_max_per_day"] = request.rate_limit_max_per_day
        if request.depends_on_schedule_id is not None:
            if request.depends_on_schedule_id:
                try:
                    db.first(
                        Schedule,
                        "SELECT * FROM schedule WHERE id = ?",
                        [request.depends_on_schedule_id],
                    )
                except KeyError:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Dependency schedule not found: {request.depends_on_schedule_id}",
                    )
            updates["depends_on_schedule_id"] = request.depends_on_schedule_id or None
        if request.dependency_mode is not None:
            updates["dependency_mode"] = request.dependency_mode
        if request.notify_on_failure is not None:
            updates["notify_on_failure"] = request.notify_on_failure
        if request.notify_on_success is not None:
            updates["notify_on_success"] = request.notify_on_success
        if request.notification_webhook_url is not None:
            updates["notification_webhook_url"] = request.notification_webhook_url
        if request.notification_email is not None:
            updates["notification_email"] = request.notification_email
        if request.group_id is not None:
            if request.group_id:
                try:
                    db.first(
                        ScheduleGroup,
                        "SELECT * FROM schedule_group WHERE id = ?",
                        [request.group_id],
                    )
                except KeyError:
                    raise HTTPException(
                        status_code=404, detail=f"Group not found: {request.group_id}"
                    )
            updates["group_id"] = request.group_id or None
        if request.tags is not None:
            updates["tags_json"] = json.dumps(request.tags)
        if request.priority is not None:
            updates["priority"] = request.priority

        # Recompute next_run_at if schedule config changed
        schedule_changed = any(
            k
            in (
                "schedule_type",
                "cron_expression",
                "interval_seconds",
                "weekday_config_json",
                "once_at",
                "timezone",
                "enabled",
            )
            for k in updates.keys()
        )

        with db.transaction():
            db.update_by_id(Schedule, schedule_id, updates)

        # Refresh schedule
        schedule = db.first(
            Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id]
        )

        # Recompute next run if needed
        if schedule_changed and schedule.enabled:
            scheduler = get_scheduler()
            if scheduler:
                next_run = scheduler.compute_next_run(schedule, now)
                with db.transaction():
                    db.update_by_id(
                        Schedule,
                        schedule_id,
                        {"next_run_at": datetime_to_str(next_run) if next_run else None},
                    )
                schedule = db.first(
                    Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id]
                )

        action_name, depends_on_name, group_name = _get_related_names(db, schedule)

    log.info(f"Updated schedule {schedule_id}")

    return _schedule_to_response(schedule, action_name, depends_on_name, group_name)


@schedules_api_router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a schedule."""
    from sema4ai.action_server._models import Schedule, ScheduleExecution, get_db

    db = get_db()
    with db.connect():
        try:
            db.first(Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id])
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        with db.transaction():
            # Delete executions first (foreign key constraint)
            db.execute(
                "DELETE FROM schedule_execution WHERE schedule_id = ?", [schedule_id]
            )
            db.execute("DELETE FROM schedule WHERE id = ?", [schedule_id])

    log.info(f"Deleted schedule {schedule_id}")

    return {"status": "deleted", "id": schedule_id}


@schedules_api_router.post("/{schedule_id}/trigger", response_model=ExecutionResponse)
async def trigger_schedule(schedule_id: str):
    """Manually trigger a schedule execution."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._gen_ids import gen_uuid
    from sema4ai.action_server._models import (
        Schedule,
        ScheduleExecution,
        ScheduleExecutionStatus,
        get_db,
    )
    from sema4ai.action_server._scheduler import get_scheduler

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        try:
            schedule = db.first(
                Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

    scheduler = get_scheduler()
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    # Create and execute
    execution_id = gen_uuid("schedule_execution")
    await scheduler._execute_schedule(schedule, execution_id, now)

    # Get the execution record
    with db.connect():
        execution = db.first(
            ScheduleExecution,
            "SELECT * FROM schedule_execution WHERE id = ?",
            [execution_id],
        )

    return ExecutionResponse(
        id=execution.id,
        schedule_id=execution.schedule_id,
        run_id=execution.run_id,
        work_item_id=execution.work_item_id,
        scheduled_time=execution.scheduled_time,
        actual_start_time=execution.actual_start_time,
        actual_end_time=execution.actual_end_time,
        duration_ms=execution.duration_ms,
        status=execution.status,
        attempt_number=execution.attempt_number,
        error_message=execution.error_message,
        error_code=execution.error_code,
        skip_reason=execution.skip_reason,
        result=json.loads(execution.result_json) if execution.result_json else None,
        notification_sent=execution.notification_sent,
        notification_error=execution.notification_error,
    )


@schedules_api_router.post("/{schedule_id}/enable")
async def enable_schedule(schedule_id: str):
    """Enable a schedule."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._models import Schedule, get_db
    from sema4ai.action_server._scheduler import get_scheduler

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        try:
            schedule = db.first(
                Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        updates = {"enabled": True, "updated_at": datetime_to_str(now)}

        # Compute next run
        scheduler = get_scheduler()
        if scheduler:
            # Apply updates temporarily to compute next run
            schedule.enabled = True
            next_run = scheduler.compute_next_run(schedule, now)
            if next_run:
                updates["next_run_at"] = datetime_to_str(next_run)

        with db.transaction():
            db.update_by_id(Schedule, schedule_id, updates)

    return {"status": "enabled", "id": schedule_id}


@schedules_api_router.post("/{schedule_id}/disable")
async def disable_schedule(schedule_id: str):
    """Disable a schedule."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._models import Schedule, get_db

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        try:
            db.first(Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id])
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        with db.transaction():
            db.update_by_id(
                Schedule,
                schedule_id,
                {
                    "enabled": False,
                    "next_run_at": None,
                    "updated_at": datetime_to_str(now),
                },
            )

    return {"status": "disabled", "id": schedule_id}


@schedules_api_router.post("/{schedule_id}/duplicate", response_model=ScheduleResponse)
async def duplicate_schedule(schedule_id: str, new_name: Optional[str] = None):
    """Duplicate/clone a schedule."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._gen_ids import gen_uuid
    from sema4ai.action_server._models import Schedule, get_db

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        try:
            source = db.first(
                Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id]
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        new_id = gen_uuid("schedule")
        name = new_name or f"{source.name} (Copy)"

        # Create copy
        new_schedule = Schedule(
            id=new_id,
            name=name,
            description=source.description,
            action_id=source.action_id,
            execution_mode=source.execution_mode,
            work_item_queue=source.work_item_queue,
            inputs_json=source.inputs_json,
            schedule_type=source.schedule_type,
            cron_expression=source.cron_expression,
            interval_seconds=source.interval_seconds,
            weekday_config_json=source.weekday_config_json,
            once_at=source.once_at,
            timezone=source.timezone,
            enabled=False,  # Start disabled
            created_at=datetime_to_str(now),
            updated_at=datetime_to_str(now),
            skip_if_running=source.skip_if_running,
            max_concurrent=source.max_concurrent,
            timeout_seconds=source.timeout_seconds,
            retry_enabled=source.retry_enabled,
            retry_max_attempts=source.retry_max_attempts,
            retry_delay_seconds=source.retry_delay_seconds,
            retry_backoff_multiplier=source.retry_backoff_multiplier,
            rate_limit_enabled=source.rate_limit_enabled,
            rate_limit_max_per_hour=source.rate_limit_max_per_hour,
            rate_limit_max_per_day=source.rate_limit_max_per_day,
            depends_on_schedule_id=source.depends_on_schedule_id,
            dependency_mode=source.dependency_mode,
            notify_on_failure=source.notify_on_failure,
            notify_on_success=source.notify_on_success,
            notification_webhook_url=source.notification_webhook_url,
            notification_email=source.notification_email,
            group_id=source.group_id,
            tags_json=source.tags_json,
            priority=source.priority,
        )

        with db.transaction():
            db.insert(new_schedule)

        action_name, depends_on_name, group_name = _get_related_names(db, new_schedule)

    log.info(f"Duplicated schedule {schedule_id} as {new_id}")

    return _schedule_to_response(
        new_schedule, action_name, depends_on_name, group_name
    )


@schedules_api_router.get(
    "/{schedule_id}/executions", response_model=List[ExecutionResponse]
)
async def list_executions(schedule_id: str, limit: int = 50, offset: int = 0):
    """Get execution history for a schedule."""
    from sema4ai.action_server._models import Schedule, ScheduleExecution, get_db

    db = get_db()
    with db.connect():
        # Verify schedule exists
        try:
            db.first(Schedule, "SELECT * FROM schedule WHERE id = ?", [schedule_id])
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Schedule not found: {schedule_id}"
            )

        executions = db.select(
            ScheduleExecution,
            """
            SELECT * FROM schedule_execution
            WHERE schedule_id = ?
            ORDER BY actual_start_time DESC
            LIMIT ? OFFSET ?
            """,
            [schedule_id, limit, offset],
        )

    return [
        ExecutionResponse(
            id=e.id,
            schedule_id=e.schedule_id,
            run_id=e.run_id,
            work_item_id=e.work_item_id,
            scheduled_time=e.scheduled_time,
            actual_start_time=e.actual_start_time,
            actual_end_time=e.actual_end_time,
            duration_ms=e.duration_ms,
            status=e.status,
            attempt_number=e.attempt_number,
            error_message=e.error_message,
            error_code=e.error_code,
            skip_reason=e.skip_reason,
            result=json.loads(e.result_json) if e.result_json else None,
            notification_sent=e.notification_sent,
            notification_error=e.notification_error,
        )
        for e in executions
    ]


# ============================================================================
# Utility Endpoints
# ============================================================================


@schedules_api_router.post("/validate-cron", response_model=CronValidateResponse)
async def validate_cron(request: CronValidateRequest):
    """Validate a cron expression and show next runs."""
    try:
        from croniter import croniter

        # Validate expression
        croniter(request.cron_expression)
    except ImportError:
        return CronValidateResponse(
            valid=True,
            error="croniter not installed - validation skipped",
            human_readable=None,
            next_runs=[],
        )
    except Exception as e:
        return CronValidateResponse(
            valid=False,
            error=str(e),
            human_readable=None,
            next_runs=[],
        )

    # Get human readable description
    human_readable = None
    try:
        import cronstrue

        human_readable = cronstrue.get_description(request.cron_expression)
    except ImportError:
        pass
    except Exception:
        pass

    # Get next runs
    from sema4ai.action_server._scheduler import SchedulerEngine

    scheduler = SchedulerEngine()
    next_runs = []

    try:
        import pytz

        tz = pytz.timezone(request.timezone)
    except ImportError:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(request.timezone)

    base = datetime.now(timezone.utc)
    for _ in range(10):
        next_run = scheduler._compute_cron_next(
            request.cron_expression, request.timezone, base
        )
        next_runs.append(next_run.isoformat())
        base = next_run

    return CronValidateResponse(
        valid=True,
        error=None,
        human_readable=human_readable,
        next_runs=next_runs,
    )


@schedules_api_router.post("/preview-runs", response_model=PreviewRunsResponse)
async def preview_runs(request: PreviewRunsRequest):
    """Preview next run times for a schedule configuration."""
    from sema4ai.action_server._models import Schedule
    from sema4ai.action_server._scheduler import SchedulerEngine

    # Create a temporary schedule object
    schedule = Schedule(
        id="preview",
        name="preview",
        description=None,
        action_id=None,
        execution_mode="run",
        work_item_queue=None,
        inputs_json="{}",
        schedule_type=request.schedule_type,
        cron_expression=request.cron_expression,
        interval_seconds=request.interval_seconds,
        weekday_config_json=(
            json.dumps(request.weekday_config) if request.weekday_config else None
        ),
        once_at=request.once_at,
        timezone=request.timezone,
    )

    scheduler = SchedulerEngine()
    next_runs = []
    base = datetime.now(timezone.utc)

    for _ in range(request.count):
        next_run = scheduler.compute_next_run(schedule, base)
        if next_run is None:
            break
        next_runs.append(next_run.isoformat())
        base = next_run

    return PreviewRunsResponse(next_runs=next_runs)


@schedules_api_router.get("/timezones")
async def list_timezones():
    """List available timezones."""
    try:
        import pytz

        common_timezones = pytz.common_timezones
    except ImportError:
        try:
            from zoneinfo import available_timezones

            common_timezones = sorted(available_timezones())
        except ImportError:
            common_timezones = ["UTC"]

    return {"timezones": common_timezones}


# ============================================================================
# Schedule Group Endpoints
# ============================================================================


@schedule_groups_api_router.get("", response_model=GroupListResponse)
async def list_groups():
    """List all schedule groups."""
    from sema4ai.action_server._models import Schedule, ScheduleGroup, get_db

    db = get_db()
    with db.connect():
        groups = db.all(ScheduleGroup, order_by="name")

        # Count schedules per group
        responses = []
        for group in groups:
            with db.cursor() as cursor:
                db.execute_query(
                    cursor,
                    "SELECT COUNT(*) FROM schedule WHERE group_id = ?",
                    [group.id],
                )
                count = cursor.fetchone()[0]

            responses.append(
                GroupResponse(
                    id=group.id,
                    name=group.name,
                    description=group.description,
                    parent_id=group.parent_id,
                    color=group.color,
                    created_at=group.created_at,
                    schedule_count=count,
                )
            )

    return GroupListResponse(groups=responses, total=len(responses))


@schedule_groups_api_router.post("", response_model=GroupResponse)
async def create_group(request: GroupCreateRequest):
    """Create a new schedule group."""
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._gen_ids import gen_uuid
    from sema4ai.action_server._models import ScheduleGroup, get_db

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        # Verify parent exists if specified
        if request.parent_id:
            try:
                db.first(
                    ScheduleGroup,
                    "SELECT * FROM schedule_group WHERE id = ?",
                    [request.parent_id],
                )
            except KeyError:
                raise HTTPException(
                    status_code=404, detail=f"Parent group not found: {request.parent_id}"
                )

        group_id = gen_uuid("schedule_group")

        group = ScheduleGroup(
            id=group_id,
            name=request.name,
            description=request.description,
            parent_id=request.parent_id,
            color=request.color,
            created_at=datetime_to_str(now),
        )

        with db.transaction():
            db.insert(group)

    log.info(f"Created schedule group {group_id}: {request.name}")

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        parent_id=group.parent_id,
        color=group.color,
        created_at=group.created_at,
        schedule_count=0,
    )


@schedule_groups_api_router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: str, request: GroupUpdateRequest):
    """Update a schedule group."""
    from sema4ai.action_server._models import ScheduleGroup, get_db

    db = get_db()

    with db.connect():
        try:
            group = db.first(
                ScheduleGroup,
                "SELECT * FROM schedule_group WHERE id = ?",
                [group_id],
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Group not found: {group_id}"
            )

        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.parent_id is not None:
            if request.parent_id:
                try:
                    db.first(
                        ScheduleGroup,
                        "SELECT * FROM schedule_group WHERE id = ?",
                        [request.parent_id],
                    )
                except KeyError:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Parent group not found: {request.parent_id}",
                    )
            updates["parent_id"] = request.parent_id or None
        if request.color is not None:
            updates["color"] = request.color

        if updates:
            with db.transaction():
                db.update_by_id(ScheduleGroup, group_id, updates)

        # Refresh
        group = db.first(
            ScheduleGroup,
            "SELECT * FROM schedule_group WHERE id = ?",
            [group_id],
        )

        # Count schedules
        with db.cursor() as cursor:
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM schedule WHERE group_id = ?",
                [group_id],
            )
            count = cursor.fetchone()[0]

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        parent_id=group.parent_id,
        color=group.color,
        created_at=group.created_at,
        schedule_count=count,
    )


@schedule_groups_api_router.delete("/{group_id}")
async def delete_group(group_id: str):
    """Delete a schedule group."""
    from sema4ai.action_server._models import Schedule, ScheduleGroup, get_db

    db = get_db()
    with db.connect():
        try:
            db.first(
                ScheduleGroup,
                "SELECT * FROM schedule_group WHERE id = ?",
                [group_id],
            )
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Group not found: {group_id}"
            )

        # Check if group has schedules
        with db.cursor() as cursor:
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM schedule WHERE group_id = ?",
                [group_id],
            )
            count = cursor.fetchone()[0]

        if count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete group with {count} schedules. Move or delete them first.",
            )

        # Check if group has children
        with db.cursor() as cursor:
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM schedule_group WHERE parent_id = ?",
                [group_id],
            )
            child_count = cursor.fetchone()[0]

        if child_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete group with {child_count} child groups.",
            )

        with db.transaction():
            db.execute("DELETE FROM schedule_group WHERE id = ?", [group_id])

    log.info(f"Deleted schedule group {group_id}")

    return {"status": "deleted", "id": group_id}
