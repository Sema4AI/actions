import typing
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

from pydantic.dataclasses import dataclass

from sema4ai.action_server._database import DBRules

if typing.TYPE_CHECKING:
    from sema4ai.action_server._database import Database


_db_rules = DBRules()


@dataclass
class ActionPackage:  # Table name: action_package
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("ActionPackage.id")

    name: str  # The name for the action package
    _db_rules.unique_indexes.add("ActionPackage.name")

    # The directory where the action package is (may be stored relative
    # to the datadir or as an absolute path).
    # When relative starts with `./`, otherwise it's absolute.
    directory: str

    # The sha256 hash of the package.yaml (based only on the actual content
    # not considering spaces and comments).
    conda_hash: str

    # The environment to be used for launches (as json).
    env_json: str


@dataclass
class Action:  # Table name: action
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("Action.id")

    action_package_id: str  # foreign key to the action package
    _db_rules.foreign_keys.add("Action.action_package_id")
    _db_rules.indexes.add("Action.action_package_id")

    name: str  # The action name
    docs: str  # Docs for the action

    # File for the action (relative to the directory in the ActionPackage).
    file: str

    lineno: int  # Line for the action
    input_schema: str  # The json content for the schema input
    output_schema: str  # The json content for the schema output

    enabled: bool = True

    is_consequential: Optional[bool] = None

    # The json content for the managed params schema
    managed_params_schema: Optional[str] = None

    options: str = ""


RUN_ID_COUNTER = "run_id"
ALL_COUNTERS = (RUN_ID_COUNTER,)


@dataclass
class Counter:
    id: str  # primary key (counter name -- i.e.: RUN_ID_COUNTER)
    _db_rules.unique_indexes.add("Counter.id")

    value: int  # current value


@dataclass
class Run:
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("Run.id")

    status: int  # 0=not run, 1=running, 2=passed, 3=failed, 4=cancelled
    _db_rules.indexes.add("Run.status")

    action_id: str  # foreign key to the action
    _db_rules.foreign_keys.add("Run.action_id")
    _db_rules.indexes.add("Run.action_id")

    start_time: str  # The time that the action started running (empty means it hasn't started yet).
    # The time to run the action (in seconds).
    # Does not include the time the run spent queued waiting for the
    # process to be available.
    run_time: Optional[float]
    inputs: str  # The json content with the variables used as an input
    result: Optional[str]  # The json content of the output that the run generated
    error_message: Optional[str]  # If the status=failed, this may have an error message

    # The path (relative to the datadir) of the artifacts generated in the run
    relative_artifacts_dir: str

    # We could've made this the primary key, but in theory when (if)
    # we ever have workspaces then this id would need to be scoped to the
    # workspace while the other one would be global.
    numbered_id: int
    _db_rules.unique_indexes.add("Run.numbered_id")

    # The request id that this run is associated with (if any).
    request_id: str = ""
    _db_rules.indexes.add("Run.request_id")


@dataclass
class UserSession:
    id: str  # primary key (uuid)
    _db_rules.unique_indexes.add("UserSession.id")

    created_at: str  # date in isoformat
    accessed_at: str  # date in isoformat

    external: bool  # Determines if it was requested to be created internally (automatically) or externally
    _db_rules.indexes.add("UserSession.external")


@dataclass
class TempUserSessionData:
    user_session_id: str  # foreign key (uuid)
    _db_rules.foreign_keys.add("TempUserSessionData.user_session_id")
    _db_rules.indexes.add("TempUserSessionData.user_session_id")

    key: str
    _db_rules.indexes.add("TempUserSessionData.key")

    data: str  # A json-blob of data
    expires_at: str  # date in isoformat


@dataclass
class OAuth2UserData:
    user_session_id: str  # foreign key (uuid)
    _db_rules.foreign_keys.add("OAuth2.user_session_id")
    _db_rules.indexes.add("OAuth2.user_session_id")

    provider: str
    _db_rules.indexes.add("OAuth2.provider")

    refresh_token: str  # Data encrypted with storage key
    access_token: str  # Data encrypted with storage key

    # date in isoformat or an
    # empty string if not available
    expires_at: str

    token_type: str

    # Actually a json-blob of list[str] or an
    # empty string if it is not available.
    scopes: str

    # May be used to add metadata obtained from the OAuth2 flow into the
    # model (for data which is not available in the above info already).
    metadata: str = ""

    # The code verifier is needed for pkce (authentication without a clientSecret).
    code_verifier: str = ""  # Data encrypted with storage key


class RunStatus:
    NOT_RUN = 0
    RUNNING = 1
    PASSED = 2
    FAILED = 3
    CANCELLED = 4


def run_status_to_str(run_status: int) -> str:
    """
    Args:
        run_status: The run status to convert to a string.

    Returns:
        The string representation of the run status.
    """
    if run_status == RunStatus.NOT_RUN:
        return "not run"
    elif run_status == RunStatus.RUNNING:
        return "running"
    elif run_status == RunStatus.PASSED:
        return "passed"
    elif run_status == RunStatus.FAILED:
        return "failed"
    elif run_status == RunStatus.CANCELLED:
        return "cancelled"
    else:
        raise ValueError(f"Invalid run status: {run_status}")


def get_all_model_classes():
    from sema4ai.action_server.migrations import Migration

    return [
        Migration,
        ActionPackage,
        Action,
        Run,
        Counter,
        UserSession,
        TempUserSessionData,
        OAuth2UserData,
    ]


def get_model_db_rules() -> DBRules:
    return _db_rules


_global_db: Optional["Database"] = None


@contextmanager
def load_db(db_path: Union[Path, str]) -> Iterator["Database"]:
    """
    Loads the database from the given path and initializes the internal
    models, besides setting this db as the global db for the duration
    of the context manager.
    """
    from sema4ai.action_server._database import Database

    global _global_db

    if _global_db is not None:
        raise AssertionError("There is already a global initialized database.")

    db = Database(db_path)
    with db.connect():
        db.initialize(get_all_model_classes())
        _global_db = db
        try:
            yield db
        finally:
            _global_db = None


@contextmanager
def create_db(db_path: Union[Path, str]) -> Iterator["Database"]:
    """
    Creates the database and sets this db as the global db for the duration
    of the context manager.
    """
    from sema4ai.action_server.migrations import (
        CURRENT_VERSION,
        MIGRATION_ID_TO_NAME,
        Migration,
    )

    with load_db(db_path) as db:
        with db.transaction():
            db.create_tables(get_model_db_rules())
            current_migration = MIGRATION_ID_TO_NAME[CURRENT_VERSION]
            db.insert(Migration(CURRENT_VERSION, current_migration))
            for counter in ALL_COUNTERS:
                db.insert(Counter(counter, 0))
        yield db


class DBNotInitializedError(AssertionError):
    pass


def get_db() -> "Database":
    if _global_db is None:
        raise DBNotInitializedError("DB not initialized")
    return _global_db


def get_action_package_from_action(action: Action) -> ActionPackage:
    db = get_db()
    return db.first(
        ActionPackage,
        "SELECT * FROM action_package WHERE id = ?",
        [action.action_package_id],
    )
