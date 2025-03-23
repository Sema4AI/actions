from pathlib import Path

import pytest

from sema4ai.action_server._selftest import ActionServerProcess
from sema4ai.action_server.migrations import MigrationStatus


@pytest.mark.integration_test
def test_automigrate(
    database_v0, datadir, action_server_process: ActionServerProcess, tmpdir
):
    import shutil

    from action_server_tests.fixtures import get_in_resources

    from sema4ai.action_server._database import Database
    from sema4ai.action_server._selftest import sema4ai_action_server_run
    from sema4ai.action_server.migrations import (
        CURRENT_VERSION,
        Migration,
        db_migration_status,
    )

    action_server_datadir = Path(str(tmpdir)) / ".sema4ai-test-action-server"
    action_server_datadir.mkdir(parents=True, exist_ok=True)

    db_path = database_v0
    target_db = action_server_datadir / "server.db"
    shutil.copy(db_path, target_db)

    assert db_migration_status(target_db) == MigrationStatus.NEEDS_MIGRATION
    root_dir = get_in_resources("no_conda", "greeter")
    sema4ai_action_server_run(
        [
            "import",
            f"--dir={root_dir}",
            "--db-file=server.db",
            "-v",
            "--datadir",
            action_server_datadir,
            "--skip-lint",
        ],
        returncode=0,
    )
    assert db_migration_status(target_db) == MigrationStatus.UP_TO_DATE

    # Simulate a newer version having written the db
    db = Database(target_db)
    with db.connect():
        with db.transaction():
            db.insert(Migration(id=CURRENT_VERSION + 1, name="dummy-test"))

    result = sema4ai_action_server_run(
        [
            "import",
            f"--dir={root_dir}",
            "--db-file=server.db",
            "-v",
            "--datadir",
            action_server_datadir,
            "--skip-lint",
        ],
        returncode=1,
    )
    assert "with a newer version of the" in result.stderr
