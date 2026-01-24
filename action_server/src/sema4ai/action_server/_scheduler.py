"""
Scheduler engine for the Action Server.

This module provides a full-featured embedded scheduler supporting:
- Cron expressions
- Fixed intervals
- Weekday-based schedules
- One-time schedules
- Dependency resolution between schedules
- Retry with exponential backoff
- Rate limiting (hourly/daily)
- Concurrent execution control
- Notifications (webhook/email)
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Set

log = logging.getLogger(__name__)


def _get_croniter():
    """Lazy import croniter to avoid import errors if not installed."""
    try:
        from croniter import croniter
        return croniter
    except ImportError:
        raise ImportError(
            "croniter package is required for cron scheduling. "
            "Install with: pip install croniter"
        )


def _get_pytz():
    """Lazy import pytz for timezone handling."""
    try:
        import pytz
        return pytz
    except ImportError:
        # Fall back to zoneinfo from stdlib (Python 3.9+)
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo
        except ImportError:
            raise ImportError(
                "Either pytz or Python 3.9+ zoneinfo is required for timezone support."
            )


class ScheduleType:
    """Schedule type constants."""
    CRON = "cron"
    INTERVAL = "interval"
    WEEKDAY = "weekday"
    ONCE = "once"


class SchedulerEngine:
    """
    Full-featured embedded scheduler.

    Supports:
    - Cron, interval, weekday, and one-time schedules
    - Dependency resolution
    - Retry with exponential backoff
    - Rate limiting
    - Concurrent execution control
    """

    def __init__(
        self,
        check_interval: float = 10.0,
        max_concurrent_global: int = 10,
    ):
        """
        Initialize the scheduler engine.

        Args:
            check_interval: How often to check for due schedules (seconds)
            max_concurrent_global: Maximum concurrent executions across all schedules
        """
        self._check_interval = check_interval
        self._max_concurrent_global = max_concurrent_global
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Track running executions per schedule
        self._running_executions: Dict[str, Set[str]] = defaultdict(set)
        self._global_running_count = 0

        # Rate limit tracker: schedule_id -> list of execution timestamps
        self._rate_limit_tracker: Dict[str, List[datetime]] = defaultdict(list)

        # Notification callbacks
        self._on_execution_complete: List[Callable] = []

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            log.warning("Scheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        log.info(
            f"Scheduler engine started (check_interval={self._check_interval}s, "
            f"max_concurrent={self._max_concurrent_global})"
        )

    async def stop(self) -> None:
        """Stop the scheduler loop gracefully."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        log.info("Scheduler engine stopped")

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_execute_schedules()
            except asyncio.CancelledError:
                break
            except Exception:
                log.exception("Error in scheduler loop")

            await asyncio.sleep(self._check_interval)

    async def _check_and_execute_schedules(self) -> None:
        """Check for due schedules and execute them."""
        from sema4ai.action_server._database import datetime_to_str
        from sema4ai.action_server._models import Schedule, get_db

        now = datetime.now(timezone.utc)
        now_str = datetime_to_str(now)

        db = get_db()
        with db.connect():
            # Find all enabled schedules where next_run_at <= now
            schedules = db.select(
                Schedule,
                """
                SELECT * FROM schedule
                WHERE enabled = 1
                  AND next_run_at IS NOT NULL
                  AND next_run_at <= ?
                ORDER BY priority DESC, next_run_at ASC
                """,
                [now_str],
            )

        for schedule in schedules:
            try:
                await self._process_schedule(schedule, now)
            except Exception:
                log.exception(f"Error processing schedule {schedule.id} ({schedule.name})")

    async def _process_schedule(
        self, schedule: "Schedule", now: datetime
    ) -> None:
        """
        Process a single schedule - check constraints and execute if allowed.

        Args:
            schedule: The schedule to process
            now: Current time
        """
        from sema4ai.action_server._models import (
            ScheduleExecution,
            ScheduleExecutionStatus,
            ScheduleSkipReason,
            get_db,
        )

        # Import here to avoid circular imports
        from sema4ai.action_server._database import datetime_to_str
        from sema4ai.action_server._gen_ids import gen_uuid

        schedule_id = schedule.id

        # Check global concurrent limit
        if self._global_running_count >= self._max_concurrent_global:
            log.debug(f"Schedule {schedule_id}: skipped - global limit reached")
            return

        # Check concurrent execution limit for this schedule
        if not await self._check_concurrent_limit(schedule):
            await self._record_skip(
                schedule, now, ScheduleSkipReason.PREVIOUS_RUNNING
            )
            return

        # Check rate limits
        if not await self._check_rate_limit(schedule, now):
            await self._record_skip(
                schedule, now, ScheduleSkipReason.RATE_LIMITED
            )
            return

        # Check dependencies
        if not await self._check_dependencies(schedule):
            await self._record_skip(
                schedule, now, ScheduleSkipReason.DEPENDENCY_FAILED
            )
            return

        # All checks passed - execute the schedule
        execution_id = gen_uuid("schedule_execution")
        await self._execute_schedule(schedule, execution_id, now)

    async def _check_concurrent_limit(self, schedule: "Schedule") -> bool:
        """Check if the schedule's concurrent execution limit allows execution."""
        async with self._lock:
            current_count = len(self._running_executions.get(schedule.id, set()))
            if current_count >= schedule.max_concurrent:
                if schedule.skip_if_running:
                    log.debug(
                        f"Schedule {schedule.id}: concurrent limit reached "
                        f"({current_count}/{schedule.max_concurrent})"
                    )
                    return False
            return True

    async def _check_rate_limit(
        self, schedule: "Schedule", now: datetime
    ) -> bool:
        """Check if the schedule's rate limits allow execution."""
        if not schedule.rate_limit_enabled:
            return True

        # Clean up old entries
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        timestamps = self._rate_limit_tracker[schedule.id]
        self._rate_limit_tracker[schedule.id] = [
            ts for ts in timestamps if ts > day_ago
        ]
        timestamps = self._rate_limit_tracker[schedule.id]

        # Check hourly limit
        if schedule.rate_limit_max_per_hour:
            hourly_count = sum(1 for ts in timestamps if ts > hour_ago)
            if hourly_count >= schedule.rate_limit_max_per_hour:
                log.debug(
                    f"Schedule {schedule.id}: hourly rate limit reached "
                    f"({hourly_count}/{schedule.rate_limit_max_per_hour})"
                )
                return False

        # Check daily limit
        if schedule.rate_limit_max_per_day:
            daily_count = len(timestamps)
            if daily_count >= schedule.rate_limit_max_per_day:
                log.debug(
                    f"Schedule {schedule.id}: daily rate limit reached "
                    f"({daily_count}/{schedule.rate_limit_max_per_day})"
                )
                return False

        return True

    async def _check_dependencies(self, schedule: "Schedule") -> bool:
        """Check if the schedule's dependency requirements are met."""
        if not schedule.depends_on_schedule_id:
            return True

        from sema4ai.action_server._models import (
            ScheduleExecution,
            ScheduleExecutionStatus,
            get_db,
        )

        db = get_db()
        with db.connect():
            # Get the most recent execution of the dependency
            executions = db.select(
                ScheduleExecution,
                """
                SELECT * FROM schedule_execution
                WHERE schedule_id = ?
                ORDER BY actual_start_time DESC
                LIMIT 1
                """,
                [schedule.depends_on_schedule_id],
            )

        if not executions:
            log.debug(
                f"Schedule {schedule.id}: dependency {schedule.depends_on_schedule_id} "
                "has no executions yet"
            )
            return False

        last_execution = executions[0]

        if schedule.dependency_mode == "after_success":
            if last_execution.status != ScheduleExecutionStatus.COMPLETED:
                log.debug(
                    f"Schedule {schedule.id}: dependency not completed "
                    f"(status={last_execution.status})"
                )
                return False
        elif schedule.dependency_mode == "after_any":
            # Any completion status is fine
            if last_execution.status not in (
                ScheduleExecutionStatus.COMPLETED,
                ScheduleExecutionStatus.FAILED,
            ):
                log.debug(
                    f"Schedule {schedule.id}: dependency still running "
                    f"(status={last_execution.status})"
                )
                return False

        return True

    async def _record_skip(
        self,
        schedule: "Schedule",
        now: datetime,
        reason: str,
    ) -> None:
        """Record a skipped execution."""
        from sema4ai.action_server._database import datetime_to_str
        from sema4ai.action_server._gen_ids import gen_uuid
        from sema4ai.action_server._models import (
            ScheduleExecution,
            ScheduleExecutionStatus,
            get_db,
        )

        execution_id = gen_uuid("schedule_execution")
        db = get_db()

        with db.connect():
            with db.transaction():
                execution = ScheduleExecution(
                    id=execution_id,
                    schedule_id=schedule.id,
                    run_id=None,
                    work_item_id=None,
                    scheduled_time=schedule.next_run_at or datetime_to_str(now),
                    actual_start_time=datetime_to_str(now),
                    actual_end_time=datetime_to_str(now),
                    duration_ms=0,
                    status=ScheduleExecutionStatus.SKIPPED,
                    skip_reason=reason,
                )
                db.insert(execution)

                # Update next_run_at even when skipped
                next_run = self.compute_next_run(schedule, now)
                if next_run:
                    db.update_by_id(
                        type(schedule),
                        schedule.id,
                        {
                            "next_run_at": datetime_to_str(next_run),
                            "updated_at": datetime_to_str(now),
                        },
                    )

        log.info(
            f"Schedule {schedule.id} ({schedule.name}) skipped: {reason}"
        )

    async def _execute_schedule(
        self,
        schedule: "Schedule",
        execution_id: str,
        now: datetime,
    ) -> None:
        """Execute a schedule with retry support."""
        from sema4ai.action_server._database import datetime_to_str
        from sema4ai.action_server._models import (
            Schedule,
            ScheduleExecution,
            ScheduleExecutionStatus,
            get_db,
        )

        # Track this execution
        async with self._lock:
            self._running_executions[schedule.id].add(execution_id)
            self._global_running_count += 1
            self._rate_limit_tracker[schedule.id].append(now)

        db = get_db()

        try:
            # Create initial execution record
            with db.connect():
                with db.transaction():
                    execution = ScheduleExecution(
                        id=execution_id,
                        schedule_id=schedule.id,
                        run_id=None,
                        work_item_id=None,
                        scheduled_time=schedule.next_run_at or datetime_to_str(now),
                        actual_start_time=datetime_to_str(now),
                        actual_end_time=None,
                        duration_ms=None,
                        status=ScheduleExecutionStatus.RUNNING,
                        attempt_number=1,
                    )
                    db.insert(execution)

            # Execute with retry logic
            success, result, error = await self._execute_with_retry(
                schedule, execution_id, now
            )

            # Update execution record
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - now).total_seconds() * 1000)

            with db.connect():
                with db.transaction():
                    update_fields = {
                        "actual_end_time": datetime_to_str(end_time),
                        "duration_ms": duration_ms,
                        "status": (
                            ScheduleExecutionStatus.COMPLETED
                            if success
                            else ScheduleExecutionStatus.FAILED
                        ),
                    }

                    if result is not None:
                        update_fields["result_json"] = json.dumps(result)
                    if error:
                        update_fields["error_message"] = str(error)

                    db.update_by_id(ScheduleExecution, execution_id, update_fields)

                    # Update schedule timestamps
                    next_run = self.compute_next_run(schedule, end_time)
                    schedule_updates = {
                        "last_run_at": datetime_to_str(now),
                        "updated_at": datetime_to_str(end_time),
                    }
                    if next_run:
                        schedule_updates["next_run_at"] = datetime_to_str(next_run)
                    else:
                        # One-time schedule or no more runs
                        schedule_updates["next_run_at"] = None
                        if schedule.schedule_type == ScheduleType.ONCE:
                            schedule_updates["enabled"] = False

                    db.update_by_id(Schedule, schedule.id, schedule_updates)

            # Send notifications
            await self._send_notifications(schedule, execution, success, error)

            log.info(
                f"Schedule {schedule.id} ({schedule.name}) "
                f"{'completed' if success else 'failed'} "
                f"(duration={duration_ms}ms)"
            )

        finally:
            # Clean up tracking
            async with self._lock:
                self._running_executions[schedule.id].discard(execution_id)
                self._global_running_count -= 1

    async def _execute_with_retry(
        self,
        schedule: "Schedule",
        execution_id: str,
        start_time: datetime,
    ) -> tuple[bool, Optional[Any], Optional[str]]:
        """
        Execute the schedule action with retry logic.

        Returns:
            Tuple of (success, result, error_message)
        """
        from sema4ai.action_server._database import datetime_to_str
        from sema4ai.action_server._models import (
            ScheduleExecution,
            ScheduleExecutionStatus,
            get_db,
        )

        max_attempts = 1
        if schedule.retry_enabled:
            max_attempts = schedule.retry_max_attempts

        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                # Update attempt number
                if attempt > 1:
                    db = get_db()
                    with db.connect():
                        with db.transaction():
                            db.update_by_id(
                                ScheduleExecution,
                                execution_id,
                                {
                                    "attempt_number": attempt,
                                    "status": ScheduleExecutionStatus.RETRYING,
                                },
                            )

                # Execute the action
                result = await self._trigger_action(schedule)
                return True, result, None

            except Exception as e:
                last_error = str(e)
                log.warning(
                    f"Schedule {schedule.id} attempt {attempt}/{max_attempts} failed: {e}"
                )

                if attempt < max_attempts and schedule.retry_enabled:
                    # Calculate delay with exponential backoff
                    delay = schedule.retry_delay_seconds * (
                        schedule.retry_backoff_multiplier ** (attempt - 1)
                    )
                    log.info(f"Retrying schedule {schedule.id} in {delay}s...")
                    await asyncio.sleep(delay)

        return False, None, last_error

    async def _trigger_action(self, schedule: "Schedule") -> Optional[Any]:
        """
        Trigger the action for a schedule.

        Returns the result of the action execution.
        """
        if schedule.execution_mode == "run":
            return await self._create_action_run(schedule)
        elif schedule.execution_mode == "work_item":
            return await self._create_work_item(schedule)
        else:
            raise ValueError(f"Unknown execution mode: {schedule.execution_mode}")

    async def _create_action_run(self, schedule: "Schedule") -> Optional[str]:
        """
        Create an action run for a schedule.

        Returns the run ID.
        """
        from sema4ai.action_server._actions_run import (
            _create_run,
            _create_run_artifacts_dir,
        )
        from sema4ai.action_server._gen_ids import gen_uuid
        from sema4ai.action_server._models import Action, get_db

        if not schedule.action_id:
            raise ValueError("Schedule has no action_id configured")

        db = get_db()
        with db.connect():
            try:
                action = db.first(
                    Action,
                    "SELECT * FROM action WHERE id = ?",
                    [schedule.action_id],
                )
            except KeyError:
                raise ValueError(f"Action not found: {schedule.action_id}")

            if not action.enabled:
                raise ValueError(f"Action {action.id} is disabled")

        # Parse inputs
        inputs = json.loads(schedule.inputs_json) if schedule.inputs_json else {}

        # Create the run
        run_id = gen_uuid("run")
        relative_artifacts_dir = _create_run_artifacts_dir(action, run_id)

        with db.connect():
            run = _create_run(
                action=action,
                run_id=run_id,
                inputs=inputs,
                relative_artifacts_dir=relative_artifacts_dir,
                request_id=f"schedule:{schedule.id}",
            )

        log.info(
            f"Schedule {schedule.id}: created run {run_id} for action {action.name}"
        )

        # Note: The actual action execution happens asynchronously through the
        # action server's normal execution pipeline. We just create the run here.
        # For synchronous execution, we'd need to wait for the run to complete.

        return run_id

    async def _create_work_item(self, schedule: "Schedule") -> Optional[str]:
        """
        Create a work item for a schedule.

        Returns the work item ID.
        """
        # Work item creation depends on the actions-work-items package
        # This is a placeholder - actual implementation would use the work items API
        log.warning(
            f"Schedule {schedule.id}: work_item mode not yet fully implemented"
        )

        inputs = json.loads(schedule.inputs_json) if schedule.inputs_json else {}
        queue_name = schedule.work_item_queue or "default"

        # Add schedule metadata
        inputs["_schedule_id"] = schedule.id
        inputs["_schedule_name"] = schedule.name

        # TODO: Integrate with work items adapter when available
        # adapter = _get_work_items_adapter()
        # if adapter:
        #     return adapter.seed_input(payload=inputs, queue_name=queue_name)

        return None

    async def _send_notifications(
        self,
        schedule: "Schedule",
        execution: "ScheduleExecution",
        success: bool,
        error: Optional[str],
    ) -> None:
        """Send notifications based on schedule configuration."""
        should_notify = (
            (success and schedule.notify_on_success)
            or (not success and schedule.notify_on_failure)
        )

        if not should_notify:
            return

        notification_error = None

        # Webhook notification
        if schedule.notification_webhook_url:
            try:
                await self._send_webhook_notification(
                    schedule, execution, success, error
                )
            except Exception as e:
                notification_error = f"Webhook failed: {e}"
                log.exception(f"Failed to send webhook notification: {e}")

        # Email notification
        if schedule.notification_email:
            try:
                await self._send_email_notification(
                    schedule, execution, success, error
                )
            except Exception as e:
                if notification_error:
                    notification_error += f"; Email failed: {e}"
                else:
                    notification_error = f"Email failed: {e}"
                log.exception(f"Failed to send email notification: {e}")

        # Update notification status
        if schedule.notification_webhook_url or schedule.notification_email:
            from sema4ai.action_server._models import ScheduleExecution, get_db

            db = get_db()
            with db.connect():
                with db.transaction():
                    db.update_by_id(
                        ScheduleExecution,
                        execution.id,
                        {
                            "notification_sent": notification_error is None,
                            "notification_error": notification_error,
                        },
                    )

    async def _send_webhook_notification(
        self,
        schedule: "Schedule",
        execution: "ScheduleExecution",
        success: bool,
        error: Optional[str],
    ) -> None:
        """Send a webhook notification."""
        import aiohttp

        payload = {
            "schedule_id": schedule.id,
            "schedule_name": schedule.name,
            "execution_id": execution.id,
            "success": success,
            "status": "completed" if success else "failed",
            "error": error,
            "scheduled_time": execution.scheduled_time,
            "actual_start_time": execution.actual_start_time,
            "duration_ms": execution.duration_ms,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                schedule.notification_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status >= 400:
                    raise Exception(f"Webhook returned status {response.status}")

        log.info(f"Sent webhook notification for schedule {schedule.id}")

    async def _send_email_notification(
        self,
        schedule: "Schedule",
        execution: "ScheduleExecution",
        success: bool,
        error: Optional[str],
    ) -> None:
        """Send an email notification."""
        # Email notification requires SMTP configuration
        # This is handled by the NotificationService
        from sema4ai.action_server._notifications import get_notification_service

        service = get_notification_service()
        if service is None:
            log.warning("Email notifications not configured (no SMTP settings)")
            return

        subject = (
            f"[{'SUCCESS' if success else 'FAILURE'}] "
            f"Schedule: {schedule.name}"
        )

        body = f"""
Schedule Execution Report
========================

Schedule: {schedule.name}
Status: {'Completed successfully' if success else 'Failed'}
Execution ID: {execution.id}
Scheduled Time: {execution.scheduled_time}
Start Time: {execution.actual_start_time}
Duration: {execution.duration_ms}ms
"""

        if error:
            body += f"\nError:\n{error}\n"

        await service.send_email(
            to=schedule.notification_email,
            subject=subject,
            body=body,
        )

        log.info(f"Sent email notification for schedule {schedule.id}")

    def compute_next_run(
        self,
        schedule: "Schedule",
        after: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """
        Compute the next run time for a schedule.

        Args:
            schedule: The schedule to compute next run for
            after: Base time for calculation (defaults to now)

        Returns:
            Next run time in UTC, or None if no more runs
        """
        if after is None:
            after = datetime.now(timezone.utc)

        schedule_type = schedule.schedule_type

        if schedule_type == ScheduleType.CRON:
            return self._compute_cron_next(
                schedule.cron_expression,
                schedule.timezone,
                after,
            )
        elif schedule_type == ScheduleType.INTERVAL:
            return self._compute_interval_next(
                schedule.interval_seconds,
                after,
            )
        elif schedule_type == ScheduleType.WEEKDAY:
            return self._compute_weekday_next(
                schedule.weekday_config_json,
                schedule.timezone,
                after,
            )
        elif schedule_type == ScheduleType.ONCE:
            # One-time schedules don't have a next run after execution
            return None
        else:
            log.warning(f"Unknown schedule type: {schedule_type}")
            return None

    def _compute_cron_next(
        self,
        cron_expression: str,
        timezone_str: str,
        after: datetime,
    ) -> datetime:
        """Compute next run time from cron expression."""
        croniter = _get_croniter()

        try:
            import pytz
            tz = pytz.timezone(timezone_str)
        except ImportError:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone_str)

        # Convert to local timezone for cron calculation
        if after.tzinfo is None:
            after = after.replace(tzinfo=timezone.utc)
        local_after = after.astimezone(tz)

        cron = croniter(cron_expression, local_after)
        next_local = cron.get_next(datetime)

        # Convert back to UTC
        if hasattr(next_local, 'astimezone'):
            return next_local.astimezone(timezone.utc)
        else:
            # Handle naive datetime
            return next_local.replace(tzinfo=timezone.utc)

    def _compute_interval_next(
        self,
        interval_seconds: int,
        after: datetime,
    ) -> datetime:
        """Compute next run time for interval-based schedule."""
        return after + timedelta(seconds=interval_seconds)

    def _compute_weekday_next(
        self,
        weekday_config_json: str,
        timezone_str: str,
        after: datetime,
    ) -> datetime:
        """Compute next run time for weekday-based schedule."""
        config = json.loads(weekday_config_json)
        days = config.get("days", [])  # 0=Monday, 6=Sunday
        time_str = config.get("time", "09:00")  # HH:MM format

        if not days:
            raise ValueError("Weekday schedule has no days configured")

        try:
            import pytz
            tz = pytz.timezone(timezone_str)
        except ImportError:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone_str)

        # Parse time
        hour, minute = map(int, time_str.split(":"))

        # Convert after to local time
        if after.tzinfo is None:
            after = after.replace(tzinfo=timezone.utc)
        local_after = after.astimezone(tz)

        # Find next occurrence
        current = local_after.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        # If current time is past today's scheduled time, start from tomorrow
        if current <= local_after:
            current += timedelta(days=1)

        # Find the next matching weekday
        for _ in range(8):  # Max 7 days + 1 for edge cases
            if current.weekday() in days:
                break
            current += timedelta(days=1)

        return current.astimezone(timezone.utc)


# Global scheduler instance
_global_scheduler: Optional[SchedulerEngine] = None


def get_scheduler() -> Optional[SchedulerEngine]:
    """Get the global scheduler instance."""
    return _global_scheduler


def set_scheduler(scheduler: Optional[SchedulerEngine]) -> None:
    """Set the global scheduler instance."""
    global _global_scheduler
    _global_scheduler = scheduler


async def initialize_schedule_next_runs() -> None:
    """
    Initialize next_run_at for all enabled schedules that don't have one.

    This should be called on server startup.
    """
    from sema4ai.action_server._database import datetime_to_str
    from sema4ai.action_server._models import Schedule, get_db

    scheduler = get_scheduler()
    if scheduler is None:
        return

    db = get_db()
    now = datetime.now(timezone.utc)

    with db.connect():
        # Find schedules without next_run_at
        schedules = db.select(
            Schedule,
            """
            SELECT * FROM schedule
            WHERE enabled = 1 AND next_run_at IS NULL
            """,
        )

        for schedule in schedules:
            next_run = scheduler.compute_next_run(schedule, now)
            if next_run:
                with db.transaction():
                    db.update_by_id(
                        Schedule,
                        schedule.id,
                        {
                            "next_run_at": datetime_to_str(next_run),
                            "updated_at": datetime_to_str(now),
                        },
                    )
                log.info(
                    f"Initialized next_run_at for schedule {schedule.id}: {next_run}"
                )
