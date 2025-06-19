<!-- markdownlint-disable -->

# module `sema4ai.mcp`

Sema4.ai MCP (Model Context Protocol) bindings for Python.

This package provides the concepts around MCP (such as tools, resources, and prompts), but unlike other MCP packages, it can be run standalone (without being a real service).

Packages developed with sema4ai.mcp can run as an actual MCP server, by loading it into the `Sema4.ai Action Server`, which loads this package and provides the actual MCP server implementation.

This approach enables: 1. Automatic generation of the environment to run the server (the Action Server will read the related `package.yaml` and then run the tools/resources/prompts in thetarget environment, enabling multiple MCPs to have different environments).2. Automated logging and execution tracking (i.e.: `robocorp.log` is used to automatically log the Python execution and the results of the tools/resources/prompts).3. It's possible to inspect in the Action Server all the tools/resources/prompts calls made and inspect the details on the execution.

# Functions

______________________________________________________________________

## `tool`

Decorator for tools which can be used by AI agents to perform actions.

**Args:**

- <b>`title`</b>: A human-readable title for the tool.

- <b>`read_only_hint`</b>: If true, the tool does not modify its environment (default: False).

- <b>`destructive_hint`</b>: If true, the tool may perform destructive updates to its environment (default: True).

- <b>`idempotent_hint`</b>: If true, calling the tool repeatedly with the same arguments will have no additional effect on the its environment (default: False).

- <b>`open_world_hint`</b>: If true, this tool may interact with an "open world" of external entities (default: True).

If False, the tool's domain of interaction is closed. For example, the world of a web search tool is open, whereas that of a memory tool is not.

**Example:**

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

Note that a tool needs sema4ai actions to be executed. The command line to execute it is:

python -m sema4ai.actions run actions.py -a assign_ticket

[**Link to source**](https://github.com/sema4ai/actions/tree/master/mcp/src/sema4ai/mcp/__init__.py#L91)

```python
tool(*args, **kwargs)
```

______________________________________________________________________

## `resource`

Decorator for resources which provide data to the LLM.

Resources may be simple or templates. Templates are resources with `{placeholder}` indications in the uri, according to RFC 6570.

**Args:**

- <b>`uri`</b>: The URI of the resource (may be a template or a simple resource). If not provided, a uri such as `resource://read/<function_name>/{arg_name1}/{arg_name2}` will be created automatically (arguments are optional).
- <b>`mime_type`</b>: The MIME type of the resource. If not provided, it's based on the type of the result (if it's a string, it's `text/plain`, if it's a bytes, it's `application/octet-stream`, if it's another type dict, it's converted to json and then `application/json` is used as the mime type).
- <b>`size`</b>: The size of the raw resource content, in bytes (i.e., before base64 encoding or any tokenization), if known. This can be used by Hosts to display file sizes and estimate context window usage.

Note: the name is the name of the function and the description is gotten from the docstring.

If called without any argument, an automatic uri is created based on the function name and arguments with the following format: `resource://read/<function_name>/{arg_name1}/{arg_name2}`.

**Example:**

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

Note that a resource needs sema4ai actions to be executed. The command line to execute it is:

python -m sema4ai.actions run actions.py -a get_ticket

See: https://modelcontextprotocol.io/docs/concepts/resources

[**Link to source**](https://github.com/sema4ai/actions/tree/master/mcp/src/sema4ai/mcp/__init__.py#L206)

```python
resource(*args, **kwargs) → Callable
```

______________________________________________________________________

## `prompt`

Decorator for functions that generate prompts for the LLM.

No arguments are accepted by this decorator.

The description of the prompt is gotten from the docstring.

Note that each argument in the function signature is automatically added as a required argument in the prompt (the argument description is gotten from the `Args` in the docstring).

**Example:**

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

Note that a prompt needs sema4ai actions to be executed. The command line to execute it is:

python -m sema4ai.actions run actions.py -a make_a_summary

[**Link to source**](https://github.com/sema4ai/actions/tree/master/mcp/src/sema4ai/mcp/__init__.py#L318)

```python
prompt(*args, **kwargs)
```
