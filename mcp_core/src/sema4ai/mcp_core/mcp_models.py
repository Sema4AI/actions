from typing import Any, TypeVar, Literal
from dataclasses import dataclass, field
from enum import Enum

T = TypeVar('T')

class MessageType(Enum):
    REQUEST = "request"
    NOTIFICATION = "notification"
    RESPONSE = "response"

@dataclass
class BaseModel:
    """Base class for all MCP models."""
    
    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        return cls(**data)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    @classmethod
    def get_message_type(cls) -> MessageType:
        """Get the type of message this class represents."""
        if cls.__name__.endswith('Request'):
            return MessageType.REQUEST
        elif cls.__name__.endswith('Notification'):
            return MessageType.NOTIFICATION
        elif cls.__name__.endswith('Result') or cls.__name__.endswith('Response'):
            return MessageType.RESPONSE
        return MessageType.REQUEST  # Default to request if unknown

@dataclass
class Annotations(BaseModel):
    """Optional annotations for the client. The client can use annotations to inform how objects are used or displayed"""
    audience: "None | list[Role]" = field(default=None)
    priority: "None | float" = field(default=None)


@dataclass
class AudioContent(BaseModel):
    """Audio provided to or from an LLM."""
    annotations: "None | Annotations" = field(default=None)
    data: "str" = field(default="")
    mimeType: "str" = field(default="")
    type: "str" = field(default="")


@dataclass
class BlobResourceContents(BaseModel):

    blob: "str" = field(default="")
    mimeType: "None | str" = field(default=None)
    uri: "str" = field(default="")


@dataclass
class CallToolRequest(BaseModel):
    """Used by the client to invoke a tool provided by the server."""
    method: "Literal['tools/call']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class CallToolResult(BaseModel):
    """The server's response to a tool call.

Any errors that originate from the tool SHOULD be reported inside the result
object, with `isError` set to true, _not_ as an MCP protocol-level error
response. Otherwise, the LLM would not be able to see that an error occurred
and self-correct.

However, any errors in _finding_ the tool, an error indicating that the
server does not support tool calls, or any other exceptional conditions,
should be reported as an MCP error response."""
    _meta: "None | dict[str, Any]" = field(default=None)
    content: "list[TextContent | ImageContent | AudioContent | EmbeddedResource]" = field(default=field(default_factory=list))
    isError: "None | bool" = field(default=None)


@dataclass
class CancelledNotification(BaseModel):
    """This notification can be sent by either side to indicate that it is cancelling a previously-issued request.

The request SHOULD still be in-flight, but due to communication latency, it is always possible that this notification MAY arrive after the request has already finished.

This notification indicates that the result will be unused, so any associated processing SHOULD cease.

A client MUST NOT attempt to cancel its `initialize` request."""
    method: "Literal['notifications/cancelled']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class ClientCapabilities(BaseModel):
    """Capabilities a client may support. Known capabilities are defined here, in this schema, but this is not a closed set: any client can define its own, additional capabilities."""
    experimental: "None | dict[str, Any]" = field(default=None)
    roots: "None | dict[str, Any]" = field(default=None)
    sampling: "None | dict[str, Any]" = field(default=None)


@dataclass
class CompleteRequest(BaseModel):
    """A request from the client to the server, to ask for completion options."""
    method: "Literal['completion/complete']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class CompleteResult(BaseModel):
    """The server's response to a completion/complete request"""
    _meta: "None | dict[str, Any]" = field(default=None)
    completion: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class CreateMessageRequest(BaseModel):
    """A request from the server to sample an LLM via the client. The client has full discretion over which model to select. The client should also inform the user before beginning sampling, to allow them to inspect the request (human in the loop) and decide whether to approve it."""
    method: "Literal['sampling/createMessage']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class CreateMessageResult(BaseModel):
    """The client's response to a sampling/create_message request from the server. The client should inform the user before returning the sampled message, to allow them to inspect the response (human in the loop) and decide whether to allow the server to see it."""
    _meta: "None | dict[str, Any]" = field(default=None)
    content: "TextContent | ImageContent | AudioContent" = field(default=...)
    model: "str" = field(default="")
    role: "Role" = field(default=...)
    stopReason: "None | str" = field(default=None)


@dataclass
class EmbeddedResource(BaseModel):
    """The contents of a resource, embedded into a prompt or tool call result.

It is up to the client how best to render embedded resources for the benefit
of the LLM and/or the user."""
    annotations: "None | Annotations" = field(default=None)
    resource: "TextResourceContents | BlobResourceContents" = field(default=...)
    type: "str" = field(default="")


@dataclass
class GetPromptRequest(BaseModel):
    """Used by the client to get a prompt provided by the server."""
    method: "Literal['prompts/get']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class GetPromptResult(BaseModel):
    """The server's response to a prompts/get request from the client."""
    _meta: "None | dict[str, Any]" = field(default=None)
    description: "None | str" = field(default=None)
    messages: "list[PromptMessage]" = field(default=field(default_factory=list))


@dataclass
class ImageContent(BaseModel):
    """An image provided to or from an LLM."""
    annotations: "None | Annotations" = field(default=None)
    data: "str" = field(default="")
    mimeType: "str" = field(default="")
    type: "str" = field(default="")


@dataclass
class Implementation(BaseModel):
    """Describes the name and version of an MCP implementation."""
    name: "str" = field(default="")
    version: "str" = field(default="")


@dataclass
class InitializeRequest(BaseModel):
    """This request is sent from the client to the server when it first connects, asking it to begin initialization."""
    method: "Literal['initialize']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class InitializeResult(BaseModel):
    """After receiving an initialize request from the client, the server sends this response."""
    _meta: "None | dict[str, Any]" = field(default=None)
    capabilities: "ServerCapabilities" = field(default=...)
    instructions: "None | str" = field(default=None)
    protocolVersion: "str" = field(default="")
    serverInfo: "Implementation" = field(default=...)


@dataclass
class InitializedNotification(BaseModel):
    """This notification is sent from the client to the server after initialization has finished."""
    method: "Literal['notifications/initialized']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class JSONRPCError(BaseModel):
    """A response to a request that indicates an error occurred."""
    error: "dict[str, Any]" = field(default=field(default_factory=dict))
    id: "RequestId" = field(default=...)
    jsonrpc: "str" = field(default="")


@dataclass
class JSONRPCNotification(BaseModel):
    """A notification which does not expect a response."""
    jsonrpc: "str" = field(default="")
    method: "str" = field(default="")
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class JSONRPCRequest(BaseModel):
    """A request that expects a response."""
    id: "RequestId" = field(default=...)
    jsonrpc: "str" = field(default="")
    method: "str" = field(default="")
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class JSONRPCResponse(BaseModel):
    """A successful (non-error) response to a request."""
    id: "RequestId" = field(default=...)
    jsonrpc: "str" = field(default="")
    result: "Result" = field(default=...)


@dataclass
class ListPromptsRequest(BaseModel):
    """Sent from the client to request a list of prompts and prompt templates the server has."""
    method: "Literal['prompts/list']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class ListPromptsResult(BaseModel):
    """The server's response to a prompts/list request from the client."""
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)
    prompts: "list[Prompt]" = field(default=field(default_factory=list))


@dataclass
class ListResourceTemplatesRequest(BaseModel):
    """Sent from the client to request a list of resource templates the server has."""
    method: "Literal['resources/templates/list']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class ListResourceTemplatesResult(BaseModel):
    """The server's response to a resources/templates/list request from the client."""
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)
    resourceTemplates: "list[ResourceTemplate]" = field(default=field(default_factory=list))


@dataclass
class ListResourcesRequest(BaseModel):
    """Sent from the client to request a list of resources the server has."""
    method: "Literal['resources/list']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class ListResourcesResult(BaseModel):
    """The server's response to a resources/list request from the client."""
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)
    resources: "list[Resource]" = field(default=field(default_factory=list))


@dataclass
class ListRootsRequest(BaseModel):
    """Sent from the server to request a list of root URIs from the client. Roots allow
servers to ask for specific directories or files to operate on. A common example
for roots is providing a set of repositories or directories a server should operate
on.

This request is typically used when the server needs to understand the file system
structure or access specific locations that the client has permission to read from."""
    method: "Literal['roots/list']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class ListRootsResult(BaseModel):
    """The client's response to a roots/list request from the server.
This result contains an array of Root objects, each representing a root directory
or file that the server can operate on."""
    _meta: "None | dict[str, Any]" = field(default=None)
    roots: "list[Root]" = field(default=field(default_factory=list))


@dataclass
class ListToolsRequest(BaseModel):
    """Sent from the client to request a list of tools the server has."""
    method: "Literal['tools/list']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class ListToolsResult(BaseModel):
    """The server's response to a tools/list request from the client."""
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)
    tools: "list[Tool]" = field(default=field(default_factory=list))


@dataclass
class LoggingMessageNotification(BaseModel):
    """Notification of a log message passed from server to client. If no logging/setLevel request has been sent from the client, the server MAY decide which messages to send automatically."""
    method: "Literal['notifications/message']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class ModelHint(BaseModel):
    """Hints to use for model selection.

Keys not declared here are currently left unspecified by the spec and are up
to the client to interpret."""
    name: "None | str" = field(default=None)


@dataclass
class ModelPreferences(BaseModel):
    """The server's preferences for model selection, requested of the client during sampling.

Because LLMs can vary along multiple dimensions, choosing the "best" model is
rarely straightforward.  Different models excel in different areas—some are
faster but less capable, others are more capable but more expensive, and so
on. This interface allows servers to express their priorities across multiple
dimensions to help clients make an appropriate selection for their use case.

These preferences are always advisory. The client MAY ignore them. It is also
up to the client to decide how to interpret these preferences and how to
balance them against other considerations."""
    costPriority: "None | float" = field(default=None)
    hints: "None | list[ModelHint]" = field(default=None)
    intelligencePriority: "None | float" = field(default=None)
    speedPriority: "None | float" = field(default=None)


@dataclass
class Notification(BaseModel):

    method: "str" = field(default="")
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class PaginatedRequest(BaseModel):

    method: "str" = field(default="")
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class PaginatedResult(BaseModel):

    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)


@dataclass
class PingRequest(BaseModel):
    """A ping, issued by either the server or the client, to check that the other party is still alive. The receiver must promptly respond, or else may be disconnected."""
    method: "Literal['ping']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class ProgressNotification(BaseModel):
    """An out-of-band notification used to inform the receiver of a progress update for a long-running request."""
    method: "Literal['notifications/progress']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class Prompt(BaseModel):
    """A prompt or prompt template that the server offers."""
    arguments: "None | list[PromptArgument]" = field(default=None)
    description: "None | str" = field(default=None)
    name: "str" = field(default="")


@dataclass
class PromptArgument(BaseModel):
    """Describes an argument that a prompt can accept."""
    description: "None | str" = field(default=None)
    name: "str" = field(default="")
    required: "None | bool" = field(default=None)


@dataclass
class PromptListChangedNotification(BaseModel):
    """An optional notification from the server to the client, informing it that the list of prompts it offers has changed. This may be issued by servers without any previous subscription from the client."""
    method: "Literal['notifications/prompts/list_changed']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class PromptMessage(BaseModel):
    """Describes a message returned as part of a prompt.

This is similar to `SamplingMessage`, but also supports the embedding of
resources from the MCP server."""
    content: "TextContent | ImageContent | AudioContent | EmbeddedResource" = field(default=...)
    role: "Role" = field(default=...)


@dataclass
class PromptReference(BaseModel):
    """Identifies a prompt."""
    name: "str" = field(default="")
    type: "str" = field(default="")


@dataclass
class ReadResourceRequest(BaseModel):
    """Sent from the client to the server, to read a specific resource URI."""
    method: "Literal['resources/read']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class ReadResourceResult(BaseModel):
    """The server's response to a resources/read request from the client."""
    _meta: "None | dict[str, Any]" = field(default=None)
    contents: "list[TextResourceContents | BlobResourceContents]" = field(default=field(default_factory=list))


@dataclass
class Request(BaseModel):

    method: "str" = field(default="")
    params: "None | dict[str, Any]" = field(default=None)


# Type alias for request identifiers
RequestId = int | str


@dataclass
class Resource(BaseModel):
    """A known resource that the server is capable of reading."""
    annotations: "None | Annotations" = field(default=None)
    description: "None | str" = field(default=None)
    mimeType: "None | str" = field(default=None)
    name: "str" = field(default="")
    size: "None | int" = field(default=None)
    uri: "str" = field(default="")


@dataclass
class ResourceContents(BaseModel):
    """The contents of a specific resource or sub-resource."""
    mimeType: "None | str" = field(default=None)
    uri: "str" = field(default="")


@dataclass
class ResourceListChangedNotification(BaseModel):
    """An optional notification from the server to the client, informing it that the list of resources it can read from has changed. This may be issued by servers without any previous subscription from the client."""
    method: "Literal['notifications/resources/list_changed']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class ResourceReference(BaseModel):
    """A reference to a resource or resource template definition."""
    type: "str" = field(default="")
    uri: "str" = field(default="")


@dataclass
class ResourceTemplate(BaseModel):
    """A template description for resources available on the server."""
    annotations: "None | Annotations" = field(default=None)
    description: "None | str" = field(default=None)
    mimeType: "None | str" = field(default=None)
    name: "str" = field(default="")
    uriTemplate: "str" = field(default="")


@dataclass
class ResourceUpdatedNotification(BaseModel):
    """A notification from the server to the client, informing it that a resource has changed and may need to be read again. This should only be sent if the client previously sent a resources/subscribe request."""
    method: "Literal['notifications/resources/updated']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class Result(BaseModel):

    _meta: "None | dict[str, Any]" = field(default=None)


class Role(Enum):
    """The sender or recipient of messages and data in a conversation."""
    ASSISTANT = 'assistant'
    USER = 'user'


@dataclass
class Root(BaseModel):
    """Represents a root directory or file that the server can operate on."""
    name: "None | str" = field(default=None)
    uri: "str" = field(default="")


@dataclass
class RootsListChangedNotification(BaseModel):
    """A notification from the client to the server, informing it that the list of roots has changed.
This notification should be sent whenever the client adds, removes, or modifies any root.
The server should then request an updated list of roots using the ListRootsRequest."""
    method: "Literal['notifications/roots/list_changed']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class SamplingMessage(BaseModel):
    """Describes a message issued to or received from an LLM API."""
    content: "TextContent | ImageContent | AudioContent" = field(default=...)
    role: "Role" = field(default=...)


@dataclass
class ServerCapabilities(BaseModel):
    """Capabilities that a server may support. Known capabilities are defined here, in this schema, but this is not a closed set: any server can define its own, additional capabilities."""
    completions: "None | dict[str, Any]" = field(default=None)
    experimental: "None | dict[str, Any]" = field(default=None)
    logging: "None | dict[str, Any]" = field(default=None)
    prompts: "None | dict[str, Any]" = field(default=None)
    resources: "None | dict[str, Any]" = field(default=None)
    tools: "None | dict[str, Any]" = field(default=None)


@dataclass
class SetLevelRequest(BaseModel):
    """A request from the client to the server, to enable or adjust logging."""
    method: "Literal['logging/setLevel']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class SubscribeRequest(BaseModel):
    """Sent from the client to request resources/updated notifications from the server whenever a particular resource changes."""
    method: "Literal['resources/subscribe']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


@dataclass
class TextContent(BaseModel):
    """Text provided to or from an LLM."""
    annotations: "None | Annotations" = field(default=None)
    text: "str" = field(default="")
    type: "str" = field(default="")


@dataclass
class TextResourceContents(BaseModel):

    mimeType: "None | str" = field(default=None)
    text: "str" = field(default="")
    uri: "str" = field(default="")


@dataclass
class Tool(BaseModel):
    """Definition for a tool the client can call."""
    annotations: "None | ToolAnnotations" = field(default=None)
    description: "None | str" = field(default=None)
    inputSchema: "dict[str, Any]" = field(default=field(default_factory=dict))
    name: "str" = field(default="")


@dataclass
class ToolAnnotations(BaseModel):
    """Additional properties describing a Tool to clients.

NOTE: all properties in ToolAnnotations are **hints**.
They are not guaranteed to provide a faithful description of
tool behavior (including descriptive properties like `title`).

Clients should never make tool use decisions based on ToolAnnotations
received from untrusted servers."""
    destructiveHint: "None | bool" = field(default=None)
    idempotentHint: "None | bool" = field(default=None)
    openWorldHint: "None | bool" = field(default=None)
    readOnlyHint: "None | bool" = field(default=None)
    title: "None | str" = field(default=None)


@dataclass
class ToolListChangedNotification(BaseModel):
    """An optional notification from the server to the client, informing it that the list of tools it offers has changed. This may be issued by servers without any previous subscription from the client."""
    method: "Literal['notifications/tools/list_changed']" = field(default=...)
    params: "None | dict[str, Any]" = field(default=None)


@dataclass
class UnsubscribeRequest(BaseModel):
    """Sent from the client to request cancellation of resources/updated notifications from the server. This should follow a previous resources/subscribe request."""
    method: "Literal['resources/unsubscribe']" = field(default=...)
    params: "dict[str, Any]" = field(default=field(default_factory=dict))


_class_map = {
    'tools/call': CallToolRequest,
    'notifications/cancelled': CancelledNotification,
    'completion/complete': CompleteRequest,
    'sampling/createMessage': CreateMessageRequest,
    'prompts/get': GetPromptRequest,
    'initialize': InitializeRequest,
    'notifications/initialized': InitializedNotification,
    'prompts/list': ListPromptsRequest,
    'resources/templates/list': ListResourceTemplatesRequest,
    'resources/list': ListResourcesRequest,
    'roots/list': ListRootsRequest,
    'tools/list': ListToolsRequest,
    'notifications/message': LoggingMessageNotification,
    'ping': PingRequest,
    'notifications/progress': ProgressNotification,
    'notifications/prompts/list_changed': PromptListChangedNotification,
    'resources/read': ReadResourceRequest,
    'notifications/resources/list_changed': ResourceListChangedNotification,
    'notifications/resources/updated': ResourceUpdatedNotification,
    'notifications/roots/list_changed': RootsListChangedNotification,
    'logging/setLevel': SetLevelRequest,
    'resources/subscribe': SubscribeRequest,
    'notifications/tools/list_changed': ToolListChangedNotification,
    'resources/unsubscribe': UnsubscribeRequest,
}

def create_mcp_model(data: dict[str, Any]) -> BaseModel:
    """Create an MCP model instance from a dictionary based on its method field.
    
    Args:
        data: Dictionary containing the model data
        
    Returns:
        An instance of the appropriate MCP model class
        
    Raises:
        ValueError: If the method field is missing or no matching class is found
    """
    if "method" not in data:
        raise ValueError("Input dictionary must contain a 'method' field")
        
    method = data["method"]
    if method not in _class_map:
        raise ValueError(f"No MCP model class found for method: {method}")
        
    return _class_map[method].from_dict(data)
