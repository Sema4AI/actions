-- DuckDB Schema for Consolidated Robocorp Task Logs Dashboard
-- This schema defines the structure for storing and querying task execution logs

-- Main task logs table
CREATE TABLE IF NOT EXISTS task_logs (
    id INTEGER PRIMARY KEY,
    task_name VARCHAR NOT NULL,                -- Producer, Consumer, Reporter
    timestamp TIMESTAMP NOT NULL,
    log_level VARCHAR NOT NULL,                -- INFO, WARNING, ERROR, DEBUG
    message TEXT NOT NULL,
    file_path VARCHAR,                         -- Source file reference
    line_number INTEGER,                       -- Line number in source file
    execution_time_ms INTEGER,                 -- Execution time in milliseconds
    thread_id VARCHAR,                         -- Thread identifier
    work_item_id VARCHAR,                      -- Associated work item ID
    screenshot_refs TEXT[]                     -- Array of screenshot file paths
);

-- Task execution summary table
CREATE TABLE IF NOT EXISTS task_executions (
    id INTEGER PRIMARY KEY,
    task_name VARCHAR NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    status VARCHAR NOT NULL,                   -- SUCCESS, FAILURE, CANCELLED
    total_work_items INTEGER,
    processed_items INTEGER,
    failed_items INTEGER,
    error_summary TEXT,
    log_file_path VARCHAR,
    output_artifacts TEXT[]                    -- Array of output file paths
);

-- Work items processing details
CREATE TABLE IF NOT EXISTS work_items (
    id INTEGER PRIMARY KEY,
    task_name VARCHAR NOT NULL,
    work_item_id VARCHAR NOT NULL,
    call_id VARCHAR,
    status VARCHAR NOT NULL,                   -- PASS, FAIL, PENDING
    original_file VARCHAR,
    error_message TEXT,
    retry_attempted BOOLEAN DEFAULT FALSE,
    processing_time_ms INTEGER,
    screenshot_paths TEXT[],                   -- Array of screenshot file paths
    timestamp TIMESTAMP NOT NULL
);

-- Screenshot metadata table
CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY,
    task_name VARCHAR NOT NULL,
    work_item_id VARCHAR,
    file_path VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    file_size INTEGER,
    timestamp TIMESTAMP NOT NULL,
    description TEXT                           -- Optional description of screenshot
);

-- Task performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY,
    task_name VARCHAR NOT NULL,
    metric_name VARCHAR NOT NULL,              -- e.g., 'memory_usage', 'cpu_usage', 'network_calls'
    metric_value DECIMAL,
    metric_unit VARCHAR,                       -- e.g., 'MB', 'percent', 'count'
    timestamp TIMESTAMP NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_task_logs_timestamp ON task_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_task_logs_task_name ON task_logs(task_name);
CREATE INDEX IF NOT EXISTS idx_task_logs_log_level ON task_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_task_logs_work_item_id ON task_logs(work_item_id);

CREATE INDEX IF NOT EXISTS idx_task_executions_task_name ON task_executions(task_name);
CREATE INDEX IF NOT EXISTS idx_task_executions_start_time ON task_executions(start_time);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);

CREATE INDEX IF NOT EXISTS idx_work_items_task_name ON work_items(task_name);
CREATE INDEX IF NOT EXISTS idx_work_items_status ON work_items(status);
CREATE INDEX IF NOT EXISTS idx_work_items_call_id ON work_items(call_id);
CREATE INDEX IF NOT EXISTS idx_work_items_timestamp ON work_items(timestamp);

CREATE INDEX IF NOT EXISTS idx_screenshots_task_name ON screenshots(task_name);
CREATE INDEX IF NOT EXISTS idx_screenshots_work_item_id ON screenshots(work_item_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_timestamp ON screenshots(timestamp);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_task_name ON performance_metrics(task_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Useful views for dashboard queries
CREATE VIEW IF NOT EXISTS task_summary AS
SELECT 
    te.task_name,
    te.start_time,
    te.end_time,
    te.duration_ms,
    te.status,
    te.total_work_items,
    te.processed_items,
    te.failed_items,
    COALESCE(error_count.error_count, 0) as error_log_count,
    COALESCE(warning_count.warning_count, 0) as warning_log_count,
    COALESCE(screenshot_count.screenshot_count, 0) as screenshot_count
FROM task_executions te
LEFT JOIN (
    SELECT task_name, COUNT(*) as error_count
    FROM task_logs 
    WHERE log_level = 'ERROR' 
    GROUP BY task_name
) error_count ON te.task_name = error_count.task_name
LEFT JOIN (
    SELECT task_name, COUNT(*) as warning_count
    FROM task_logs 
    WHERE log_level = 'WARNING' 
    GROUP BY task_name
) warning_count ON te.task_name = warning_count.task_name
LEFT JOIN (
    SELECT task_name, COUNT(*) as screenshot_count
    FROM screenshots 
    GROUP BY task_name
) screenshot_count ON te.task_name = screenshot_count.task_name;

-- View for work item status distribution
CREATE VIEW IF NOT EXISTS work_item_status_summary AS
SELECT 
    task_name,
    status,
    COUNT(*) as item_count,
    AVG(processing_time_ms) as avg_processing_time_ms,
    MIN(timestamp) as first_processed,
    MAX(timestamp) as last_processed
FROM work_items
GROUP BY task_name, status;

-- View for error analysis
CREATE VIEW IF NOT EXISTS error_analysis AS
SELECT 
    tl.task_name,
    tl.timestamp,
    tl.message,
    tl.file_path,
    tl.line_number,
    tl.work_item_id,
    wi.call_id,
    wi.error_message as work_item_error
FROM task_logs tl
LEFT JOIN work_items wi ON tl.work_item_id = wi.work_item_id
WHERE tl.log_level = 'ERROR'
ORDER BY tl.timestamp DESC;

-- View for performance trending
CREATE VIEW IF NOT EXISTS performance_trends AS
SELECT 
    task_name,
    DATE_TRUNC('minute', timestamp) as time_bucket,
    AVG(CASE WHEN metric_name = 'memory_usage' THEN metric_value END) as avg_memory_mb,
    AVG(CASE WHEN metric_name = 'cpu_usage' THEN metric_value END) as avg_cpu_percent,
    COUNT(CASE WHEN metric_name = 'network_calls' THEN 1 END) as network_calls
FROM performance_metrics
GROUP BY task_name, DATE_TRUNC('minute', timestamp)
ORDER BY task_name, time_bucket;