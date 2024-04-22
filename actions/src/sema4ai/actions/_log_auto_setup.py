from contextlib import contextmanager
from typing import Optional

from robocorp import log

from sema4ai.actions._protocols import IAction


def _log_before_action_run(action: IAction):
    log.start_task(
        action.name,
        action.module_name,
        action.filename,
        action.method.__code__.co_firstlineno + 1,
        getattr(action.method, "__doc__", ""),
    )


def _log_after_action_run(action: IAction):
    status = action.status
    log.end_task(action.name, action.module_name, status, action.message)


@contextmanager
def setup_cli_auto_logging(config: Optional[log.AutoLogConfigBase]):
    # This needs to be called before importing code which needs to show in the log
    # (user or library).

    from sema4ai.actions._hooks import after_action_run, before_action_run

    with log.setup_auto_logging(config):
        with before_action_run.register(
            _log_before_action_run
        ), after_action_run.register(_log_after_action_run):
            try:
                yield
            finally:
                log.close_log_outputs()
