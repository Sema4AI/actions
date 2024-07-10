from sema4ai.action_server._database import Database
from sema4ai.action_server.migrations import Migration


def migrate(db: Database) -> None:
    from sema4ai.action_server.migrations import MIGRATION_ID_TO_NAME

    sqls = [
        "CREATE INDEX action_action_package_id_non_unique_index ON action(action_package_id);",
        "CREATE INDEX run_status_non_unique_index ON run(status);",
        "CREATE INDEX run_action_id_non_unique_index ON run(action_id);",
        """
CREATE TABLE IF NOT EXISTS user_session(
    id TEXT NOT NULL PRIMARY KEY,
    created_at TEXT NOT NULL,
    accessed_at TEXT NOT NULL,
    external INTEGER CHECK(external IN (0, 1)) NOT NULL  
)
""",
        """
CREATE UNIQUE INDEX user_session_id_index ON user_session(id);
""",
        """
CREATE INDEX user_session_external_non_unique_index ON user_session(external);
""",
        """
CREATE TABLE IF NOT EXISTS temp_user_session_data(
    user_session_id TEXT NOT NULL,
    key TEXT NOT NULL,
    data TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_session_id) REFERENCES user_session(id)  
)
""",
        """
CREATE INDEX temp_user_session_data_user_session_id_non_unique_index ON temp_user_session_data(user_session_id);
""",
        """
CREATE INDEX temp_user_session_data_key_non_unique_index ON temp_user_session_data(key);
""",
        """
CREATE TABLE IF NOT EXISTS o_auth2_user_data(
    user_session_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    access_token TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    token_type TEXT NOT NULL,
    scopes TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT ''
)
""",
    ]
    for sql in sqls:
        db.execute(sql)

    db.insert(Migration(id=6, name=MIGRATION_ID_TO_NAME[6]))
