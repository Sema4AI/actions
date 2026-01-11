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

from sema4ai.action_server._models import Run, RunStatus, get_db

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
            # Get total runs count
            db.execute_query(cursor, "SELECT COUNT(*) FROM run")
            total_runs = cursor.fetchone()[0]

            if total_runs == 0:
                return AnalyticsSummary(
                    total_runs=0,
                    success_rate=0.0,
                    avg_duration_ms=0.0,
                    runs_today=0,
                )

            # Get passed runs count
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM run WHERE status = ?",
                [RunStatus.PASSED],
            )
            passed_runs = cursor.fetchone()[0]

            # Get average duration (only for completed runs)
            db.execute_query(
                cursor,
                """
                SELECT AVG(run_time) FROM run
                WHERE run_time IS NOT NULL AND status IN (?, ?)
                """,
                [RunStatus.PASSED, RunStatus.FAILED],
            )
            avg_duration_result = cursor.fetchone()[0]
            avg_duration_ms = (
                (avg_duration_result * 1000) if avg_duration_result else 0.0
            )

            # Get runs today count
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM run WHERE start_time >= ?",
                [today_start],
            )
            runs_today = cursor.fetchone()[0]

            # Calculate success rate (passed / (passed + failed))
            db.execute_query(
                cursor,
                "SELECT COUNT(*) FROM run WHERE status = ?",
                [RunStatus.FAILED],
            )
            failed_runs = cursor.fetchone()[0]
            completed_runs = passed_runs + failed_runs
            success_rate = (
                (passed_runs / completed_runs * 100) if completed_runs > 0 else 0.0
            )

            return AnalyticsSummary(
                total_runs=total_runs,
                success_rate=round(success_rate, 1),
                avg_duration_ms=round(avg_duration_ms, 1),
                runs_today=runs_today,
            )


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
            # Calculate start date
            start_date = (datetime.now() - timedelta(days=days)).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()

            # Get all runs in the date range
            db.execute_query(
                cursor,
                """
                SELECT
                    date(start_time) as run_date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as failed
                FROM run
                WHERE start_time >= ?
                GROUP BY date(start_time)
                ORDER BY run_date ASC
                """,
                [RunStatus.PASSED, RunStatus.FAILED, start_date],
            )

            results = []
            for row in cursor.fetchall():
                run_date, total, passed, failed = row
                results.append(
                    RunsByDay(
                        date=run_date,
                        total=total,
                        passed=passed or 0,
                        failed=failed or 0,
                    )
                )

            return results


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
            # Get run statistics per action
            db.execute_query(
                cursor,
                """
                SELECT
                    r.action_id,
                    COUNT(*) as total,
                    SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN r.status = ? THEN 1 ELSE 0 END) as failed,
                    AVG(CASE WHEN r.run_time IS NOT NULL AND r.status IN (?, ?)
                        THEN r.run_time ELSE NULL END) as avg_duration
                FROM run r
                GROUP BY r.action_id
                ORDER BY total DESC
                """,
                [RunStatus.PASSED, RunStatus.FAILED, RunStatus.PASSED, RunStatus.FAILED],
            )

            run_stats = {}
            for row in cursor.fetchall():
                action_id, total, passed, failed, avg_duration = row
                run_stats[action_id] = {
                    "total": total,
                    "passed": passed or 0,
                    "failed": failed or 0,
                    "avg_duration": avg_duration,
                }

        # Get action and package names
        actions = db.all(Action)
        action_packages = db.all(ActionPackage)

        # Build package lookup
        package_lookup = {pkg.id: pkg.name for pkg in action_packages}

        results = []
        for action in actions:
            if action.id in run_stats:
                stats = run_stats[action.id]
                avg_duration_ms = (
                    (stats["avg_duration"] * 1000) if stats["avg_duration"] else 0.0
                )
                results.append(
                    RunsByAction(
                        action_name=action.name,
                        package_name=package_lookup.get(action.action_package_id, "Unknown"),
                        total=stats["total"],
                        passed=stats["passed"],
                        failed=stats["failed"],
                        avg_duration_ms=round(avg_duration_ms, 1),
                    )
                )

        # Sort by total runs descending
        results.sort(key=lambda x: x.total, reverse=True)
        return results
