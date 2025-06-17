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
    title: str | None = None,
    read_only_hint: bool = False,
    destructive_hint: bool = True,
    idempotent_hint: bool = False,
    open_world_hint: bool = True,
) -> Callable:
    """
    Decorator for tools which can be used by AI agents to perform actions.

    Args:
        title: A human-readable title for the tool.

        read_only_hint: If true, the tool does not modify its environment (default: False).

        destructive_hint: If true, the tool may perform destructive updates to its environment (default: True).

        idempotent_hint: If true, calling the tool repeatedly with the same arguments
            will have no additional effect on the its environment (default: False).

        open_world_hint: If true, this tool may interact with an "open world" of external
            entities (default: True).

            If False, the tool's domain of interaction is closed.
            For example, the world of a web search tool is open, whereas that
            of a memory tool is not.
    """


def tool(*args, **kwargs):
    """
    Decorator for tools which can be used by AI agents to perform actions.

    Args:
        title: A human-readable title for the tool.

        read_only_hint: If true, the tool does not modify its environment (default: False).

        destructive_hint: If true, the tool may perform destructive updates to its environment (default: True).

        idempotent_hint: If true, calling the tool repeatedly with the same arguments
            will have no additional effect on the its environment (default: False).

        open_world_hint: If true, this tool may interact with an "open world" of external
            entities (default: True).

            If False, the tool's domain of interaction is closed.
            For example, the world of a web search tool is open, whereas that
            of a memory tool is not.

    Example:
        ```python
        from sema4ai.mcp import tool

        @tool
        def assign_ticket(ticket_id: str, user_id: str) -> bool:
            '''
            Assign a ticket to a user.

            Args:
                ticket_id: The ID of the ticket to assign.
                user_id: The ID of the user to assign the ticket to.

            Returns:
                True if the ticket was assigned successfully, False otherwise.
            '''
            ...
            return True
        ```

    Note that a tool needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a assign_ticket
    """

    def decorator(func, **kwargs):
        from sema4ai.actions import _hooks

        title = kwargs.pop("title", None)
        if title is not None:
            if not isinstance(title, str):
                raise ValueError("Expected 'title' argument to be a str.")

        read_only_hint = kwargs.pop("read_only_hint", False)
        if not isinstance(read_only_hint, bool):
            raise ValueError("Expected 'read_only_hint' argument to be a bool.")

        destructive_hint = kwargs.pop("destructive_hint", True)
        if not isinstance(destructive_hint, bool):
            raise ValueError("Expected 'destructive_hint' argument to be a bool.")

        idempotent_hint = kwargs.pop("idempotent_hint", False)
        if not isinstance(idempotent_hint, bool):
            raise ValueError("Expected 'idempotent_hint' argument to be a bool.")

        open_world_hint = kwargs.pop("open_world_hint", True)
        if not isinstance(open_world_hint, bool):
            raise ValueError("Expected 'open_world_hint' argument to be a bool.")

        if kwargs:
            raise ValueError(
                f"Arguments accepted by @tool: ['name', 'title', 'read_only_hint', 'destructive_hint', 'idempotent_hint', 'open_world_hint']. Received arguments: {list(kwargs.keys())}"
            )

        # When an action is found, register it in the framework as a target for execution.
        # The tool schema in MCP requires:
        # - name (from the func name or passed as argument),
        # - description (always from the function docstring),
        _hooks.on_action_func_found(
            func,
            options={
                "title": title,
                "read_only_hint": read_only_hint,
                "destructive_hint": destructive_hint,
                "idempotent_hint": idempotent_hint,
                "open_world_hint": open_world_hint,
                "kind": "tool",
            },
        )

        return func

    if args and callable(args[0]):
        return decorator(args[0], **kwargs)

    return lambda func: decorator(func, **kwargs)


@overload
def resource(func: Callable) -> Callable:
    ...


@overload
def resource(
    uri: str = "",
    *,
    mime_type: str | None = None,
    size: int | None = None,
) -> Callable:
    ...


def resource(*args, **kwargs) -> Callable:
    """
    Decorator for resources which provide data to the LLM.

    Resources may be simple or templates.
        Templates are resources with `{placeholder}` indications in the uri, according to RFC 6570.

    Args:
        uri: The URI of the resource (may be a template or a simple resource).
            If not provided, a uri such as `resource://read/<function_name>/{arg_name1}/{arg_name2}` will
            be created automatically (arguments are optional).
        mime_type: The MIME type of the resource. If not provided, it's based on the type of the result
            (if it's a string, it's `text/plain`, if it's a bytes, it's `application/octet-stream`, if it's
            another type dict, it's converted to json and then `application/json` is used as the mime type).
        size: The size of the raw resource content, in bytes (i.e., before base64 encoding
            or any tokenization), if known.
            This can be used by Hosts to display file sizes and estimate context window usage.

    Note: the name is the name of the function and the description is gotten from the docstring.

    If called without any argument, an automatic uri is created based on the function name and arguments
    with the following format: `resource://read/<function_name>/{arg_name1}/{arg_name2}`.

    Example:
        ```python
        from sema4ai.mcp import resource

        @resource("tickets://{ticket_id}")
        def get_ticket(ticket_id: str) -> dict[str, str]:
            '''
            Get ticket information from the database.

            Args:
                ticket_id: The ID of the ticket to get information for.

            Returns:
                A dictionary containing the ticket information.
            '''
            return {"id": ticket_id, "summary": "This is a test ticket"}
        ```

    Note that a resource needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a get_ticket

    See: https://modelcontextprotocol.io/docs/concepts/resources
    """

    def decorator(func, *args, **kwargs):
        import inspect

        from sema4ai.actions import _hooks

        if args:
            uri = args[0]
            if not isinstance(uri, str):
                raise ValueError("Expected 'uri' argument to be a str.")

            if len(args) > 1:
                raise ValueError(
                    "Expected only one argument (uri). Found: " + ", ".join(args)
                )
        else:
            uri = kwargs.pop("uri", "")

        if not uri:
            uri = f"resource://read/{func.__name__}"
            # Get the signature of the function
            signature = inspect.signature(func)
            for arg_name, arg in signature.parameters.items():
                if arg.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    uri += f"/{{{arg_name}}}"

        # If not specified, it's based on the type of the result
        mime_type = kwargs.pop("mime_type", None)
        size = kwargs.pop("size", None)

        if kwargs:
            raise ValueError(
                f"Arguments accepted by @resource: ['uri', 'mime_type', 'size']. Received arguments: {list(kwargs.keys())}"
            )

        # When an action is found, register it in the framework as a target for execution.
        _hooks.on_action_func_found(
            func,
            options={
                "uri": uri,
                "kind": "resource",
                "mime_type": mime_type,
                "size": size,
            },
        )

        return func

    if args and callable(args[0]):
        return decorator(args[0], *args[1:], **kwargs)

    return lambda func: decorator(func, *args, **kwargs)


@overload
def prompt(func: Callable) -> Callable:
    ...


@overload
def prompt() -> Callable:
    ...


def prompt(*args, **kwargs):
    """
    Decorator for functions that generate prompts for the LLM.

    No arguments are accepted by this decorator.

    The description of the prompt is gotten from the docstring.

    Note that each argument in the function signature is automatically added
    as a required argument in the prompt (the argument description is gotten
    from the `Args` in the docstring).

    Example:
        ```python
        from sema4ai.mcp import prompt

        @prompt
        def make_a_summary(text: str) -> str:
            '''
            Provide a prompt to the LLM.

            Args:
                text: The text to make a summary of.
            '''
            return "Please make a summary of the following text: {text}"
        ```

    Note that a prompt needs sema4ai actions to be executed.
    The command line to execute it is:

    python -m sema4ai.actions run actions.py -a make_a_summary
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
