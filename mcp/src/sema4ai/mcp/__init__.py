from pathlib import Path
from typing import Any, Callable, Optional, overload

__version__ = "0.1.0"
version_info = [int(x) for x in __version__.split(".")]


@overload
def tool(func: Callable) -> Callable:
    ...


@overload
def tool(
    *, is_consequential: Optional[bool] = None, display_name: Optional[str] = None
) -> Callable:
    ...


def tool(*args, **kwargs):
    """
    Decorator for tools which can be executed by `sema4ai.actions`.

    i.e.:

    If a file such as actions.py has the contents below:

    ```python
    from sema4ai.mcp import tool

    @tool
    def execute_tool(param1: str, param2: int) -> dict:
        ...
    ```

    Note that a tool needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a execute_tool

    Args:
        func: A function which is a tool to `sema4ai.mcp`.
        is_consequential: Whether the action is consequential or not.
            This will add `x-openai-isConsequential: true` to the action
            metadata and shown in OpenApi spec.
        display_name: A name to be displayed for this action.
            If given will be used as the openapi.json summary for this action.
    """
    from sema4ai.actions import action

    kwargs["kind"] = "tool"
    return action(*args, **kwargs)


@overload
def resource(func: Callable) -> Callable:
    ...


@overload
def resource(
    *, is_consequential: Optional[bool] = None, display_name: Optional[str] = None
) -> Callable:
    ...


def resource(*args, **kwargs):
    """
    Decorator for resources which can be executed by `sema4ai.actions`.

    i.e.:

    If a file such as actions.py has the contents below:

    ```python
    from sema4ai.mcp import resource

    @resource
    def manage_resource(param1: str, param2: int) -> dict:
        ...
    ```

    Note that a resource needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a manage_resource

    Args:
        func: A function which is a resource to `sema4ai.mcp`.
        is_consequential: Whether the action is consequential or not.
            This will add `x-openai-isConsequential: true` to the action
            metadata and shown in OpenApi spec.
        display_name: A name to be displayed for this action.
            If given will be used as the openapi.json summary for this action.
    """
    from sema4ai.actions import action

    kwargs["kind"] = "resource"
    return action(*args, **kwargs)


@overload
def prompt(func: Callable) -> Callable:
    ...


@overload
def prompt(
    *, is_consequential: Optional[bool] = None, display_name: Optional[str] = None
) -> Callable:
    ...


def prompt(*args, **kwargs):
    """
    Decorator for prompts which can be executed by `sema4ai.actions`.

    i.e.:

    If a file such as actions.py has the contents below:

    ```python
    from sema4ai.mcp import prompt

    @prompt
    def generate_prompt(param1: str, param2: int) -> str:
        ...
    ```

    Note that a prompt needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a generate_prompt

    Args:
        func: A function which is a prompt to `sema4ai.mcp`.
        is_consequential: Whether the action is consequential or not.
            This will add `x-openai-isConsequential: true` to the action
            metadata and shown in OpenApi spec.
        display_name: A name to be displayed for this action.
            If given will be used as the openapi.json summary for this action.
    """
    from sema4ai.actions import action

    kwargs["kind"] = "prompt"
    return action(*args, **kwargs)


__all__ = [
    "tool",
    "resource",
    "prompt",
]
