from pathlib import Path

import pytest


@pytest.mark.integration_test
def test_datadir_related_actions(
    tmpdir,
    action_server_datadir: Path,
) -> None:
    from action_server_tests.fixtures import sema4ai_action_server_run

    from sema4ai.action_server._database import Database
    from sema4ai.action_server._models import Action, load_db

    action_server_datadir.mkdir(parents=True, exist_ok=True)
    db_path = action_server_datadir / "server.db"
    assert not db_path.exists()

    calculator = Path(tmpdir) / "v1" / "calculator" / "action_calculator.py"
    calculator.parent.mkdir(parents=True, exist_ok=True)
    calculator.write_text(
        """
from sema4ai.actions import action

@action
def calculator_sum(v1: float, v2: float) -> float:
    return v1 + v2
    
@action
def calculator_subtract(v1: float, v2: float) -> float:
    return v1 - v2
"""
    )

    def import_action(action_name: str) -> None:
        sema4ai_action_server_run(
            [
                "import",
                f"--dir={calculator.parent}",
                "--db-file=server.db",
                "-v",
                "--skip-lint",
                "--datadir",
                action_server_datadir,
                "--whitelist",
                action_name,
            ],
            returncode=0,
        )

    def clear_actions() -> None:
        sema4ai_action_server_run(
            [
                "datadir",
                "clear-actions",
                "--datadir",
                action_server_datadir,
                "--db-file=server.db",
            ],
            returncode=0,
        )

    import_action("calculator_sum")

    def check_actions_enabled(enabled_count: int, total_count: int) -> None:
        db: Database
        with load_db(db_path) as db:
            with db.connect():
                actions = db.all(Action)
                assert (
                    len([action for action in actions if action.enabled])
                    == enabled_count
                )
                assert len(actions) == total_count

    check_actions_enabled(1, 1)

    import_action("calculator_subtract")

    check_actions_enabled(2, 2)

    # Re-importing the same action should not add a new action.
    import_action("calculator_subtract")

    check_actions_enabled(2, 2)

    clear_actions()

    check_actions_enabled(0, 2)

    import_action("calculator_subtract")

    check_actions_enabled(1, 2)
