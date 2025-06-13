# Sema4AI Model Context Protocol (MCP)

The Model Context Protocol (MCP) is a protocol that AI agents can use to take action based on the output of a conversation with an LLM. This package provides the necessary tools and decorators to implement MCP in your AI applications.

It works a bit different from other MCP implementations in that the idea is that you'll just worry
about the MCP tool/resource/prompt functions, but the actual management of the connection and lifecycle
of your tool/resource/prompt functions is handled by the `Sema4AI Action Server`.

This means that you should just focus on the MCP functions, not on running the server, making logging (which is automatically setup using `robocorp.log`), creating your python environment or handling connections here.

Using the `Sema4ai VSCode Extension`, enables you to easily run your MCP functions locally and later on (if you choose to easily deploy your MCP server and agents to the cloud by using `Sema4AI` -- or just use the `Sema4AI Action Server` in a private cloud or locally as well, no vendor lock-in).

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

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
