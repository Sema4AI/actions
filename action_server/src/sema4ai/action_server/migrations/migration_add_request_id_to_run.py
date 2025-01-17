from sema4ai.action_server._database import Database
from sema4ai.action_server.migrations import Migration


def migrate(db: Database) -> None:
    from sema4ai.action_server.migrations import MIGRATION_ID_TO_NAME

    sqls = [
        """
ALTER TABLE run ADD COLUMN request_id TEXT NOT NULL DEFAULT '';
""",
        """
CREATE INDEX run_request_id_non_unique_index ON run(request_id);
""",
    ]
    for sql in sqls:
        db.execute(sql)

    db.insert(Migration(id=8, name=MIGRATION_ID_TO_NAME[8]))
