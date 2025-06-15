"""
Sema4.ai MCP (Model Context Protocol) bindings for Python.

This package provides the concepts around MCP (such as tools, resources, and prompts),
but unlike other MCP packages, it can be run standalone (without being a real service).

Packages developed with sema4ai.mcp can run as an actual MCP server,
by loading it into the `Sema4.ai Action Server`, which loads this package
and provides the actual MCP server implementation.

This approach enables:
1. Automatic generation of the environment to run the server (the Action Server will
   read the related `package.yaml` and then run the tools/resources/prompts in the
   target environment, enabling multiple MCPs to have different environments).
2. Automated logging and execution tracking (i.e.: `robocorp.log` is used to automatically
   log the Python execution and the results of the tools/resources/prompts).
3. It's possible to inspect in the Action Server all the tools/resources/prompts calls made
   and inspect the details on the execution.
"""

from typing import Callable, overload

from sema4ai.actions._hooks import after_collect_actions as _after_collect_actions
from sema4ai.actions._protocols import IAction

from .types import ToolAnnotations

__version__ = "0.0.1"
version_info = [int(x) for x in __version__.split(".")]


def _validate_collected_actions(actions: list[IAction]):
    from sema4ai.actions._exceptions import ActionsCollectError

    from sema4ai.mcp._validate_prompt import _validate_prompt
    from sema4ai.mcp._validate_resource import _validate_resource

    errors = []
    for action in actions:
        kind = (action.options and action.options.get("kind")) or "unknown"
        if kind == "resource":
            errors.extend(_validate_resource(action))
        elif kind == "prompt":
            errors.extend(_validate_prompt(action))

    if errors:
        if len(errors) == 1:
            raise ActionsCollectError(errors[0])
        raise ActionsCollectError(
            f"Found {len(errors)} errors on collect:\n====\n" + "\n====\n".join(errors)
        )


_after_collect_actions.register(_validate_collected_actions)


@overload
def tool(func: Callable) -> Callable:
    ...


@overload
def tool(
    *,
    name: str | None = None,
    description: str | None = None,
    annotations: ToolAnnotations | None = None,
) -> Callable:
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


def resource(
    uri: str,
    *,
    name: str | None = None,
    description: str | None = None,
    mime_type: str = "text/plain",
    size: int | None = None,
) -> Callable:
    """
    Decorator for resources which provide data to the LLM.

    Resources may be simple or templates.
        Templates are resources with `{placeholder}` indications in the uri,
        according to RFC 6570.

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

    See: https://modelcontextprotocol.io/docs/concepts/resources

    Args:
        uri: The URI of the resource (may be a template or a simple resource).
        name: A human-readable name for this resource.
        description: A description of what this resource represents.
        mime_type: The MIME type of the resource.
        size: The size of the raw resource content, in bytes (i.e., before base64 encoding
            or any tokenization), if known.
            This can be used by Hosts to display file sizes and estimate context window usage.
    """

    def decorator(func):
        from sema4ai.actions import _hooks

        # When an action is found, register it in the framework as a target for execution.
        _hooks.on_action_func_found(
            func,
            options={
                "uri": uri,
                "kind": "resource",
                "name": name,
                "description": description,
                "mime_type": mime_type,
                "size": size,
            },
        )

        return func

    # This one always requires arguments and thus users must always do:
    # @resource(uri, ...)
    return lambda func: decorator(func)


@overload
def prompt(func: Callable) -> Callable:
    ...


@overload
def prompt() -> Callable:
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
    """

    def decorator(func):
        from sema4ai.actions import _hooks

        _hooks.on_action_func_found(
            func,
            options={
                "kind": "prompt",
            },
        )

        return func

    if args and callable(args[0]):
        return decorator(args[0], **kwargs)

    return lambda func: decorator(func, **kwargs)


__all__ = [
    "tool",
    "resource",
    "prompt",
]
