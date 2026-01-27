/* eslint-disable camelcase */
import type { OpenAPIV3_1 } from 'openapi-types';

export interface ActionPackage {
  id: string;
  name: string;
  actions: Action[];
}

export interface Action {
  id: string; // primary key (uuid)
  action_package_id: string; // foreign key to the action package
  name: string; // The action name
  docs: string; // Docs for the action
  enabled: boolean; // Is the action available to be run

  // File for the action (relative to the directory in the ActionPackage).
  file: string;
  lineno: number; // Line for the action
  input_schema: string; // The json content for the schema input
  output_schema: string; // The json content for the schema output
  managed_params_schema?: string; // The json content for the managed parameters.
}

export enum RunStatus {
  'NOT_RUN' = 0,
  'RUNNING' = 1,
  'PASSED' = 2,
  'FAILED' = 3,
  'CANCELLED' = 4,
}

export interface Run {
  id: string; // primary key (uuid)
  status: RunStatus; // 0=not run, 1=running, 2=passed, 3=failed, 4=cancelled
  action_id: string; // foreign key to the action (may be null for robots)
  start_time: string; // The time of the run creation.
  run_time?: number | null; // The time from the run creation to the run finish (in seconds)
  inputs: string; // The json content with the variables used as an input
  result?: string | null; // The json content of the output that the run generated (actions)
  error_message?: string | null; // If the status=failed, this may have an error message
  numbered_id: number;
  request_id?: string;
  relative_artifacts_dir?: string;
  // Unified fields:
  run_type: 'action' | 'robot'; // The type of run (action or robot)
  action_name?: string | null; // Name of the action if run_type='action'
  robot_package_path?: string | null; // Path to robot package if run_type='robot'
  robot_task_name?: string | null; // Name of robot task if run_type='robot'
  robot_env_hash?: string | null; // RCC environment hash if run_type='robot'
  stdout?: string | null; // Robot run stdout
  stderr?: string | null; // Robot run stderr
}

export interface RunTableEntry extends Run {
  action?: Action;
}

export type Artifact = Record<string, string>;

export interface ArtifactInfo {
  name: string;
  size_in_bytes: number;
}

export interface AsyncLoaded<T> {
  data?: T;
  isPending?: boolean;
  errorMessage?: string;
}

export type LoadedRuns = AsyncLoaded<Run[]>;
export type LoadedActionsPackages = AsyncLoaded<ActionPackage[]>;
export type LoadedArtifacts = AsyncLoaded<Artifact>;
export type LoadedServerConfig = AsyncLoaded<ServerConfig>;

export interface InputProperty {
  type: OpenAPIV3_1.NonArraySchemaObjectType | 'enum' | 'array';
  description: string;
  title: string;
  default?: string;
}

export type ServerConfig = {
  expose_url: string;
  auth_enabled: boolean;
  version: string; // The version for the action server (if it changes a full window reload would be needed).
  mtime_uuid: string; // The mtime of the action server (if it changes all data needs to be reloaded).
};

// Robot Catalog Types
export interface RobotTaskInfoAPI {
  name: string;
  docs: string;
}

export interface RobotPackageDetailAPI {
  name: string;
  description?: string;
  path: string;
  environment_hash: string;
  tasks: RobotTaskInfoAPI[];
}

export interface RobotCatalogResponseAPI {
  robots: RobotPackageDetailAPI[];
}

// Robot Run API Types
export interface RobotRunRequestAPI {
  robot_package_path: string;
  task_name: string;
  inputs: Record<string, string>;
  use_secrets: boolean;
}

export interface RobotRunResponseAPI {
  run_id: string;
  status: string;
  message?: string;
}

// ============================================================================
// Scheduling Types
// ============================================================================

export type ScheduleType = 'cron' | 'interval' | 'weekday' | 'once';
export type ExecutionMode = 'run' | 'work_item';
export type DependencyMode = 'after_success' | 'after_any';

export enum ScheduleExecutionStatus {
  TRIGGERED = 'triggered',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SKIPPED = 'skipped',
  RETRYING = 'retrying',
}

export interface ScheduleGroup {
  id: string;
  name: string;
  description?: string;
  parent_id?: string;
  color?: string;
  created_at: string;
}

export interface WeekdayConfig {
  days: number[]; // 0=Sunday, 1=Monday, ..., 6=Saturday
  time: string; // HH:MM format
}

export interface Schedule {
  id: string;
  name: string;
  description?: string;

  // Target
  action_id?: string;
  action_name?: string; // Populated by backend
  execution_mode: ExecutionMode;
  work_item_queue?: string;
  inputs: Record<string, unknown>; // Backend sends as object, not JSON string

  // Schedule type
  schedule_type: ScheduleType;
  cron_expression?: string;
  interval_seconds?: number;
  weekday_config?: WeekdayConfig; // Backend sends as object, not JSON string
  weekday_config_json?: string; // For internal use when parsing
  once_at?: string;
  timezone: string;

  // State
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_run_at?: string;
  next_run_at?: string;

  // Execution settings
  skip_if_running: boolean;
  max_concurrent: number;
  timeout_seconds: number;

  // Retry policy
  retry_enabled: boolean;
  retry_max_attempts: number;
  retry_delay_seconds: number;
  retry_backoff_multiplier: number;

  // Rate limiting
  rate_limit_enabled: boolean;
  rate_limit_max_per_hour?: number;
  rate_limit_max_per_day?: number;

  // Dependencies
  depends_on_schedule_id?: string;
  depends_on_schedule_name?: string; // Populated by backend
  dependency_mode: DependencyMode;

  // Notifications
  notify_on_failure: boolean;
  notify_on_success: boolean;
  notification_webhook_url?: string;
  notification_email?: string;

  // Organization
  group_id?: string;
  group_name?: string; // Populated by backend
  tags: string[]; // Backend sends as array, not JSON string
  priority: number;
}

export interface ScheduleExecution {
  id: string;
  schedule_id: string;
  run_id?: string;
  work_item_id?: string;
  scheduled_time: string;
  actual_start_time: string;
  actual_end_time?: string;
  duration_ms?: number;
  status: ScheduleExecutionStatus;
  attempt_number: number;
  error_message?: string;
  error_code?: string;
  skip_reason?: string;
  result_json?: string;
  notification_sent: boolean;
  notification_error?: string;
}

export interface ScheduleWithAction extends Schedule {
  action?: Action;
  group?: ScheduleGroup;
}

// Schedule API request/response types
export interface CreateScheduleRequest {
  name: string;
  description?: string;
  action_id?: string;
  execution_mode?: ExecutionMode;
  work_item_queue?: string;
  inputs?: Record<string, unknown>;
  schedule_type: ScheduleType;
  cron_expression?: string;
  interval_seconds?: number;
  weekday_config?: WeekdayConfig;
  once_at?: string;
  timezone?: string;
  enabled?: boolean;
  skip_if_running?: boolean;
  max_concurrent?: number;
  timeout_seconds?: number;
  retry_enabled?: boolean;
  retry_max_attempts?: number;
  retry_delay_seconds?: number;
  retry_backoff_multiplier?: number;
  rate_limit_enabled?: boolean;
  rate_limit_max_per_hour?: number;
  rate_limit_max_per_day?: number;
  depends_on_schedule_id?: string;
  dependency_mode?: DependencyMode;
  notify_on_failure?: boolean;
  notify_on_success?: boolean;
  notification_webhook_url?: string;
  notification_email?: string;
  group_id?: string;
  tags?: string[];
  priority?: number;
}

export interface UpdateScheduleRequest extends Partial<CreateScheduleRequest> {
  // All fields optional for partial updates
}

export interface ScheduleStatsResponse {
  total: number;
  enabled: number;
  disabled: number;
  running: number;
  failed_24h: number;
  success_rate_7d: number;
  total_executions_7d: number;
}

export interface CronValidationResponse {
  valid: boolean;
  error?: string;
  description?: string;
}

export interface PreviewRunsResponse {
  next_runs: string[];
  timezone: string;
}

// ============================================================================
// Trigger Types
// ============================================================================

export type TriggerType = 'webhook' | 'email' | 'file_watch';

export enum TriggerInvocationStatus {
  ACCEPTED = 'accepted',
  REJECTED = 'rejected',
  RATE_LIMITED = 'rate_limited',
  ERROR = 'error',
}

export interface Trigger {
  id: string;
  name: string;
  description?: string;
  action_id?: string;
  execution_mode: ExecutionMode;
  work_item_queue?: string;
  inputs_template_json: string;
  trigger_type: TriggerType;
  webhook_secret?: string;
  webhook_method: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_triggered_at?: string;
  trigger_count: number;
  rate_limit_enabled: boolean;
  rate_limit_max_per_minute: number;
}

export interface TriggerInvocation {
  id: string;
  trigger_id: string;
  invoked_at: string;
  source_ip?: string;
  payload_json?: string;
  headers_json?: string;
  status: TriggerInvocationStatus;
  run_id?: string;
  work_item_id?: string;
  error_message?: string;
}

export interface TriggerWithAction extends Trigger {
  action?: Action;
}
