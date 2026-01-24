"""
Migration 10: Add scheduling tables for Action Server scheduling feature.

This migration adds support for:
- Schedules (cron, interval, weekday, one-time)
- Schedule groups for organization
- Schedule execution history
- Triggers (webhook, email)
- Trigger invocation logs
"""

from sema4ai.action_server._database import Database
from sema4ai.action_server.migrations import Migration


def migrate(db: Database) -> None:
    from sema4ai.action_server.migrations import MIGRATION_ID_TO_NAME

    sqls = [
        # Schedule groups/folders for organization
        """
CREATE TABLE IF NOT EXISTS schedule_group (
    id TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT NULL,
    parent_id TEXT DEFAULT NULL,
    color TEXT DEFAULT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES schedule_group(id)
);
""",
        # Core schedule table
        """
CREATE TABLE IF NOT EXISTS schedule (
    id TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT NULL,

    -- Target (what to execute)
    action_id TEXT DEFAULT NULL,
    execution_mode TEXT NOT NULL DEFAULT 'run',
    work_item_queue TEXT DEFAULT NULL,
    inputs_json TEXT NOT NULL DEFAULT '{}',

    -- Schedule type (one of these is set)
    schedule_type TEXT NOT NULL,
    cron_expression TEXT DEFAULT NULL,
    interval_seconds INTEGER DEFAULT NULL,
    weekday_config_json TEXT DEFAULT NULL,
    once_at TEXT DEFAULT NULL,

    timezone TEXT NOT NULL DEFAULT 'UTC',

    -- State
    enabled INTEGER CHECK(enabled IN (0, 1)) NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_run_at TEXT DEFAULT NULL,
    next_run_at TEXT DEFAULT NULL,

    -- Execution settings
    skip_if_running INTEGER CHECK(skip_if_running IN (0, 1)) NOT NULL DEFAULT 0,
    max_concurrent INTEGER NOT NULL DEFAULT 1,
    timeout_seconds INTEGER NOT NULL DEFAULT 3600,

    -- Retry policy
    retry_enabled INTEGER CHECK(retry_enabled IN (0, 1)) NOT NULL DEFAULT 0,
    retry_max_attempts INTEGER NOT NULL DEFAULT 3,
    retry_delay_seconds INTEGER NOT NULL DEFAULT 60,
    retry_backoff_multiplier REAL NOT NULL DEFAULT 2.0,

    -- Rate limiting
    rate_limit_enabled INTEGER CHECK(rate_limit_enabled IN (0, 1)) NOT NULL DEFAULT 0,
    rate_limit_max_per_hour INTEGER DEFAULT NULL,
    rate_limit_max_per_day INTEGER DEFAULT NULL,

    -- Dependencies
    depends_on_schedule_id TEXT DEFAULT NULL,
    dependency_mode TEXT NOT NULL DEFAULT 'after_success',

    -- Notifications
    notify_on_failure INTEGER CHECK(notify_on_failure IN (0, 1)) NOT NULL DEFAULT 0,
    notify_on_success INTEGER CHECK(notify_on_success IN (0, 1)) NOT NULL DEFAULT 0,
    notification_webhook_url TEXT DEFAULT NULL,
    notification_email TEXT DEFAULT NULL,

    -- Organization
    group_id TEXT DEFAULT NULL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    priority INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (action_id) REFERENCES action(id),
    FOREIGN KEY (depends_on_schedule_id) REFERENCES schedule(id),
    FOREIGN KEY (group_id) REFERENCES schedule_group(id)
);
""",
        # Schedule execution audit trail
        """
CREATE TABLE IF NOT EXISTS schedule_execution (
    id TEXT NOT NULL PRIMARY KEY,
    schedule_id TEXT NOT NULL,

    -- What was created
    run_id TEXT DEFAULT NULL,
    work_item_id TEXT DEFAULT NULL,

    -- Timing
    scheduled_time TEXT NOT NULL,
    actual_start_time TEXT NOT NULL,
    actual_end_time TEXT DEFAULT NULL,
    duration_ms INTEGER DEFAULT NULL,

    -- Status
    status TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    error_message TEXT DEFAULT NULL,
    error_code TEXT DEFAULT NULL,
    skip_reason TEXT DEFAULT NULL,

    -- Result data
    result_json TEXT DEFAULT NULL,

    -- Notification tracking
    notification_sent INTEGER CHECK(notification_sent IN (0, 1)) NOT NULL DEFAULT 0,
    notification_error TEXT DEFAULT NULL,

    FOREIGN KEY (schedule_id) REFERENCES schedule(id)
);
""",
        # Triggers (webhook, email, file_watch)
        """
CREATE TABLE IF NOT EXISTS trigger (
    id TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT NULL,

    -- What to execute
    action_id TEXT DEFAULT NULL,
    execution_mode TEXT NOT NULL DEFAULT 'run',
    work_item_queue TEXT DEFAULT NULL,
    inputs_template_json TEXT NOT NULL DEFAULT '{}',

    -- Trigger type
    trigger_type TEXT NOT NULL,

    -- Webhook config
    webhook_secret TEXT DEFAULT NULL,
    webhook_method TEXT NOT NULL DEFAULT 'POST',

    -- State
    enabled INTEGER CHECK(enabled IN (0, 1)) NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_triggered_at TEXT DEFAULT NULL,
    trigger_count INTEGER NOT NULL DEFAULT 0,

    -- Rate limiting
    rate_limit_enabled INTEGER CHECK(rate_limit_enabled IN (0, 1)) NOT NULL DEFAULT 0,
    rate_limit_max_per_minute INTEGER NOT NULL DEFAULT 60,

    FOREIGN KEY (action_id) REFERENCES action(id)
);
""",
        # Trigger invocation log
        """
CREATE TABLE IF NOT EXISTS trigger_invocation (
    id TEXT NOT NULL PRIMARY KEY,
    trigger_id TEXT NOT NULL,

    -- Invocation details
    invoked_at TEXT NOT NULL,
    source_ip TEXT DEFAULT NULL,
    payload_json TEXT DEFAULT NULL,
    headers_json TEXT DEFAULT NULL,

    -- Result
    status TEXT NOT NULL,
    run_id TEXT DEFAULT NULL,
    work_item_id TEXT DEFAULT NULL,
    error_message TEXT DEFAULT NULL,

    FOREIGN KEY (trigger_id) REFERENCES trigger(id)
);
""",
        # Indexes for schedule_group
        "CREATE UNIQUE INDEX schedule_group_id_index ON schedule_group(id);",
        "CREATE INDEX schedule_group_parent_id_non_unique_index ON schedule_group(parent_id);",
        # Indexes for schedule
        "CREATE UNIQUE INDEX schedule_id_index ON schedule(id);",
        "CREATE INDEX schedule_enabled_next_non_unique_index ON schedule(enabled, next_run_at);",
        "CREATE INDEX schedule_group_id_non_unique_index ON schedule(group_id);",
        "CREATE INDEX schedule_depends_on_non_unique_index ON schedule(depends_on_schedule_id);",
        "CREATE INDEX schedule_action_id_non_unique_index ON schedule(action_id);",
        # Indexes for schedule_execution
        "CREATE UNIQUE INDEX schedule_execution_id_index ON schedule_execution(id);",
        "CREATE INDEX schedule_execution_schedule_id_non_unique_index ON schedule_execution(schedule_id);",
        "CREATE INDEX schedule_execution_status_non_unique_index ON schedule_execution(status);",
        # Indexes for trigger
        "CREATE UNIQUE INDEX trigger_id_index ON trigger(id);",
        "CREATE INDEX trigger_type_non_unique_index ON trigger(trigger_type);",
        "CREATE INDEX trigger_action_id_non_unique_index ON trigger(action_id);",
        # Indexes for trigger_invocation
        "CREATE UNIQUE INDEX trigger_invocation_id_index ON trigger_invocation(id);",
        "CREATE INDEX trigger_invocation_trigger_id_non_unique_index ON trigger_invocation(trigger_id);",
    ]

    for sql in sqls:
        db.execute(sql)

    db.insert(Migration(id=10, name=MIGRATION_ID_TO_NAME[10]))
