"""
Note: this is easy while we're in a single process!

If we ever change the design to support multiple processes we'd need to have a
way to synchronize state across multiple processes.
"""
import threading
import typing
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Dict, Literal, Optional

if typing.TYPE_CHECKING:
    from ._database import Database
    from ._models import Run


@dataclass(slots=True)
class RunChangeEvent:
    ev: Literal["added", "changed"]
    run: "Run"
    changes: Optional[dict[str, Any]] = None


class RunRuntimeInfo:
    def __init__(self, run_id: str):
        from sema4ai.action_server._robo_utils.callback import Callback

        self._run_id = run_id
        self._canceled = False
        self.on_cancel = Callback()

    def cancel(self):
        self._canceled = True
        self.on_cancel()  # Notify all listeners that the run was canceled.

    def is_canceled(self) -> bool:
        return self._canceled


class RunsState:
    def __init__(self, db: "Database"):
        # Clients that want to register/unregister must use this semaphore
        # to avoid racing conditions.
        #
        # This is done because the expected scenario is the following:
        # 1. The client acquires this semaphore
        # 2. then notifies about existing
        # 3. then registers so that it knows about new runs in the structure
        #
        # In this case, if the client doesn't hold the semaphore himself we
        # could have a racing condition.
        #
        # We could make it an RLock, but then we'd need a wrapper to do the
        # verification on whether it's acquired, so, we use a Semaphore to
        # use the `_value` to do the needed asserts.
        self.semaphore = threading.Semaphore(1)

        # Use dict keys for uniqueness and ordering.
        self._run_listeners: Dict[Any, int] = {}

        self._db = db
        self._run_id_to_runtime_info: dict[str, RunRuntimeInfo] = {}

    def get_current_run_state(self, offset: int = 0, limit: int = 200) -> list["Run"]:
        from ._models import Run

        assert (
            self.semaphore._value == 0
        ), "Clients getting the current run state must acquire the semaphore."
        return self._db.all(
            Run, offset=offset, limit=limit, order_by="numbered_id DESC"
        )

    def get_run_from_id(self, run_id: str) -> "Run":
        """
        Returns the run associated with the run id (or throws a KeyError if not found).
        """
        assert run_id, "Run id cannot be empty."
        from ._database import Database
        from ._models import Run

        assert (
            self.semaphore._value == 0
        ), "Clients getting the current run state must acquire the semaphore."
        db: Database = self._db

        with db.connect():
            return db.first(Run, "SELECT * FROM run WHERE id = ?", [run_id])

    def get_run_from_request_id(self, request_id: str) -> "Run":
        """
        Returns the run associated with the request id (or throws a KeyError if not found).
        """
        assert request_id, "Request id cannot be empty."
        from ._database import Database
        from ._models import Run

        assert (
            self.semaphore._value == 0
        ), "Clients getting the current run state must acquire the semaphore."
        db: Database = self._db

        with db.connect():
            return db.first(Run, "SELECT * FROM run WHERE request_id = ?", [request_id])

    def register(self, listener):
        assert (
            self.semaphore._value == 0
        ), "Clients registering must acquire the semaphore."
        self._run_listeners[listener] = 1

    def unregister(self, listener):
        assert (
            self.semaphore._value == 0
        ), "Clients unregistering must acquire the semaphore."
        self._run_listeners.pop(listener, None)

    def on_run_inserted(self, run: "Run"):
        # Semaphore is acquired internally in this case.
        from ._models import Run

        run_copy = Run(**asdict(run))
        with self.semaphore:
            for listener in self._run_listeners.keys():
                listener(RunChangeEvent("added", run_copy))

    def create_run_runtime_info(self, run_id: str) -> RunRuntimeInfo:
        """
        Creates the runtime info for a run and returns it.
        """
        runtime_info = RunRuntimeInfo(run_id)
        assert run_id not in self._run_id_to_runtime_info
        self._run_id_to_runtime_info[run_id] = runtime_info
        return runtime_info

    def on_run_changed(self, run: "Run", changes: Dict[str, Any]):
        from sema4ai.action_server._models import RunStatus

        # Semaphore is acquired internally in this case.
        from ._models import Run

        run_copy = Run(**asdict(run))
        with self.semaphore:
            for listener in self._run_listeners.keys():
                listener(RunChangeEvent("changed", run_copy, changes))

            if run_copy.status not in (RunStatus.RUNNING, RunStatus.NOT_RUN):
                # Finished run, remove from runtime info.
                self._run_id_to_runtime_info.pop(run_copy.id, None)

    def cancel_run(self, run_id: str) -> bool:
        """
        Cancels a run.

        Args:
            run_id: The ID of the run to cancel.

        Returns:
            True if the run was canceled, False otherwise (if the run was not running).
        """

        with self.semaphore:
            runtime_info = self._run_id_to_runtime_info.get(run_id)
            if runtime_info is not None:
                runtime_info.cancel()
                return True
            return False


_runs_state: Optional[RunsState] = None


@contextmanager
def use_runs_state_ctx(db: "Database"):
    global _runs_state
    _runs_state = RunsState(db)
    try:
        yield _runs_state
    finally:
        pass
    _runs_state = None


def get_global_runs_state() -> RunsState:
    assert _runs_state
    return _runs_state
