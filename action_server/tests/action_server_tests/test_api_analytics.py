"""
Tests for the Analytics API endpoints.
"""

from datetime import datetime, timedelta

import pytest

from sema4ai.action_server._api_analytics import (
    AnalyticsSummary,
    RunsByAction,
    RunsByDay,
    get_analytics_summary,
    get_runs_by_action,
    get_runs_by_day,
)
from sema4ai.action_server._models import (
    Action,
    ActionPackage,
    Run,
    RunStatus,
    create_db,
)


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    with create_db(db_path) as db:
        yield db


def _create_test_action(
    action_id: str, package_id: str, action_name: str, lineno: int = 10
) -> Action:
    """Helper to create test action objects."""
    return Action(
        id=action_id,
        action_package_id=package_id,
        name=action_name,
        docs=f"Test {action_name}",
        file="actions.py",
        lineno=lineno,
        input_schema="{}",
        output_schema="{}",
        enabled=True,
    )


def _create_test_run(
    run_id: str,
    action_id: str,
    status: RunStatus,
    start_time: str,
    run_time: float,
    numbered_id: int,
) -> Run:
    """Helper to create test run objects."""
    return Run(
        id=run_id,
        status=status,  # type: ignore[arg-type]
        action_id=action_id,
        start_time=start_time,
        run_time=run_time,
        inputs="{}",
        result='{"success": true}' if status == RunStatus.PASSED else None,
        error_message="Test error" if status == RunStatus.FAILED else None,
        relative_artifacts_dir=run_id,
        numbered_id=numbered_id,
    )


@pytest.fixture
def populated_db(tmp_path):
    """Create a temporary database with sample data."""
    db_path = tmp_path / "test_populated.db"
    with create_db(db_path) as db:
        with db.transaction():
            # Create an action package
            package = ActionPackage(
                id="pkg-001",
                name="test-package",
                directory="./test-package",
                conda_hash="abc123",
                env_json="{}",
            )
            db.insert(package)

            # Create actions
            action1 = _create_test_action("action-001", "pkg-001", "test_action_1", 10)
            action2 = _create_test_action("action-002", "pkg-001", "test_action_2", 20)
            db.insert(action1)
            db.insert(action2)

            # Create runs
            now = datetime.now()
            today = now.isoformat()
            yesterday = (now - timedelta(days=1)).isoformat()

            runs = [
                # Today's runs for action 1
                _create_test_run(
                    "run-001", "action-001", RunStatus.PASSED, today, 1.5, 1
                ),
                _create_test_run(
                    "run-002", "action-001", RunStatus.FAILED, today, 0.5, 2
                ),
                # Yesterday's runs for action 2
                _create_test_run(
                    "run-003", "action-002", RunStatus.PASSED, yesterday, 2.0, 3
                ),
                _create_test_run(
                    "run-004", "action-002", RunStatus.PASSED, yesterday, 1.0, 4
                ),
            ]

            for run in runs:
                db.insert(run)

        yield db


def test_analytics_summary_empty_db(temp_db):
    """Test analytics summary with no runs."""
    summary = get_analytics_summary()

    assert isinstance(summary, AnalyticsSummary)
    assert summary.total_runs == 0
    assert summary.success_rate == 0.0
    assert summary.avg_duration_ms == 0.0
    assert summary.runs_today == 0


def test_analytics_summary_with_data(populated_db):
    """Test analytics summary with sample data."""
    summary = get_analytics_summary()

    assert isinstance(summary, AnalyticsSummary)
    assert summary.total_runs == 4
    # 3 passed, 1 failed -> 75% success rate
    assert summary.success_rate == 75.0
    # Avg duration: (1.5 + 0.5 + 2.0 + 1.0) / 4 = 1.25s = 1250ms
    assert summary.avg_duration_ms == 1250.0
    # 2 runs today
    assert summary.runs_today == 2


def test_runs_by_day_empty_db(temp_db):
    """Test runs by day with no data."""
    results = get_runs_by_day(days=30)

    assert isinstance(results, list)
    assert len(results) == 0


def test_runs_by_day_with_data(populated_db):
    """Test runs by day with sample data."""
    results = get_runs_by_day(days=30)

    assert isinstance(results, list)
    # Should have 2 days of data (today and yesterday)
    assert len(results) == 2

    # Results should be sorted by date ascending
    for result in results:
        assert isinstance(result, RunsByDay)
        assert result.total > 0


def test_runs_by_action_empty_db(temp_db):
    """Test runs by action with no data."""
    results = get_runs_by_action()

    assert isinstance(results, list)
    assert len(results) == 0


def test_runs_by_action_with_data(populated_db):
    """Test runs by action with sample data."""
    results = get_runs_by_action()

    assert isinstance(results, list)
    assert len(results) == 2

    for result in results:
        assert isinstance(result, RunsByAction)
        assert result.action_name in ["test_action_1", "test_action_2"]
        assert result.package_name == "test-package"
        assert result.total > 0


def test_analytics_summary_dataclass():
    """Test AnalyticsSummary dataclass creation."""
    summary = AnalyticsSummary(
        total_runs=100,
        success_rate=95.5,
        avg_duration_ms=500.0,
        runs_today=10,
    )
    assert summary.total_runs == 100
    assert summary.success_rate == 95.5
    assert summary.avg_duration_ms == 500.0
    assert summary.runs_today == 10


def test_runs_by_day_dataclass():
    """Test RunsByDay dataclass creation."""
    run = RunsByDay(
        date="2024-01-15",
        total=50,
        passed=45,
        failed=5,
    )
    assert run.date == "2024-01-15"
    assert run.total == 50
    assert run.passed == 45
    assert run.failed == 5


def test_runs_by_action_dataclass():
    """Test RunsByAction dataclass creation."""
    run = RunsByAction(
        action_name="my_action",
        package_name="my_package",
        total=100,
        passed=90,
        failed=10,
        avg_duration_ms=250.5,
    )
    assert run.action_name == "my_action"
    assert run.package_name == "my_package"
    assert run.total == 100
    assert run.passed == 90
    assert run.failed == 10
    assert run.avg_duration_ms == 250.5
