import os
from logging import getLogger

from sema4ai.actions._callback import Callback
from sema4ai.actions._protocols import (
    IAfterActionRunCallback,
    IAfterAllActionsRunCallback,
    IBeforeActionRunCallback,
    IBeforeAllActionsRunCallback,
    IBeforeCollectActionsCallback,
    IOnActionFuncFoundCallback,
)

logger = getLogger(__name__)


class SessionCallback(Callback):
    def __init__(self, skip_env_name, skip_always, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._called_already = set()
        self._skip_env_name = skip_env_name
        self._skip_always = skip_always

    def unregister(self, callback):
        self._called_already.discard(callback)
        super().unregister(callback)

    def __call__(self, *args, **kwargs):
        if self._reversed:
            iter_in = reversed(self._callbacks)
        else:
            iter_in = self._callbacks

        skip = os.environ.get(self._skip_env_name, "") in ("true", "1")

        if skip and self._skip_always:
            return

        for c in iter_in:
            if skip and c in self._called_already:
                continue
            self._called_already.add(c)

            try:
                c(*args, **kwargs)
            except Exception:
                logger.exception(f"Error calling: {c}.")
                if self.raise_exceptions:
                    raise


# Called as on_action_func_found(action: IAction)
on_action_func_found: IOnActionFuncFoundCallback = Callback(raise_exceptions=True)

# Called as before_collect_actions(path: Path, action_names: Set[str])
before_collect_actions: IBeforeCollectActionsCallback = Callback()

# Called as before_all_actions_run(actions: List[IAction])
before_all_actions_run: IBeforeAllActionsRunCallback = SessionCallback(
    "S4_ACTIONS_SKIP_SESSION_SETUP", False, raise_exceptions=True
)

# Called as before_action_run(action: IAction)
before_action_run: IBeforeActionRunCallback = Callback(raise_exceptions=True)

# Called as after_action_run(action: IAction)
# Note that this one is done in reversed registry order (as is usually
# expected from tear-downs).
after_action_run: IAfterActionRunCallback = Callback(reversed=True)

# Called as after_all_actions_run(actions: List[IAction])
# Note that this one is done in reversed registry order (as is usually
# expected from tear-downs).
after_all_actions_run: IAfterAllActionsRunCallback = SessionCallback(
    "S4_ACTIONS_SKIP_SESSION_TEARDOWN", True, reversed=True
)
