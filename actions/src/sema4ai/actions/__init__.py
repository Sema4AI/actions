"""Sema4.ai Actions enables running your AI actions in the Sema4.ai Action Server.

To use:

Mark actions with:

```
from sema4ai.actions import action

@action
def my_action():
    ...
```

And then go to a parent folder containing the action and serve them by 
running `action-server start`.

Note that it's also possible to programmatically run actions (without the Action
Server) with:

Run all the actions in a .py file:

  `python -m sema4ai.actions run <path_to_file>`

Run all the actions in files named *action*.py:

  `python -m sema4ai.actions run <directory>`

Run only actions with a given name:

  `python -m sema4ai.actions run <directory or file> -t <action_name>`

"""

from pathlib import Path
from typing import Callable, Optional, overload

from ._fixtures import setup, teardown
from ._protocols import IAction, Status
from ._request import Request
from ._response import ActionError, Response
from ._secret import OAuth2Secret, Secret

__version__ = "0.10.0"
version_info = [int(x) for x in __version__.split(".")]


@overload
def action(func: Callable) -> Callable:
    ...


@overload
def action(
    *, is_consequential: Optional[bool] = None, display_name: Optional[str] = None
) -> Callable:
    ...


def action(*args, **kwargs):
    """
    Decorator for actions (entry points) which can be executed by `sema4ai.actions`.

    i.e.:

    If a file such as actions.py has the contents below:

    ```python
    from sema4ai.actions import action

    @action
    def enter_user() -> str:
        ...
    ```

    It'll be executable by sema4ai actions as:

    python -m sema4ai.actions run actions.py -a enter_user

    Args:
        func: A function which is an action to `sema4ai.actions`.
        is_consequential: Whether the action is consequential or not.
            This will add `x-openai-isConsequential: true` to the action
            metadata and shown in OpenApi spec.
        display_name: A name to be displayed for this action.
            If given will be used as the openapi.json summary for this action.
    """

    def decorator(func, **kwargs):
        from sema4ai.actions import _hooks

        is_consequential = kwargs.pop("is_consequential", None)
        if is_consequential is not None:
            if not isinstance(is_consequential, bool):
                raise ValueError(
                    "Expected 'is_consequential' argument to be a boolean."
                )

        display_name = kwargs.pop("display_name", None)
        if display_name is not None:
            if not isinstance(display_name, str):
                raise ValueError("Expected 'display_name' argument to be a str.")

        if kwargs:
            raise ValueError(
                f"Arguments accepted by @action: ['is_consequential']. Received arguments: {list(kwargs.keys())}"
            )

        # When an action is found, register it in the framework as a target for execution.
        _hooks.on_action_func_found(
            func,
            options={
                "is_consequential": is_consequential,
                "display_name": display_name,
            },
        )

        return func

    if args and callable(args[0]):
        return decorator(args[0], **kwargs)

    return lambda func: decorator(func, **kwargs)


def session_cache(func):
    """
    Provides decorator which caches return and clears automatically when all
    actions have been run.

    A decorator which automatically cache the result of the given function and
    will return it on any new invocation until sema4ai-actions finishes running
    all actions.

    The function may be either a generator with a single yield (so, the first
    yielded value will be returned and when the cache is released the generator
    will be resumed) or a function returning some value.

    Args:
        func: wrapped function.
    """
    from sema4ai.actions._hooks import after_all_actions_run
    from sema4ai.actions._lifecycle import _cache

    return _cache(after_all_actions_run, func)


def action_cache(func):
    """
    Provides decorator which caches return and clears it automatically when the
    current action has been run.

    A decorator which automatically cache the result of the given function and
    will return it on any new invocation until sema4ai-actions finishes running
    the current action.

    The function may be either a generator with a single yield (so, the first
    yielded value will be returned and when the cache is released the generator
    will be resumed) or a function returning some value.

    Args:
        func: wrapped function.
    """
    from sema4ai.actions._hooks import after_action_run
    from sema4ai.actions._lifecycle import _cache

    return _cache(after_action_run, func)


def get_output_dir() -> Optional[Path]:
    """
    Provide the output directory being used for the run or None if there's no
    output dir configured.
    """
    from sema4ai.actions._config import get_config

    config = get_config()
    if config is None:
        return None
    return config.output_dir


def get_current_action() -> Optional[IAction]:
    """
    Provides the action which is being currently run or None if not currently
    running an action.
    """
    from sema4ai.actions import _action

    return _action.get_current_action()


__all__ = [
    "ActionError",
    "IAction",
    "OAuth2Secret",
    "Request",
    "Response",
    "Secret",
    "Status",
    "action",
    "action_cache",
    "get_current_action",
    "get_output_dir",
    "session_cache",
    "setup",
    "teardown",
]
