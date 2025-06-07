from pathlib import Path
from typing import Any, Callable, Optional, overload

__version__ = "0.0.1"
version_info = [int(x) for x in __version__.split(".")]


@overload
def tool(func: Callable) -> Callable:
    ...


@overload
def tool(*, display_name: Optional[str] = None) -> Callable:
    ...


def tool(*args, **kwargs):
    """
    Decorator for tools which can be used by AI agents to perform actions.

    Example:
        ```python
        from sema4ai.mcp import tool

        @tool
        def assign_ticket(ticket_id: str, user_id: str) -> bool:
            \"\"\"
            Assign a ticket to a user.

            Args:
                ticket_id: The ID of the ticket to assign.
                user_id: The ID of the user to assign the ticket to.

            Returns:
                True if the ticket was assigned successfully, False otherwise.
            \"\"\"
            ...
            return True
        ```

    Note that a tool needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a assign_ticket

    Args:
        func: A function which is a tool to `sema4ai.mcp`.
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
def resource(*, display_name: Optional[str] = None) -> Callable:
    ...


def resource(*args, **kwargs):
    """
    Decorator for resources which provide data to the LLM.

    Example:
        ```python
        from sema4ai.mcp import resource

        @resource("tickets://{ticket_id}")
        def get_ticket(ticket_id: str) -> dict[str, str]:
            \"\"\"
            Get ticket information from the database.

            Args:
                ticket_id: The ID of the ticket to get information for.

            Returns:
                A dictionary containing the ticket information.
            \"\"\"
            return {"id": ticket_id, "summary": "This is a test ticket"}
        ```

    Note that a resource needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a get_ticket

    Args:
        func: A function which is a resource to `sema4ai.mcp`.
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
def prompt(*, display_name: Optional[str] = None) -> Callable:
    ...


def prompt(*args, **kwargs):
    """
    Decorator for functions that generate prompts for the LLM.

    Example:
        ```python
        from sema4ai.mcp import prompt

        @prompt
        def make_a_summary(text: str) -> str:
            \"\"\"
            Provide a prompt to the LLM.
            \"\"\"
            return "Please make a summary of the following text: {text}"
        ```

    Note that a prompt needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a make_a_summary

    Args:
        func: A function which is a prompt to `sema4ai.mcp`.
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
