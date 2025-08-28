from sema4ai.actions._secret import Secret

from sema4ai import mcp


@mcp.tool()
def greet_mcp(name: str, title="Mr.") -> str:
    """
    Provides a greeting for a person.

    Args:
        name: The name of the person to greet.
        title: The title for the persor (Mr., Mrs., ...).

    Returns:
        The greeting for the person.

    Tool structure:

    {
        name: string;          // Unique identifier for the tool
        description?: string;  // Human-readable description
        inputSchema: {         // JSON Schema for the tool's parameters
            type: "object",
            properties: { ... }  // Tool-specific parameters
        },
        annotations?: {        // Optional hints about tool behavior
            title?: string;      // Human-readable title for the tool
            readOnlyHint?: boolean;    // If true, the tool does not modify its environment
            destructiveHint?: boolean; // If true, the tool may perform destructive updates
            idempotentHint?: boolean;  // If true, repeated calls with same args have no additional effect
            openWorldHint?: boolean;   // If true, tool interacts with external entities
        }
    }
    """
    return f"Hello {title} {name}."


@mcp.tool
async def check_secrets(my_secret: Secret) -> str:
    """
    Check if the secrets are working.

    Args:
        my_secret: The secret to check.

    Returns:
        The value of the secret.
    """
    return my_secret.value


@mcp.tool()
async def long_running_tool(duration: float) -> str:
    """
    Does a long running task.

    Args:
        duration: The duration to wait in seconds.

    Returns:
        The result of the long running task.
    """
    # We'd like to cancel this, but it's just not possible with the current SDK!
    import asyncio

    await asyncio.sleep(duration)
    return "ok"


@mcp.prompt()
async def my_prompt(name: str) -> str:
    """
    Prompts in MCP are predefined templates that can:

        Accept dynamic arguments
        Include context from resources
        Chain multiple interactions
        Guide specific workflows
        Surface as UI elements (like slash commands)

    Prompt structure

    Each prompt is defined with:

    {
        name: string;              // Unique identifier for the prompt
        description?: string;      // Human-readable description
        arguments?: [              // Optional list of arguments
            {
                name: string;          // Argument identifier
                description?: string;  // Argument description
                required?: boolean;    // Whether argument is required
            }
        ]
    }

    Args:
        name: The name of the person to greet.
    """
    return f"This is the built in prompt for {name}."


@mcp.prompt()
async def my_prompt_with_optional_arg(name: str | None = None) -> str:
    """
        Prompt with an optional argument.

        Args:
            name: The name of the person to greet.
        """
    return (
        f"This is the built in prompt for {name}."
        if name
        else "This is the built in prompt without a name."
    )


@mcp.resource(
    uri="custom://my/resource/simple"
)  # uri must be: [protocol]://[host]/[path]
async def my_resource_no_template() -> str:
    """
    This is a simple resource without a template.
    """
    return "This is a simple resource without a template."


@mcp.resource(
    uri="custom://my/resource/{name}"
)  # uri must be: [protocol]://[host]/[path]
async def my_resource_template(name: str) -> str:
    """
    Resources represent any kind of data that an MCP server wants to make available to clients. This can include:

        File contents
        Database records
        API responses
        Live system data
        Screenshots and images
        Log files
        And more

    Each resource is identified by a unique URI and can contain either text or binary data.

    Structure is:

    Direct resources:
    {
        uri: string;           // Unique identifier for the resource
        name: string;          // Human-readable name
        description?: string;  // Optional description
        mimeType?: string;     // Optional MIME type
        size?: number;         // Optional size in bytes
    }

    Resource templates:
    {
        uriTemplate: string;   // URI template following RFC 6570
        name: string;          // Human-readable name for this type
        description?: string;  // Optional description
        mimeType?: string;     // Optional MIME type for all matching resources
    }
    """
    return f"This is the built in resource for {name}."
