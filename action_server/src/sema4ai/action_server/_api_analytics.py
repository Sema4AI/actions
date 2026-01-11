"""
Analytics API endpoints for Action Server.

Provides aggregated run statistics including:
- Summary metrics (total runs, success rate, average duration)
- Runs grouped by day
- Runs grouped by action
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi.routing import APIRouter

from sema4ai.action_server._models import RunStatus, get_db

log = logging.getLogger(__name__)
analytics_api_router = APIRouter(prefix="/api/analytics")


@dataclass
class AnalyticsSummary:
    """Summary statistics for all runs."""

    total_runs: int
    success_rate: float  # Percentage 0-100
    avg_duration_ms: float
    runs_today: int


@dataclass
class RunsByDay:
    """Run counts grouped by date."""

    date: str  # ISO date string (YYYY-MM-DD)
    total: int
    passed: int
    failed: int


@dataclass
class RunsByAction:
    """Run counts grouped by action."""

    action_name: str
    package_name: str
    total: int
    passed: int
    failed: int
    avg_duration_ms: float


def _empty_summary() -> AnalyticsSummary:
    """Returns an empty analytics summary when no runs exist."""
    return AnalyticsSummary(
        total_runs=0,
        success_rate=0.0,
        avg_duration_ms=0.0,
        runs_today=0,
    )


def _calculate_summary_metrics(row: tuple) -> AnalyticsSummary:
    """Calculates summary metrics from database row."""
    total_runs, passed_runs, failed_runs, avg_duration, runs_today = row

    # Calculate success rate from completed runs only
    passed_runs = passed_runs or 0
    failed_runs = failed_runs or 0
    completed_runs = passed_runs + failed_runs

    success_rate = 0.0
    if completed_runs > 0:
        success_rate = (passed_runs / completed_runs) * 100

    # Convert duration from seconds to milliseconds
    avg_duration_ms = (avg_duration * 1000) if avg_duration else 0.0

    return AnalyticsSummary(
        total_runs=total_runs,
        success_rate=round(success_rate, 1),
        avg_duration_ms=round(avg_duration_ms, 1),
        runs_today=runs_today or 0,
    )


def _seconds_to_milliseconds(seconds: float | None) -> float:
    """Converts seconds to milliseconds, returning 0.0 for None."""
    return (seconds * 1000) if seconds else 0.0


@analytics_api_router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary() -> AnalyticsSummary:
    """
    Returns summary statistics for all runs.

    Returns:
        AnalyticsSummary with total_runs, success_rate, avg_duration_ms, runs_today
    """
    db = get_db()
    with db.connect():
        with db.cursor() as cursor:
            # Get all statistics in a single query for better performance
            db.execute_query(
                cursor,
                """
                SELECT
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as passed_runs,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as failed_runs,
                    AVG(CASE
                        WHEN run_time IS NOT NULL AND status IN (?, ?)
                        THEN run_time
                        ELSE NULL
                    END) as avg_duration,
                    SUM(CASE
                        WHEN start_time >= date('now', 'start of day')
                        THEN 1
                        ELSE 0
                    END) as runs_today
                FROM run
                """,
                [
                    RunStatus.PASSED,
                    RunStatus.FAILED,
                    RunStatus.PASSED,
                    RunStatus.FAILED,
                ],
            )

            row = cursor.fetchone()
            if not row or row[0] == 0:
                return _empty_summary()

            return _calculate_summary_metrics(row)


@analytics_api_router.get("/runs-by-day", response_model=List[RunsByDay])
def get_runs_by_day(days: int = 30) -> List[RunsByDay]:
    """
    Returns run counts grouped by day.

    Args:
        days: Number of days to look back (default 30)

    Returns:
        List of RunsByDay objects sorted by date ascending
    """
    db = get_db()
    with db.connect():
        with db.cursor() as cursor:
            # Use SQLite date functions for cleaner date handling
            db.execute_query(
                cursor,
                """
                SELECT
                    date(start_time) as run_date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as failed
                FROM run
                WHERE start_time >= date('now', ? || ' days')
                GROUP BY date(start_time)
                ORDER BY run_date ASC
                """,
                [RunStatus.PASSED, RunStatus.FAILED, -days],
            )

            return [
                RunsByDay(
                    date=row[0],
                    total=row[1],
                    passed=row[2] or 0,
                    failed=row[3] or 0,
                )
                for row in cursor.fetchall()
            ]


@analytics_api_router.get("/runs-by-action", response_model=List[RunsByAction])
def get_runs_by_action() -> List[RunsByAction]:
    """
    Returns run counts grouped by action.

    Returns:
        List of RunsByAction objects sorted by total runs descending
    """
    from sema4ai.action_server._models import Action, ActionPackage

    db = get_db()
    with db.connect():
        with db.cursor() as cursor:
            # Get run statistics with action and package names in a single query
            db.execute_query(
                cursor,
                """
                SELECT
                    a.name as action_name,
                    ap.name as package_name,
                    COUNT(*) as total,
                    SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END) as failed,
                    AVG(CASE
                        WHEN r.run_time IS NOT NULL AND r.status IN (?, ?)
                        THEN r.run_time
                        ELSE NULL
                    END) as avg_duration
                FROM run r
                JOIN action a ON r.action_id = a.id
                JOIN action_package ap ON a.action_package_id = ap.id
                GROUP BY a.id, a.name, ap.name
                ORDER BY total DESC
                """,
                [
                    RunStatus.PASSED,
                    RunStatus.FAILED,
                    RunStatus.PASSED,
                    RunStatus.FAILED,
                ],
            )

            return [
                RunsByAction(
                    action_name=row[0],
                    package_name=row[1],
                    total=row[2],
                    passed=row[3] or 0,
                    failed=row[4] or 0,
                    avg_duration_ms=round(_seconds_to_milliseconds(row[5]), 1),
                )
                for row in cursor.fetchall()
            ]
