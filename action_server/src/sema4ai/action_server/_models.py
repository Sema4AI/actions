import typing
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from sema4ai.action_server._database import DBRules

if typing.TYPE_CHECKING:
    from sema4ai.action_server._database import Database


_db_rules = DBRules()


@dataclass
class ActionPackage:  # Table name: action_package
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("ActionPackage.id")

    name: str  # The name for the action package
    _db_rules.unique_indexes.add("ActionPackage.name")

    # The directory where the action package is (may be stored relative
    # to the datadir or as an absolute path).
    # When relative starts with `./`, otherwise it's absolute.
    directory: str

    # The sha256 hash of the package.yaml (based only on the actual content
    # not considering spaces and comments).
    conda_hash: str

    # The environment to be used for launches (as json).
    env_json: str


@dataclass
class Action:  # Table name: action
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("Action.id")

    action_package_id: str  # foreign key to the action package
    _db_rules.foreign_keys.add("Action.action_package_id")
    _db_rules.indexes.add("Action.action_package_id")

    name: str  # The action name
    docs: str  # Docs for the action

    # File for the action (relative to the directory in the ActionPackage).
    file: str

    lineno: int  # Line for the action
    input_schema: str  # The json content for the schema input
    output_schema: str  # The json content for the schema output

    enabled: bool = True

    is_consequential: Optional[bool] = None

    # The json content for the managed params schema
    managed_params_schema: Optional[str] = None

    options: str = ""


RUN_ID_COUNTER = "run_id"
ALL_COUNTERS = (RUN_ID_COUNTER,)


@dataclass
class Counter:
    id: str  # primary key (counter name -- i.e.: RUN_ID_COUNTER)
    _db_rules.unique_indexes.add("Counter.id")

    value: int  # current value


@dataclass
class Run:
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("Run.id")

    status: int  # 0=not run, 1=running, 2=passed, 3=failed, 4=cancelled
    _db_rules.indexes.add("Run.status")

    action_id: str  # action ID (empty for robot runs, no FK constraint)
    _db_rules.indexes.add("Run.action_id")

    start_time: str  # The time that the action started running
    run_time: Optional[float]  # Duration in seconds
    inputs: str  # JSON input data
    result: Optional[str]  # JSON output data
    error_message: Optional[str]  # Error message if failed

    relative_artifacts_dir: str
    numbered_id: int
    _db_rules.unique_indexes.add("Run.numbered_id")

    request_id: str = ""  # Request ID if any
    _db_rules.indexes.add("Run.request_id")

    run_type: str = "action"  # 'action' or 'robot'
    _db_rules.indexes.add("Run.run_type")

    robot_package_path: Optional[
        str
    ] = None  # Path to robot package if run_type='robot'
    robot_task_name: Optional[str] = None  # Name of robot task if run_type='robot'
    robot_env_hash: Optional[str] = None  # RCC environment hash if run_type='robot'


@dataclass
class UserSession:
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("UserSession.id")

    created_at: str  # date in isoformat
    accessed_at: str  # date in isoformat

    external: bool  # Determines if it was requested to be created internally (automatically) or externally
    _db_rules.indexes.add("UserSession.external")


@dataclass
class TempUserSessionData:
    user_session_id: str  # foreign key (uuid)
    _db_rules.foreign_keys.add("TempUserSessionData.user_session_id")
    _db_rules.indexes.add("TempUserSessionData.user_session_id")

    key: str
    _db_rules.indexes.add("TempUserSessionData.key")

    data: str  # A json-blob of data
    expires_at: str  # date in isoformat


@dataclass
class OAuth2UserData:
    user_session_id: str  # foreign key (uuid)
    _db_rules.foreign_keys.add("OAuth2.user_session_id")
    _db_rules.indexes.add("OAuth2.user_session_id")

    provider: str
    _db_rules.indexes.add("OAuth2.provider")

    refresh_token: str  # Data encrypted with storage key
    access_token: str  # Data encrypted with storage key

    # date in isoformat or an
    # empty string if not available
    expires_at: str

    token_type: str

    # Actually a json-blob of list[str] or an
    # empty string if it is not available.
    scopes: str

    # May be used to add metadata obtained from the OAuth2 flow into the
    # model (for data which is not available in the above info already).
    metadata: str = ""

    # The code verifier is needed for pkce (authentication without a clientSecret).
    code_verifier: str = ""  # Data encrypted with storage key


class RunStatus:
    NOT_RUN = 0
    RUNNING = 1
    PASSED = 2
    FAILED = 3
    CANCELLED = 4


# ============================================================================
# Scheduling Models
# ============================================================================


@dataclass
class ScheduleGroup:  # Table name: schedule_group
    """A group/folder for organizing schedules."""

    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("ScheduleGroup.id")

    name: str  # Group name
    description: Optional[str]  # Group description
    parent_id: Optional[str]  # Parent group for nesting
    _db_rules.indexes.add("ScheduleGroup.parent_id")

    color: Optional[str]  # UI color hint
    created_at: str  # ISO datetime


@dataclass
class Schedule:  # Table name: schedule
    """A scheduled action execution configuration."""

    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("Schedule.id")

    name: str  # Schedule name
    description: Optional[str]  # Schedule description

    # Target (what to execute)
    action_id: Optional[str]  # FK to action (nullable for work_item mode)
    _db_rules.indexes.add("Schedule.action_id")

    execution_mode: str  # 'run' | 'work_item'
    work_item_queue: Optional[str]  # Queue name for work_item mode
    inputs_json: str  # JSON input data for the action

    # Schedule type (one of these is set)
    schedule_type: str  # 'cron' | 'interval' | 'weekday' | 'once'
    cron_expression: Optional[str]  # Cron expression for 'cron' type
    interval_seconds: Optional[int]  # Interval for 'interval' type
    weekday_config_json: Optional[str]  # JSON config for 'weekday' type
    once_at: Optional[str]  # ISO datetime for 'once' type

    timezone: str  # IANA timezone (e.g., 'UTC', 'America/New_York')

    # State
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None

    # Execution settings
    skip_if_running: bool = False
    max_concurrent: int = 1
    timeout_seconds: int = 3600

    # Retry policy
    retry_enabled: bool = False
    retry_max_attempts: int = 3
    retry_delay_seconds: int = 60
    retry_backoff_multiplier: float = 2.0

    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_max_per_hour: Optional[int] = None
    rate_limit_max_per_day: Optional[int] = None

    # Dependencies
    depends_on_schedule_id: Optional[str] = None  # FK to another schedule
    _db_rules.indexes.add("Schedule.depends_on_schedule_id")

    dependency_mode: str = "after_success"  # 'after_success' | 'after_any'

    # Notifications
    notify_on_failure: bool = False
    notify_on_success: bool = False
    notification_webhook_url: Optional[str] = None
    notification_email: Optional[str] = None

    # Organization
    group_id: Optional[str] = None  # FK to schedule_group
    _db_rules.indexes.add("Schedule.group_id")

    tags_json: str = "[]"  # JSON array of tags
    priority: int = 0


class ScheduleExecutionStatus:
    """Status values for schedule executions."""

    TRIGGERED = "triggered"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ScheduleSkipReason:
    """Reasons for skipping a schedule execution."""

    PREVIOUS_RUNNING = "previous_running"
    RATE_LIMITED = "rate_limited"
    DEPENDENCY_FAILED = "dependency_failed"
    DISABLED = "disabled"


@dataclass
class ScheduleExecution:  # Table name: schedule_execution
    """Record of a schedule execution."""

    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("ScheduleExecution.id")

    schedule_id: str  # FK to schedule
    _db_rules.indexes.add("ScheduleExecution.schedule_id")

    # What was created
    run_id: Optional[str]  # If execution_mode='run'
    work_item_id: Optional[str]  # If execution_mode='work_item'

    # Timing
    scheduled_time: str  # When it was scheduled to run (ISO datetime)
    actual_start_time: str  # When execution actually started
    actual_end_time: Optional[str]  # When execution completed
    duration_ms: Optional[int]  # Duration in milliseconds

    # Status
    status: str  # See ScheduleExecutionStatus
    _db_rules.indexes.add("ScheduleExecution.status")

    attempt_number: int = 1  # Current retry attempt
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    skip_reason: Optional[str] = None  # See ScheduleSkipReason

    # Result data
    result_json: Optional[str] = None

    # Notification tracking
    notification_sent: bool = False
    notification_error: Optional[str] = None


@dataclass
class Trigger:  # Table name: trigger
    """A trigger for event-driven action execution (webhook, email, etc.)."""

    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("Trigger.id")

    name: str  # Trigger name
    description: Optional[str]  # Trigger description

    # What to execute
    action_id: Optional[str]  # FK to action
    _db_rules.indexes.add("Trigger.action_id")

    execution_mode: str  # 'run' | 'work_item'
    work_item_queue: Optional[str]  # Queue name for work_item mode
    inputs_template_json: str  # JSON template with {{payload.field}} vars

    # Trigger type
    trigger_type: str  # 'webhook' | 'email' | 'file_watch'
    _db_rules.indexes.add("Trigger.trigger_type")

    # Webhook config
    webhook_secret: Optional[str]  # Secret for HMAC signature validation
    webhook_method: str  # HTTP method: 'POST', 'PUT'

    # State
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""
    last_triggered_at: Optional[str] = None
    trigger_count: int = 0

    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_max_per_minute: int = 60


class TriggerInvocationStatus:
    """Status values for trigger invocations."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class TriggerInvocation:  # Table name: trigger_invocation
    """Record of a trigger invocation."""

    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("TriggerInvocation.id")

    trigger_id: str  # FK to trigger
    _db_rules.indexes.add("TriggerInvocation.trigger_id")

    # Invocation details
    invoked_at: str  # ISO datetime
    source_ip: Optional[str]  # Client IP address
    payload_json: Optional[str]  # Request payload
    headers_json: Optional[str]  # Request headers

    # Result
    status: str  # See TriggerInvocationStatus
    run_id: Optional[str]  # Created run ID if any
    work_item_id: Optional[str]  # Created work item ID if any
    error_message: Optional[str]  # Error message if status='error'


def run_status_to_str(run_status: int) -> str:
    """
    Args:
        run_status: The run status to convert to a string.

    Returns:
        The string representation of the run status.
    """
    if run_status == RunStatus.NOT_RUN:
        return "not run"
    elif run_status == RunStatus.RUNNING:
        return "running"
    elif run_status == RunStatus.PASSED:
        return "passed"
    elif run_status == RunStatus.FAILED:
        return "failed"
    elif run_status == RunStatus.CANCELLED:
        return "cancelled"
    else:
        raise ValueError(f"Invalid run status: {run_status}")


def get_all_model_classes():
    from sema4ai.action_server.migrations import Migration

    return [
        Migration,
        ActionPackage,
        Action,
        Run,
        Counter,
        UserSession,
        TempUserSessionData,
        OAuth2UserData,
        # Scheduling models
        ScheduleGroup,
        Schedule,
        ScheduleExecution,
        Trigger,
        TriggerInvocation,
    ]


def get_model_db_rules() -> DBRules:
    return _db_rules


_global_db: Optional["Database"] = None


@contextmanager
def load_db(db_path: Union[Path, str]) -> Iterator["Database"]:
    """
    Loads the database from the given path and initializes the internal
    models, besides setting this db as the global db for the duration
    of the context manager.
    """
    from sema4ai.action_server._database import Database

    global _global_db

    if _global_db is not None:
        raise AssertionError("There is already a global initialized database.")

    db = Database(db_path)
    with db.connect():
        db.initialize(get_all_model_classes())
        _global_db = db
        try:
            yield db
        finally:
            _global_db = None


@contextmanager
def create_db(db_path: Union[Path, str]) -> Iterator["Database"]:
    """
    Creates the database and sets this db as the global db for the duration
    of the context manager.
    """
    from sema4ai.action_server.migrations import (
        CURRENT_VERSION,
        MIGRATION_ID_TO_NAME,
        Migration,
    )

    with load_db(db_path) as db:
        with db.transaction():
            db.create_tables(get_model_db_rules())
            current_migration = MIGRATION_ID_TO_NAME[CURRENT_VERSION]
            db.insert(Migration(CURRENT_VERSION, current_migration))
            for counter in ALL_COUNTERS:
                db.insert(Counter(counter, 0))
        yield db


class DBNotInitializedError(AssertionError):
    pass


def get_db() -> "Database":
    if _global_db is None:
        raise DBNotInitializedError("DB not initialized")
    return _global_db


def get_action_package_from_action(action: Action) -> ActionPackage:
    db = get_db()
    return db.first(
        ActionPackage,
        "SELECT * FROM action_package WHERE id = ?",
        [action.action_package_id],
    )


class RunListItemModel(BaseModel):
    id: str
    status: int
    action_id: str
    start_time: str
    run_time: Optional[float]
    inputs: str
    result: Optional[str]
    error_message: Optional[str]
    relative_artifacts_dir: str
    numbered_id: int
    request_id: str = ""
    run_type: str = "action"
    action_name: Optional[str] = None
    robot_package_path: Optional[str] = None
    robot_task_name: Optional[str] = None
    robot_env_hash: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    class Config:
        from_attributes = True


class RunDetailModel(RunListItemModel):
    # Inherit all fields, but can be extended for more details if needed
    pass
