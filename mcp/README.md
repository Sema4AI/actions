# Sema4AI Model Context Protocol (MCP) Library

The Model Context Protocol (MCP) is a protocol that AI agents can use to take action based
on the output of a conversation with an LLM. This library provides an API that allows you
to implement MCP tools, resources and prompts in your Python code.

It works a bit different from other MCP implementations in that the idea is that you'll just worry
about the MCP tool/resource/prompt implementation in Python, but the actual management of the connection
and lifecycle of your tool/resource/prompt functions is handled by the `Sema4AI Action Server`.

This means that you should just focus on the MCP functions, NOT on features provided by the `Sema4AI Action Server` such as:

- Running the server
- Making logging (which is automatically setup using `robocorp.log`)
- Creating your python environment (the environment is managed by a `package.yaml` file that's expected to be in the root of your project)
- Handling connections
- Providing a separate REST API to call your MCP functions (the regular REST API provided for actions in the `Sema4AI Action Server` may also be used to call your MCP functions)

Developing MCP functions:

Using the `Sema4ai VSCode Extension`, enables you to easily run your MCP functions locally and later on deploy as you'd like
-- you can easily deploy your MCP server and agents to the cloud by using `Sema4AI` -- or just use the `Sema4AI Action Server` in a private cloud or locally as well.

## Installation

```bash
pip install sema4ai-mcp
```

## Usage

The package provides three main decorators:

### @tool

Use the `@tool` decorator to define functions that can be used as tools by AI agents:

```python
from sema4ai.mcp import tool

@tool
def assign_ticket(ticket_id: str, user_id: str) -> bool:
    """
    Assign a ticket to a user.

    Args:
        ticket_id: The ID of the ticket to assign.
        user_id: The ID of the user to assign the ticket to.

    Returns:
        True if the ticket was assigned successfully, False otherwise.
    """
    ...
    return True
```

The `@tool` decorator can also be used with the following arguments:

- `title`: A human-readable title for the tool.
- `read_only_hint`: If true, the tool does not modify its environment (default: False).
- `destructive_hint`: If true, the tool may perform destructive updates to its environment (default: True).
- `idempotent_hint`: If true, calling the tool repeatedly with the same arguments
  will have no additional effect on the its environment (default: False).
- `open_world_hint`: If true, this tool may interact with an "open world" of external
  entities (default: True).
  If False, the tool's domain of interaction is closed.
  For example, the world of a web search tool is open, whereas that
  of a memory tool is not.

### @resource

Use the `@resource` decorator to define functions that provide resources to the LLM:

```python
from sema4ai.mcp import resource

@resource("tickets://{ticket_id}")
def get_ticket(ticket_id: str) -> dict[str, str]:
    """
    Get ticket information from the database.

    Args:
        ticket_id: The ID of the ticket to get information for.

    Returns:
        A dictionary containing the ticket information.
    """
    return {"id": ticket_id, "summary": "This is a test ticket"}
```

### @prompt

Use the `@prompt` decorator to define functions that generate prompts.

```python
from sema4ai.mcp import prompt

@prompt
def make_a_summary(text: str) -> str:
    """
    Provide a prompt to the LLM.
    """
    return "Please make a summary of the following text: {text}"
```

## License

This project is licensed under the `Apache License 2.0`.
