from sema4ai.action_server._database import Database
from sema4ai.action_server.migrations import Migration


def migrate(db: Database) -> None:
    from sema4ai.action_server.migrations import MIGRATION_ID_TO_NAME

    sqls = [
        """
ALTER TABLE run ADD COLUMN run_type TEXT NOT NULL DEFAULT 'action';
""",
        """
ALTER TABLE run ADD COLUMN robot_package_path TEXT DEFAULT NULL;
""",
        """
ALTER TABLE run ADD COLUMN robot_task_name TEXT DEFAULT NULL;
""",
        """
ALTER TABLE run ADD COLUMN robot_env_hash TEXT DEFAULT '';
""",
        """
ALTER TABLE run ADD COLUMN stdout TEXT DEFAULT NULL;
""",
        """
ALTER TABLE run ADD COLUMN stderr TEXT DEFAULT NULL;
""",
    ]
    for sql in sqls:
        db.execute(sql)

    db.insert(Migration(id=9, name=MIGRATION_ID_TO_NAME[9]))
