from typing import Any, TypeVar, Literal, Type
from dataclasses import dataclass, field
from sema4ai.mcp_core.mcp_base_model import MCPBaseModel

T = TypeVar("T")


@dataclass
class Result(MCPBaseModel):
    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        return cls(**kwargs)


@dataclass
class Annotations(MCPBaseModel):
    """
    Optional annotations for the client. The client can use annotations to inform how
    objects are used or displayed
    """

    audience: "None | list[Role]" = field(default=None)
    lastModified: "None | str" = field(default=None)
    priority: "None | float" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process audience
        value = data.get("audience")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field audience, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["audience"] = value

        # Process lastModified
        value = data.get("lastModified")
        kwargs["lastModified"] = value

        # Process priority
        value = data.get("priority")
        kwargs["priority"] = value

        return cls(**kwargs)


@dataclass
class AudioContent(MCPBaseModel):
    """Audio provided to or from an LLM."""

    data: "str"
    mimeType: "str"
    type: "Literal['audio']" = field(default="audio")
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = Annotations.from_dict(value)
        kwargs["annotations"] = value

        # Process data
        value = data.get("data")
        kwargs["data"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class BaseMetadata(MCPBaseModel):
    """
    Base interface for metadata with name (identifier) and title (display name)
    properties.
    """

    name: "str"
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        return cls(**kwargs)


@dataclass
class BlobResourceContents(MCPBaseModel):
    blob: "str"
    uri: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    mimeType: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process blob
        value = data.get("blob")
        kwargs["blob"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class BooleanSchema(MCPBaseModel):
    type: "Literal['boolean']" = field(default="boolean")
    default: "None | bool" = field(default=None)
    description: "None | str" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process default
        value = data.get("default")
        kwargs["default"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class CallToolRequest(MCPBaseModel):
    """Used by the client to invoke a tool provided by the server."""

    id: "RequestId"
    params: "CallToolRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['tools/call']" = field(default="tools/call")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = CallToolRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CallToolRequestParams(MCPBaseModel):
    name: "str"
    arguments: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process arguments
        value = data.get("arguments")
        kwargs["arguments"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        return cls(**kwargs)


@dataclass
class CallToolResult(Result):
    """The server's response to a tool call."""

    content: "list[ContentBlock]"
    _meta: "None | dict[str, Any]" = field(default=None)
    isError: "None | bool" = field(default=None)
    structuredContent: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process content
        value = data.get("content")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field content, got {type(value)}"
                )
            converted_items = []
            for item in value:
                # Try to disambiguate using const fields
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Expected a dict for union type ContentBlock, got {type(item)}"
                    )
                type_value = item.get("type")
                type_to_class = {}
                required_props_map = {}
                type_to_class["text"] = TextContent
                type_to_class["image"] = ImageContent
                type_to_class["audio"] = AudioContent
                type_to_class["resource_link"] = ResourceLink
                type_to_class["resource"] = EmbeddedResource
                if type_value is not None and type_value in type_to_class:
                    converted_items.append(type_to_class[type_value].from_dict(item))
                else:
                    # Try to disambiguate by required properties
                    matches = []
                    for type_name, reqs in required_props_map.items():
                        if all(r in item for r in reqs):
                            matches.append(type_name)
                    if len(matches) == 1:
                        converted_items.append(matches[0].from_dict(item))
                    elif len(matches) > 1:
                        match_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in matches
                        ]
                        raise ValueError(
                            f"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}"
                        )
                    else:
                        available_fields = list(item.keys())
                        type_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in required_props_map
                        ]
                        raise ValueError(
                            f"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}"
                        )
            value = converted_items
        kwargs["content"] = value

        # Process isError
        value = data.get("isError")
        kwargs["isError"] = value

        # Process structuredContent
        value = data.get("structuredContent")
        kwargs["structuredContent"] = value

        return cls(**kwargs)


@dataclass
class CancelledNotification(MCPBaseModel):
    """
    This notification can be sent by either side to indicate that it is cancelling a
    previously-issued request. The request SHOULD still be in-flight, but due to
    communication latency, it is always possible that this notification MAY arrive
    after the request has already finished. This notification indicates that the
    result will be unused, so any associated processing SHOULD cease. A client MUST
    NOT attempt to cancel its `initialize` request.
    """

    params: "CancelledNotificationParams"
    method: "Literal['notifications/cancelled']" = field(
        default="notifications/cancelled"
    )

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = CancelledNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CancelledNotificationParams(MCPBaseModel):
    requestId: "RequestId"
    reason: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process reason
        value = data.get("reason")
        kwargs["reason"] = value

        # Process requestId
        value = data.get("requestId")
        kwargs["requestId"] = value

        return cls(**kwargs)


@dataclass
class ClientCapabilities(MCPBaseModel):
    """
    Capabilities a client may support. Known capabilities are defined here, in this
    schema, but this is not a closed set: any client can define its own, additional
    capabilities.
    """

    elicitation: "None | dict[str, Any]" = field(default=None)
    experimental: "None | dict[str, Any]" = field(default=None)
    roots: "None | ClientCapabilitiesRootsParams" = field(default=None)
    sampling: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process elicitation
        value = data.get("elicitation")
        kwargs["elicitation"] = value

        # Process experimental
        value = data.get("experimental")
        kwargs["experimental"] = value

        # Process roots
        value = data.get("roots")
        if value is not None:
            value = ClientCapabilitiesRootsParams.from_dict(value)
        kwargs["roots"] = value

        # Process sampling
        value = data.get("sampling")
        kwargs["sampling"] = value

        return cls(**kwargs)


@dataclass
class ClientCapabilitiesRootsParams(MCPBaseModel):
    """Present if the client supports listing roots."""

    listChanged: "None | bool" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process listChanged
        value = data.get("listChanged")
        kwargs["listChanged"] = value

        return cls(**kwargs)


@dataclass
class CompleteRequest(MCPBaseModel):
    """A request from the client to the server, to ask for completion options."""

    id: "RequestId"
    params: "CompleteRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['completion/complete']" = field(default="completion/complete")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = CompleteRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CompleteRequestParams(MCPBaseModel):
    argument: "CompleteRequestParamsArgument"
    ref: "PromptReference | ResourceTemplateReference"
    context: "None | CompleteRequestParamsContext" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process argument
        value = data.get("argument")
        if value is not None:
            value = CompleteRequestParamsArgument.from_dict(value)
        kwargs["argument"] = value

        # Process context
        value = data.get("context")
        if value is not None:
            value = CompleteRequestParamsContext.from_dict(value)
        kwargs["context"] = value

        # Process ref
        value = data.get("ref")
        if value is not None:
            if isinstance(value, dict):
                # Try to disambiguate using const fields
                type_value = value.get("type")
                type_to_class = {}
                required_props_map = {}
                type_to_class["ref/prompt"] = PromptReference
                type_to_class["ref/resource"] = ResourceTemplateReference
                if type_value is not None and type_value in type_to_class:
                    value = type_to_class[type_value].from_dict(value)
                else:
                    # Try to disambiguate by required properties
                    matches = []
                    for type_name, reqs in required_props_map.items():
                        if all(r in value for r in reqs):
                            matches.append(type_name)
                    if len(matches) == 1:
                        value = matches[0].from_dict(value)
                    elif len(matches) > 1:
                        match_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in matches
                        ]
                        raise ValueError(
                            f"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}"
                        )
                    else:
                        available_fields = list(value.keys())
                        type_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in required_props_map
                        ]
                        raise ValueError(
                            f"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}"
                        )
        kwargs["ref"] = value

        return cls(**kwargs)


@dataclass
class CompleteRequestParamsArgument(MCPBaseModel):
    """The argument's information"""

    name: "str"
    value: "str"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process value
        value = data.get("value")
        kwargs["value"] = value

        return cls(**kwargs)


@dataclass
class CompleteRequestParamsContext(MCPBaseModel):
    """Additional, optional context for completions"""

    arguments: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process arguments
        value = data.get("arguments")
        kwargs["arguments"] = value

        return cls(**kwargs)


@dataclass
class CompleteResult(Result):
    """The server's response to a completion/complete request"""

    completion: "CompleteResultCompletionParams"
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process completion
        value = data.get("completion")
        if value is not None:
            value = CompleteResultCompletionParams.from_dict(value)
        kwargs["completion"] = value

        return cls(**kwargs)


@dataclass
class CompleteResultCompletionParams(MCPBaseModel):
    values: "list[str]"
    hasMore: "None | bool" = field(default=None)
    total: "None | int" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process hasMore
        value = data.get("hasMore")
        kwargs["hasMore"] = value

        # Process total
        value = data.get("total")
        kwargs["total"] = value

        # Process values
        value = data.get("values")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(f"Expected a list for field values, got {type(value)}")
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["values"] = value

        return cls(**kwargs)


@dataclass
class CreateMessageRequest(MCPBaseModel):
    """
    A request from the server to sample an LLM via the client. The client has full
    discretion over which model to select. The client should also inform the user
    before beginning sampling, to allow them to inspect the request (human in the
    loop) and decide whether to approve it.
    """

    id: "RequestId"
    params: "CreateMessageRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['sampling/createMessage']" = field(
        default="sampling/createMessage"
    )

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = CreateMessageRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CreateMessageRequestParams(MCPBaseModel):
    maxTokens: "int"
    messages: "list[SamplingMessage]"
    includeContext: "None | Literal['allServers', 'none', 'thisServer']" = field(
        default=None
    )
    metadata: "None | dict[str, Any]" = field(default=None)
    modelPreferences: "None | ModelPreferences" = field(default=None)
    stopSequences: "None | list[str]" = field(default=None)
    systemPrompt: "None | str" = field(default=None)
    temperature: "None | float" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process includeContext
        value = data.get("includeContext")
        kwargs["includeContext"] = value

        # Process maxTokens
        value = data.get("maxTokens")
        kwargs["maxTokens"] = value

        # Process messages
        value = data.get("messages")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field messages, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(SamplingMessage.from_dict(item))
            value = converted_items
        kwargs["messages"] = value

        # Process metadata
        value = data.get("metadata")
        kwargs["metadata"] = value

        # Process modelPreferences
        value = data.get("modelPreferences")
        if value is not None:
            value = ModelPreferences.from_dict(value)
        kwargs["modelPreferences"] = value

        # Process stopSequences
        value = data.get("stopSequences")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field stopSequences, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["stopSequences"] = value

        # Process systemPrompt
        value = data.get("systemPrompt")
        kwargs["systemPrompt"] = value

        # Process temperature
        value = data.get("temperature")
        kwargs["temperature"] = value

        return cls(**kwargs)


@dataclass
class CreateMessageResult(Result):
    """
    The client's response to a sampling/create_message request from the server. The
    client should inform the user before returning the sampled message, to allow them
    to inspect the response (human in the loop) and decide whether to allow the server
    to see it.
    """

    content: "TextContent | ImageContent | AudioContent"
    model: "str"
    role: "Role"
    _meta: "None | dict[str, Any]" = field(default=None)
    stopReason: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process content
        value = data.get("content")
        if value is not None:
            if isinstance(value, dict):
                # Try to disambiguate using const fields
                type_value = value.get("type")
                type_to_class = {}
                required_props_map = {}
                type_to_class["text"] = TextContent
                type_to_class["image"] = ImageContent
                type_to_class["audio"] = AudioContent
                if type_value is not None and type_value in type_to_class:
                    value = type_to_class[type_value].from_dict(value)
                else:
                    # Try to disambiguate by required properties
                    matches = []
                    for type_name, reqs in required_props_map.items():
                        if all(r in value for r in reqs):
                            matches.append(type_name)
                    if len(matches) == 1:
                        value = matches[0].from_dict(value)
                    elif len(matches) > 1:
                        match_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in matches
                        ]
                        raise ValueError(
                            f"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}"
                        )
                    else:
                        available_fields = list(value.keys())
                        type_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in required_props_map
                        ]
                        raise ValueError(
                            f"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}"
                        )
        kwargs["content"] = value

        # Process model
        value = data.get("model")
        kwargs["model"] = value

        # Process role
        value = data.get("role")
        kwargs["role"] = value

        # Process stopReason
        value = data.get("stopReason")
        kwargs["stopReason"] = value

        return cls(**kwargs)


@dataclass
class ElicitRequest(MCPBaseModel):
    """
    A request from the server to elicit additional information from the user via the
    client.
    """

    id: "RequestId"
    params: "ElicitRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['elicitation/create']" = field(default="elicitation/create")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ElicitRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ElicitRequestParams(MCPBaseModel):
    message: "str"
    requestedSchema: "ElicitRequestParamsRequestedschema"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process message
        value = data.get("message")
        kwargs["message"] = value

        # Process requestedSchema
        value = data.get("requestedSchema")
        if value is not None:
            value = ElicitRequestParamsRequestedschema.from_dict(value)
        kwargs["requestedSchema"] = value

        return cls(**kwargs)


@dataclass
class ElicitRequestParamsRequestedschema(MCPBaseModel):
    """
    A restricted subset of JSON Schema. Only top-level properties are allowed,
    without nesting.
    """

    properties: "dict[str, Any]"
    type: "Literal['object']" = field(default="object")
    required: "None | list[str]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process properties
        value = data.get("properties")
        kwargs["properties"] = value

        # Process required
        value = data.get("required")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field required, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["required"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class ElicitResult(Result):
    """The client's response to an elicitation request."""

    action: "Literal['accept', 'cancel', 'decline']"
    _meta: "None | dict[str, Any]" = field(default=None)
    content: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process action
        value = data.get("action")
        kwargs["action"] = value

        # Process content
        value = data.get("content")
        kwargs["content"] = value

        return cls(**kwargs)


@dataclass
class EmbeddedResource(MCPBaseModel):
    """
    The contents of a resource, embedded into a prompt or tool call result. It is up
    to the client how best to render embedded resources for the benefit of the LLM
    and/or the user.
    """

    resource: "TextResourceContents | BlobResourceContents"
    type: "Literal['resource']" = field(default="resource")
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = Annotations.from_dict(value)
        kwargs["annotations"] = value

        # Process resource
        value = data.get("resource")
        if value is not None:
            if isinstance(value, dict):
                # Try to disambiguate using const fields
                type_value = value.get("type")
                type_to_class = {}
                required_props_map = {}
                required_props_map[TextResourceContents] = ["text", "uri"]
                required_props_map[BlobResourceContents] = ["blob", "uri"]
                if type_value is not None and type_value in type_to_class:
                    value = type_to_class[type_value].from_dict(value)
                else:
                    # Try to disambiguate by required properties
                    matches = []
                    for type_name, reqs in required_props_map.items():
                        if all(r in value for r in reqs):
                            matches.append(type_name)
                    if len(matches) == 1:
                        value = matches[0].from_dict(value)
                    elif len(matches) > 1:
                        match_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in matches
                        ]
                        raise ValueError(
                            f"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}"
                        )
                    else:
                        available_fields = list(value.keys())
                        type_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in required_props_map
                        ]
                        raise ValueError(
                            f"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}"
                        )
        kwargs["resource"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class EnumSchema(MCPBaseModel):
    enum: "list[str]"
    type: "Literal['string']" = field(default="string")
    description: "None | str" = field(default=None)
    enumNames: "None | list[str]" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process enum
        value = data.get("enum")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(f"Expected a list for field enum, got {type(value)}")
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["enum"] = value

        # Process enumNames
        value = data.get("enumNames")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field enumNames, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["enumNames"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class GetPromptRequest(MCPBaseModel):
    """Used by the client to get a prompt provided by the server."""

    id: "RequestId"
    params: "GetPromptRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['prompts/get']" = field(default="prompts/get")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = GetPromptRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class GetPromptRequestParams(MCPBaseModel):
    name: "str"
    arguments: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process arguments
        value = data.get("arguments")
        kwargs["arguments"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        return cls(**kwargs)


@dataclass
class GetPromptResult(Result):
    """The server's response to a prompts/get request from the client."""

    messages: "list[PromptMessage]"
    _meta: "None | dict[str, Any]" = field(default=None)
    description: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process messages
        value = data.get("messages")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field messages, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(PromptMessage.from_dict(item))
            value = converted_items
        kwargs["messages"] = value

        return cls(**kwargs)


@dataclass
class ImageContent(MCPBaseModel):
    """An image provided to or from an LLM."""

    data: "str"
    mimeType: "str"
    type: "Literal['image']" = field(default="image")
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = Annotations.from_dict(value)
        kwargs["annotations"] = value

        # Process data
        value = data.get("data")
        kwargs["data"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class Implementation(MCPBaseModel):
    """
    Describes the name and version of an MCP implementation, with an optional title
    for UI representation.
    """

    name: "str"
    version: "str"
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process version
        value = data.get("version")
        kwargs["version"] = value

        return cls(**kwargs)


@dataclass
class InitializeRequest(MCPBaseModel):
    """
    This request is sent from the client to the server when it first connects, asking
    it to begin initialization.
    """

    id: "RequestId"
    params: "InitializeRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['initialize']" = field(default="initialize")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = InitializeRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class InitializeRequestParams(MCPBaseModel):
    capabilities: "ClientCapabilities"
    clientInfo: "Implementation"
    protocolVersion: "str"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process capabilities
        value = data.get("capabilities")
        if value is not None:
            value = ClientCapabilities.from_dict(value)
        kwargs["capabilities"] = value

        # Process clientInfo
        value = data.get("clientInfo")
        if value is not None:
            value = Implementation.from_dict(value)
        kwargs["clientInfo"] = value

        # Process protocolVersion
        value = data.get("protocolVersion")
        kwargs["protocolVersion"] = value

        return cls(**kwargs)


@dataclass
class InitializeResult(Result):
    """
    After receiving an initialize request from the client, the server sends this
    response.
    """

    capabilities: "ServerCapabilities"
    protocolVersion: "str"
    serverInfo: "Implementation"
    _meta: "None | dict[str, Any]" = field(default=None)
    instructions: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process capabilities
        value = data.get("capabilities")
        if value is not None:
            value = ServerCapabilities.from_dict(value)
        kwargs["capabilities"] = value

        # Process instructions
        value = data.get("instructions")
        kwargs["instructions"] = value

        # Process protocolVersion
        value = data.get("protocolVersion")
        kwargs["protocolVersion"] = value

        # Process serverInfo
        value = data.get("serverInfo")
        if value is not None:
            value = Implementation.from_dict(value)
        kwargs["serverInfo"] = value

        return cls(**kwargs)


@dataclass
class InitializedNotification(MCPBaseModel):
    """
    This notification is sent from the client to the server after initialization has
    finished.
    """

    method: "Literal['notifications/initialized']" = field(
        default="notifications/initialized"
    )
    params: "None | InitializedNotificationParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = InitializedNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class InitializedNotificationParams(MCPBaseModel):
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCError(MCPBaseModel):
    """A response to a request that indicates an error occurred."""

    error: "JSONRPCErrorErrorParams"
    id: "RequestId"
    jsonrpc: "Literal['2.0']" = field(default="2.0")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process error
        value = data.get("error")
        if value is not None:
            value = JSONRPCErrorErrorParams.from_dict(value)
        kwargs["error"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCErrorErrorParams(MCPBaseModel):
    code: "int"
    message: "str"
    data: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process code
        value = data.get("code")
        kwargs["code"] = value

        # Process data
        value = data.get("data")
        kwargs["data"] = value

        # Process message
        value = data.get("message")
        kwargs["message"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCNotification(MCPBaseModel):
    """A notification which does not expect a response."""

    method: "str"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    params: "None | JSONRPCNotificationParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = JSONRPCNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCNotificationParams(MCPBaseModel):
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCRequest(MCPBaseModel):
    """A request that expects a response."""

    id: "RequestId"
    method: "str"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    params: "None | JSONRPCRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = JSONRPCRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCRequestParams(MCPBaseModel):
    _meta: "None | JSONRPCRequestParams_meta" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        if value is not None:
            value = JSONRPCRequestParams_meta.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCRequestParams_meta(MCPBaseModel):
    """
    See [specification/2025-06-18/basic/index#general-fields] for notes on _meta
    usage.
    """

    progressToken: "None | ProgressToken" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process progressToken
        value = data.get("progressToken")
        kwargs["progressToken"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCResponse(MCPBaseModel):
    """A successful (non-error) response to a request."""

    id: "RequestId"
    result: "Result"
    jsonrpc: "Literal['2.0']" = field(default="2.0")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process result
        value = data.get("result")
        if value is not None:
            value = Result.from_dict(value)
        kwargs["result"] = value

        return cls(**kwargs)


@dataclass
class ListPromptsRequest(MCPBaseModel):
    """
    Sent from the client to request a list of prompts and prompt templates the server
    has.
    """

    id: "RequestId"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['prompts/list']" = field(default="prompts/list")
    params: "None | ListPromptsRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ListPromptsRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListPromptsRequestParams(MCPBaseModel):
    cursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process cursor
        value = data.get("cursor")
        kwargs["cursor"] = value

        return cls(**kwargs)


@dataclass
class ListPromptsResult(Result):
    """The server's response to a prompts/list request from the client."""

    prompts: "list[Prompt]"
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process nextCursor
        value = data.get("nextCursor")
        kwargs["nextCursor"] = value

        # Process prompts
        value = data.get("prompts")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field prompts, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(Prompt.from_dict(item))
            value = converted_items
        kwargs["prompts"] = value

        return cls(**kwargs)


@dataclass
class ListResourceTemplatesRequest(MCPBaseModel):
    """Sent from the client to request a list of resource templates the server has."""

    id: "RequestId"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['resources/templates/list']" = field(
        default="resources/templates/list"
    )
    params: "None | ListResourceTemplatesRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ListResourceTemplatesRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListResourceTemplatesRequestParams(MCPBaseModel):
    cursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process cursor
        value = data.get("cursor")
        kwargs["cursor"] = value

        return cls(**kwargs)


@dataclass
class ListResourceTemplatesResult(Result):
    """The server's response to a resources/templates/list request from the client."""

    resourceTemplates: "list[ResourceTemplate]"
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process nextCursor
        value = data.get("nextCursor")
        kwargs["nextCursor"] = value

        # Process resourceTemplates
        value = data.get("resourceTemplates")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field resourceTemplates, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(ResourceTemplate.from_dict(item))
            value = converted_items
        kwargs["resourceTemplates"] = value

        return cls(**kwargs)


@dataclass
class ListResourcesRequest(MCPBaseModel):
    """Sent from the client to request a list of resources the server has."""

    id: "RequestId"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['resources/list']" = field(default="resources/list")
    params: "None | ListResourcesRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ListResourcesRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListResourcesRequestParams(MCPBaseModel):
    cursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process cursor
        value = data.get("cursor")
        kwargs["cursor"] = value

        return cls(**kwargs)


@dataclass
class ListResourcesResult(Result):
    """The server's response to a resources/list request from the client."""

    resources: "list[Resource]"
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process nextCursor
        value = data.get("nextCursor")
        kwargs["nextCursor"] = value

        # Process resources
        value = data.get("resources")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field resources, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(Resource.from_dict(item))
            value = converted_items
        kwargs["resources"] = value

        return cls(**kwargs)


@dataclass
class ListRootsRequest(MCPBaseModel):
    """
    Sent from the server to request a list of root URIs from the client. Roots allow
    servers to ask for specific directories or files to operate on. A common example
    for roots is providing a set of repositories or directories a server should
    operate on. This request is typically used when the server needs to understand the
    file system structure or access specific locations that the client has permission
    to read from.
    """

    id: "RequestId"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['roots/list']" = field(default="roots/list")
    params: "None | ListRootsRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ListRootsRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListRootsRequestParams(MCPBaseModel):
    _meta: "None | ListRootsRequestParams_meta" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        if value is not None:
            value = ListRootsRequestParams_meta.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class ListRootsRequestParams_meta(MCPBaseModel):
    """
    See [specification/2025-06-18/basic/index#general-fields] for notes on _meta
    usage.
    """

    progressToken: "None | ProgressToken" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process progressToken
        value = data.get("progressToken")
        kwargs["progressToken"] = value

        return cls(**kwargs)


@dataclass
class ListRootsResult(Result):
    """
    The client's response to a roots/list request from the server. This result
    contains an array of Root objects, each representing a root directory or file that
    the server can operate on.
    """

    roots: "list[Root]"
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process roots
        value = data.get("roots")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(f"Expected a list for field roots, got {type(value)}")
            converted_items = []
            for item in value:
                converted_items.append(Root.from_dict(item))
            value = converted_items
        kwargs["roots"] = value

        return cls(**kwargs)


@dataclass
class ListToolsRequest(MCPBaseModel):
    """Sent from the client to request a list of tools the server has."""

    id: "RequestId"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['tools/list']" = field(default="tools/list")
    params: "None | ListToolsRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ListToolsRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListToolsRequestParams(MCPBaseModel):
    cursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process cursor
        value = data.get("cursor")
        kwargs["cursor"] = value

        return cls(**kwargs)


@dataclass
class ListToolsResult(Result):
    """The server's response to a tools/list request from the client."""

    tools: "list[Tool]"
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process nextCursor
        value = data.get("nextCursor")
        kwargs["nextCursor"] = value

        # Process tools
        value = data.get("tools")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(f"Expected a list for field tools, got {type(value)}")
            converted_items = []
            for item in value:
                converted_items.append(Tool.from_dict(item))
            value = converted_items
        kwargs["tools"] = value

        return cls(**kwargs)


@dataclass
class LoggingMessageNotification(MCPBaseModel):
    """
    Notification of a log message passed from server to client. If no
    logging/setLevel request has been sent from the client, the server MAY decide
    which messages to send automatically.
    """

    params: "LoggingMessageNotificationParams"
    method: "Literal['notifications/message']" = field(default="notifications/message")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = LoggingMessageNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class LoggingMessageNotificationParams(MCPBaseModel):
    data: "str"
    level: "LoggingLevel"
    logger: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process data
        value = data.get("data")
        kwargs["data"] = value

        # Process level
        value = data.get("level")
        kwargs["level"] = value

        # Process logger
        value = data.get("logger")
        kwargs["logger"] = value

        return cls(**kwargs)


@dataclass
class ModelHint(MCPBaseModel):
    """
    Hints to use for model selection. Keys not declared here are currently left
    unspecified by the spec and are up to the client to interpret.
    """

    name: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        return cls(**kwargs)


@dataclass
class ModelPreferences(MCPBaseModel):
    """
    The server's preferences for model selection, requested of the client during
    sampling. Because LLMs can vary along multiple dimensions, choosing the "best"
    model is rarely straightforward. Different models excel in different areas—some
    are faster but less capable, others are more capable but more expensive, and so
    on. This interface allows servers to express their priorities across multiple
    dimensions to help clients make an appropriate selection for their use case. These
    preferences are always advisory. The client MAY ignore them. It is also up to the
    client to decide how to interpret these preferences and how to balance them
    against other considerations.
    """

    costPriority: "None | float" = field(default=None)
    hints: "None | list[ModelHint]" = field(default=None)
    intelligencePriority: "None | float" = field(default=None)
    speedPriority: "None | float" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process costPriority
        value = data.get("costPriority")
        kwargs["costPriority"] = value

        # Process hints
        value = data.get("hints")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(f"Expected a list for field hints, got {type(value)}")
            converted_items = []
            for item in value:
                converted_items.append(ModelHint.from_dict(item))
            value = converted_items
        kwargs["hints"] = value

        # Process intelligencePriority
        value = data.get("intelligencePriority")
        kwargs["intelligencePriority"] = value

        # Process speedPriority
        value = data.get("speedPriority")
        kwargs["speedPriority"] = value

        return cls(**kwargs)


@dataclass
class Notification(MCPBaseModel):
    method: "str"
    params: "None | NotificationParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = NotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class NotificationParams(MCPBaseModel):
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class NumberSchema(MCPBaseModel):
    type: "Literal['integer', 'number']"
    description: "None | str" = field(default=None)
    maximum: "None | int" = field(default=None)
    minimum: "None | int" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process maximum
        value = data.get("maximum")
        kwargs["maximum"] = value

        # Process minimum
        value = data.get("minimum")
        kwargs["minimum"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class PaginatedRequest(MCPBaseModel):
    id: "RequestId"
    method: "str"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    params: "None | PaginatedRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = PaginatedRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class PaginatedRequestParams(MCPBaseModel):
    cursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process cursor
        value = data.get("cursor")
        kwargs["cursor"] = value

        return cls(**kwargs)


@dataclass
class PaginatedResult(Result):
    _meta: "None | dict[str, Any]" = field(default=None)
    nextCursor: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process nextCursor
        value = data.get("nextCursor")
        kwargs["nextCursor"] = value

        return cls(**kwargs)


@dataclass
class PingRequest(MCPBaseModel):
    """
    A ping, issued by either the server or the client, to check that the other party
    is still alive. The receiver must promptly respond, or else may be disconnected.
    """

    id: "RequestId"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['ping']" = field(default="ping")
    params: "None | PingRequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = PingRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class PingRequestParams(MCPBaseModel):
    _meta: "None | PingRequestParams_meta" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        if value is not None:
            value = PingRequestParams_meta.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class PingRequestParams_meta(MCPBaseModel):
    """
    See [specification/2025-06-18/basic/index#general-fields] for notes on _meta
    usage.
    """

    progressToken: "None | ProgressToken" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process progressToken
        value = data.get("progressToken")
        kwargs["progressToken"] = value

        return cls(**kwargs)


@dataclass
class ProgressNotification(MCPBaseModel):
    """
    An out-of-band notification used to inform the receiver of a progress update for
    a long-running request.
    """

    params: "ProgressNotificationParams"
    method: "Literal['notifications/progress']" = field(
        default="notifications/progress"
    )

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ProgressNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ProgressNotificationParams(MCPBaseModel):
    progress: "float"
    progressToken: "ProgressToken"
    message: "None | str" = field(default=None)
    total: "None | float" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process message
        value = data.get("message")
        kwargs["message"] = value

        # Process progress
        value = data.get("progress")
        kwargs["progress"] = value

        # Process progressToken
        value = data.get("progressToken")
        kwargs["progressToken"] = value

        # Process total
        value = data.get("total")
        kwargs["total"] = value

        return cls(**kwargs)


@dataclass
class Prompt(MCPBaseModel):
    """A prompt or prompt template that the server offers."""

    name: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    arguments: "None | list[PromptArgument]" = field(default=None)
    description: "None | str" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process arguments
        value = data.get("arguments")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field arguments, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(PromptArgument.from_dict(item))
            value = converted_items
        kwargs["arguments"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        return cls(**kwargs)


@dataclass
class PromptArgument(MCPBaseModel):
    """Describes an argument that a prompt can accept."""

    name: "str"
    description: "None | str" = field(default=None)
    required: "None | bool" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process required
        value = data.get("required")
        kwargs["required"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        return cls(**kwargs)


@dataclass
class PromptListChangedNotification(MCPBaseModel):
    """
    An optional notification from the server to the client, informing it that the
    list of prompts it offers has changed. This may be issued by servers without any
    previous subscription from the client.
    """

    method: "Literal['notifications/prompts/list_changed']" = field(
        default="notifications/prompts/list_changed"
    )
    params: "None | PromptListChangedNotificationParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = PromptListChangedNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class PromptListChangedNotificationParams(MCPBaseModel):
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class PromptMessage(MCPBaseModel):
    """
    Describes a message returned as part of a prompt. This is similar to
    `SamplingMessage`, but also supports the embedding of resources from the MCP
    server.
    """

    content: "ContentBlock"
    role: "Role"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process content
        value = data.get("content")
        if value is not None:
            if isinstance(value, dict):
                # Try to disambiguate using const fields
                type_value = value.get("type")
                type_to_class = {}
                required_props_map = {}
                type_to_class["text"] = TextContent
                type_to_class["image"] = ImageContent
                type_to_class["audio"] = AudioContent
                type_to_class["resource_link"] = ResourceLink
                type_to_class["resource"] = EmbeddedResource
                if type_value is not None and type_value in type_to_class:
                    value = type_to_class[type_value].from_dict(value)
                else:
                    # Try to disambiguate by required properties
                    matches = []
                    for type_name, reqs in required_props_map.items():
                        if all(r in value for r in reqs):
                            matches.append(type_name)
                    if len(matches) == 1:
                        value = matches[0].from_dict(value)
                    elif len(matches) > 1:
                        match_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in matches
                        ]
                        raise ValueError(
                            f"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}"
                        )
                    else:
                        available_fields = list(value.keys())
                        type_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in required_props_map
                        ]
                        raise ValueError(
                            f"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}"
                        )
        kwargs["content"] = value

        # Process role
        value = data.get("role")
        kwargs["role"] = value

        return cls(**kwargs)


@dataclass
class PromptReference(MCPBaseModel):
    """Identifies a prompt."""

    name: "str"
    type: "Literal['ref/prompt']" = field(default="ref/prompt")
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class ReadResourceRequest(MCPBaseModel):
    """Sent from the client to the server, to read a specific resource URI."""

    id: "RequestId"
    params: "ReadResourceRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['resources/read']" = field(default="resources/read")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ReadResourceRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ReadResourceRequestParams(MCPBaseModel):
    uri: "str"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class ReadResourceResult(Result):
    """The server's response to a resources/read request from the client."""

    contents: "list[TextResourceContents | BlobResourceContents]"
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process contents
        value = data.get("contents")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field contents, got {type(value)}"
                )
            converted_items = []
            for item in value:
                # Try to disambiguate using const fields
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Expected a dict for union type TextResourceContents | BlobResourceContents, got {type(item)}"
                    )
                type_value = item.get("type")
                type_to_class = {}
                required_props_map = {}
                required_props_map[TextResourceContents] = ["text", "uri"]
                required_props_map[BlobResourceContents] = ["blob", "uri"]
                if type_value is not None and type_value in type_to_class:
                    converted_items.append(type_to_class[type_value].from_dict(item))
                else:
                    # Try to disambiguate by required properties
                    matches = []
                    for type_name, reqs in required_props_map.items():
                        if all(r in item for r in reqs):
                            matches.append(type_name)
                    if len(matches) == 1:
                        converted_items.append(matches[0].from_dict(item))
                    elif len(matches) > 1:
                        match_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in matches
                        ]
                        raise ValueError(
                            f"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}"
                        )
                    else:
                        available_fields = list(item.keys())
                        type_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in required_props_map
                        ]
                        raise ValueError(
                            f"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}"
                        )
            value = converted_items
        kwargs["contents"] = value

        return cls(**kwargs)


@dataclass
class Request(MCPBaseModel):
    id: "RequestId"
    method: "str"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    params: "None | RequestParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = RequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class RequestParams(MCPBaseModel):
    _meta: "None | RequestParams_meta" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        if value is not None:
            value = RequestParams_meta.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class RequestParams_meta(MCPBaseModel):
    """
    See [specification/2025-06-18/basic/index#general-fields] for notes on _meta
    usage.
    """

    progressToken: "None | ProgressToken" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process progressToken
        value = data.get("progressToken")
        kwargs["progressToken"] = value

        return cls(**kwargs)


@dataclass
class Resource(MCPBaseModel):
    """A known resource that the server is capable of reading."""

    name: "str"
    uri: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | Annotations" = field(default=None)
    description: "None | str" = field(default=None)
    mimeType: "None | str" = field(default=None)
    size: "None | int" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = Annotations.from_dict(value)
        kwargs["annotations"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process size
        value = data.get("size")
        kwargs["size"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class ResourceContents(MCPBaseModel):
    """The contents of a specific resource or sub-resource."""

    uri: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    mimeType: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class ResourceLink(MCPBaseModel):
    """
    A resource that the server is capable of reading, included in a prompt or tool
    call result. Note: resource links returned by tools are not guaranteed to appear
    in the results of `resources/list` requests.
    """

    name: "str"
    uri: "str"
    type: "Literal['resource_link']" = field(default="resource_link")
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | Annotations" = field(default=None)
    description: "None | str" = field(default=None)
    mimeType: "None | str" = field(default=None)
    size: "None | int" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = Annotations.from_dict(value)
        kwargs["annotations"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process size
        value = data.get("size")
        kwargs["size"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class ResourceListChangedNotification(MCPBaseModel):
    """
    An optional notification from the server to the client, informing it that the
    list of resources it can read from has changed. This may be issued by servers
    without any previous subscription from the client.
    """

    method: "Literal['notifications/resources/list_changed']" = field(
        default="notifications/resources/list_changed"
    )
    params: "None | ResourceListChangedNotificationParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ResourceListChangedNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ResourceListChangedNotificationParams(MCPBaseModel):
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class ResourceTemplate(MCPBaseModel):
    """A template description for resources available on the server."""

    name: "str"
    uriTemplate: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | Annotations" = field(default=None)
    description: "None | str" = field(default=None)
    mimeType: "None | str" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = Annotations.from_dict(value)
        kwargs["annotations"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process uriTemplate
        value = data.get("uriTemplate")
        kwargs["uriTemplate"] = value

        return cls(**kwargs)


@dataclass
class ResourceTemplateReference(MCPBaseModel):
    """A reference to a resource or resource template definition."""

    uri: "str"
    type: "Literal['ref/resource']" = field(default="ref/resource")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class ResourceUpdatedNotification(MCPBaseModel):
    """
    A notification from the server to the client, informing it that a resource has
    changed and may need to be read again. This should only be sent if the client
    previously sent a resources/subscribe request.
    """

    params: "ResourceUpdatedNotificationParams"
    method: "Literal['notifications/resources/updated']" = field(
        default="notifications/resources/updated"
    )

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ResourceUpdatedNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ResourceUpdatedNotificationParams(MCPBaseModel):
    uri: "str"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class Root(MCPBaseModel):
    """Represents a root directory or file that the server can operate on."""

    uri: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    name: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class RootsListChangedNotification(MCPBaseModel):
    """
    A notification from the client to the server, informing it that the list of roots
    has changed. This notification should be sent whenever the client adds, removes,
    or modifies any root. The server should then request an updated list of roots
    using the ListRootsRequest.
    """

    method: "Literal['notifications/roots/list_changed']" = field(
        default="notifications/roots/list_changed"
    )
    params: "None | RootsListChangedNotificationParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = RootsListChangedNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class RootsListChangedNotificationParams(MCPBaseModel):
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class SamplingMessage(MCPBaseModel):
    """Describes a message issued to or received from an LLM API."""

    content: "TextContent | ImageContent | AudioContent"
    role: "Role"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process content
        value = data.get("content")
        if value is not None:
            if isinstance(value, dict):
                # Try to disambiguate using const fields
                type_value = value.get("type")
                type_to_class = {}
                required_props_map = {}
                type_to_class["text"] = TextContent
                type_to_class["image"] = ImageContent
                type_to_class["audio"] = AudioContent
                if type_value is not None and type_value in type_to_class:
                    value = type_to_class[type_value].from_dict(value)
                else:
                    # Try to disambiguate by required properties
                    matches = []
                    for type_name, reqs in required_props_map.items():
                        if all(r in value for r in reqs):
                            matches.append(type_name)
                    if len(matches) == 1:
                        value = matches[0].from_dict(value)
                    elif len(matches) > 1:
                        match_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in matches
                        ]
                        raise ValueError(
                            f"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}"
                        )
                    else:
                        available_fields = list(value.keys())
                        type_details = [
                            f"{name} (requires any of {required_props_map[name]})"
                            for name in required_props_map
                        ]
                        raise ValueError(
                            f"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}"
                        )
        kwargs["content"] = value

        # Process role
        value = data.get("role")
        kwargs["role"] = value

        return cls(**kwargs)


@dataclass
class ServerCapabilities(MCPBaseModel):
    """
    Capabilities that a server may support. Known capabilities are defined here, in
    this schema, but this is not a closed set: any server can define its own,
    additional capabilities.
    """

    completions: "None | dict[str, Any]" = field(default=None)
    experimental: "None | dict[str, Any]" = field(default=None)
    logging: "None | dict[str, Any]" = field(default=None)
    prompts: "None | ServerCapabilitiesPromptsParams" = field(default=None)
    resources: "None | ServerCapabilitiesResourcesParams" = field(default=None)
    tools: "None | ServerCapabilitiesToolsParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process completions
        value = data.get("completions")
        kwargs["completions"] = value

        # Process experimental
        value = data.get("experimental")
        kwargs["experimental"] = value

        # Process logging
        value = data.get("logging")
        kwargs["logging"] = value

        # Process prompts
        value = data.get("prompts")
        if value is not None:
            value = ServerCapabilitiesPromptsParams.from_dict(value)
        kwargs["prompts"] = value

        # Process resources
        value = data.get("resources")
        if value is not None:
            value = ServerCapabilitiesResourcesParams.from_dict(value)
        kwargs["resources"] = value

        # Process tools
        value = data.get("tools")
        if value is not None:
            value = ServerCapabilitiesToolsParams.from_dict(value)
        kwargs["tools"] = value

        return cls(**kwargs)


@dataclass
class ServerCapabilitiesPromptsParams(MCPBaseModel):
    """Present if the server offers any prompt templates."""

    listChanged: "None | bool" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process listChanged
        value = data.get("listChanged")
        kwargs["listChanged"] = value

        return cls(**kwargs)


@dataclass
class ServerCapabilitiesResourcesParams(MCPBaseModel):
    """Present if the server offers any resources to read."""

    listChanged: "None | bool" = field(default=None)
    subscribe: "None | bool" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process listChanged
        value = data.get("listChanged")
        kwargs["listChanged"] = value

        # Process subscribe
        value = data.get("subscribe")
        kwargs["subscribe"] = value

        return cls(**kwargs)


@dataclass
class ServerCapabilitiesToolsParams(MCPBaseModel):
    """Present if the server offers any tools to call."""

    listChanged: "None | bool" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process listChanged
        value = data.get("listChanged")
        kwargs["listChanged"] = value

        return cls(**kwargs)


@dataclass
class SetLevelRequest(MCPBaseModel):
    """A request from the client to the server, to enable or adjust logging."""

    id: "RequestId"
    params: "SetLevelRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['logging/setLevel']" = field(default="logging/setLevel")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = SetLevelRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class SetLevelRequestParams(MCPBaseModel):
    level: "LoggingLevel"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process level
        value = data.get("level")
        kwargs["level"] = value

        return cls(**kwargs)


@dataclass
class StringSchema(MCPBaseModel):
    type: "Literal['string']" = field(default="string")
    description: "None | str" = field(default=None)
    format: "None | Literal['date', 'date-time', 'email', 'uri']" = field(default=None)
    maxLength: "None | int" = field(default=None)
    minLength: "None | int" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process format
        value = data.get("format")
        kwargs["format"] = value

        # Process maxLength
        value = data.get("maxLength")
        kwargs["maxLength"] = value

        # Process minLength
        value = data.get("minLength")
        kwargs["minLength"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class SubscribeRequest(MCPBaseModel):
    """
    Sent from the client to request resources/updated notifications from the server
    whenever a particular resource changes.
    """

    id: "RequestId"
    params: "SubscribeRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['resources/subscribe']" = field(default="resources/subscribe")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = SubscribeRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class SubscribeRequestParams(MCPBaseModel):
    uri: "str"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class TextContent(MCPBaseModel):
    """Text provided to or from an LLM."""

    text: "str"
    type: "Literal['text']" = field(default="text")
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = Annotations.from_dict(value)
        kwargs["annotations"] = value

        # Process text
        value = data.get("text")
        kwargs["text"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class TextResourceContents(MCPBaseModel):
    text: "str"
    uri: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    mimeType: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process text
        value = data.get("text")
        kwargs["text"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class Tool(MCPBaseModel):
    """Definition for a tool the client can call."""

    inputSchema: "ToolInputschemaParams"
    name: "str"
    _meta: "None | dict[str, Any]" = field(default=None)
    annotations: "None | ToolAnnotations" = field(default=None)
    description: "None | str" = field(default=None)
    outputSchema: "None | ToolOutputschemaParams" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        # Process annotations
        value = data.get("annotations")
        if value is not None:
            value = ToolAnnotations.from_dict(value)
        kwargs["annotations"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process inputSchema
        value = data.get("inputSchema")
        if value is not None:
            value = ToolInputschemaParams.from_dict(value)
        kwargs["inputSchema"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        # Process outputSchema
        value = data.get("outputSchema")
        if value is not None:
            value = ToolOutputschemaParams.from_dict(value)
        kwargs["outputSchema"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        return cls(**kwargs)


@dataclass
class ToolInputschemaParams(MCPBaseModel):
    """A JSON Schema object defining the expected parameters for the tool."""

    type: "Literal['object']" = field(default="object")
    properties: "None | dict[str, Any]" = field(default=None)
    required: "None | list[str]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process properties
        value = data.get("properties")
        kwargs["properties"] = value

        # Process required
        value = data.get("required")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field required, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["required"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class ToolOutputschemaParams(MCPBaseModel):
    """
    An optional JSON Schema object defining the structure of the tool's output
    returned in the structuredContent field of a CallToolResult.
    """

    type: "Literal['object']" = field(default="object")
    properties: "None | dict[str, Any]" = field(default=None)
    required: "None | list[str]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process properties
        value = data.get("properties")
        kwargs["properties"] = value

        # Process required
        value = data.get("required")
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for field required, got {type(value)}"
                )
            converted_items = []
            for item in value:
                converted_items.append(item)
            value = converted_items
        kwargs["required"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class ToolAnnotations(MCPBaseModel):
    """
    Additional properties describing a Tool to clients. NOTE: all properties in
    ToolAnnotations are **hints**. They are not guaranteed to provide a faithful
    description of tool behavior (including descriptive properties like `title`).
    Clients should never make tool use decisions based on ToolAnnotations received
    from untrusted servers.
    """

    destructiveHint: "None | bool" = field(default=None)
    idempotentHint: "None | bool" = field(default=None)
    openWorldHint: "None | bool" = field(default=None)
    readOnlyHint: "None | bool" = field(default=None)
    title: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process destructiveHint
        value = data.get("destructiveHint")
        kwargs["destructiveHint"] = value

        # Process idempotentHint
        value = data.get("idempotentHint")
        kwargs["idempotentHint"] = value

        # Process openWorldHint
        value = data.get("openWorldHint")
        kwargs["openWorldHint"] = value

        # Process readOnlyHint
        value = data.get("readOnlyHint")
        kwargs["readOnlyHint"] = value

        # Process title
        value = data.get("title")
        kwargs["title"] = value

        return cls(**kwargs)


@dataclass
class ToolListChangedNotification(MCPBaseModel):
    """
    An optional notification from the server to the client, informing it that the
    list of tools it offers has changed. This may be issued by servers without any
    previous subscription from the client.
    """

    method: "Literal['notifications/tools/list_changed']" = field(
        default="notifications/tools/list_changed"
    )
    params: "None | ToolListChangedNotificationParams" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = ToolListChangedNotificationParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ToolListChangedNotificationParams(MCPBaseModel):
    _meta: "None | dict[str, Any]" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process _meta
        value = data.get("_meta")
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class UnsubscribeRequest(MCPBaseModel):
    """
    Sent from the client to request cancellation of resources/updated notifications
    from the server. This should follow a previous resources/subscribe request.
    """

    id: "RequestId"
    params: "UnsubscribeRequestParams"
    jsonrpc: "Literal['2.0']" = field(default="2.0")
    method: "Literal['resources/unsubscribe']" = field(default="resources/unsubscribe")

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process jsonrpc
        value = data.get("jsonrpc")
        kwargs["jsonrpc"] = value

        # Process id
        value = data.get("id")
        kwargs["id"] = value

        # Process method
        value = data.get("method")
        kwargs["method"] = value

        # Process params
        value = data.get("params")
        if value is not None:
            value = UnsubscribeRequestParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class UnsubscribeRequestParams(MCPBaseModel):
    uri: "str"

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


_class_map: dict[str, Type[MCPBaseModel]] = {
    "tools/call": CallToolRequest,
    "notifications/cancelled": CancelledNotification,
    "completion/complete": CompleteRequest,
    "sampling/createMessage": CreateMessageRequest,
    "elicitation/create": ElicitRequest,
    "prompts/get": GetPromptRequest,
    "initialize": InitializeRequest,
    "notifications/initialized": InitializedNotification,
    "prompts/list": ListPromptsRequest,
    "resources/templates/list": ListResourceTemplatesRequest,
    "resources/list": ListResourcesRequest,
    "roots/list": ListRootsRequest,
    "tools/list": ListToolsRequest,
    "notifications/message": LoggingMessageNotification,
    "ping": PingRequest,
    "notifications/progress": ProgressNotification,
    "notifications/prompts/list_changed": PromptListChangedNotification,
    "resources/read": ReadResourceRequest,
    "notifications/resources/list_changed": ResourceListChangedNotification,
    "notifications/resources/updated": ResourceUpdatedNotification,
    "notifications/roots/list_changed": RootsListChangedNotification,
    "logging/setLevel": SetLevelRequest,
    "resources/subscribe": SubscribeRequest,
    "notifications/tools/list_changed": ToolListChangedNotification,
    "resources/unsubscribe": UnsubscribeRequest,
}

_request_to_result_map: dict[Type[MCPBaseModel], Type[MCPBaseModel]] = {
    CallToolRequest: CallToolResult,
    CompleteRequest: CompleteResult,
    CreateMessageRequest: CreateMessageResult,
    ElicitRequest: ElicitResult,
    GetPromptRequest: GetPromptResult,
    InitializeRequest: InitializeResult,
    ListPromptsRequest: ListPromptsResult,
    ListResourceTemplatesRequest: ListResourceTemplatesResult,
    ListResourcesRequest: ListResourcesResult,
    ListRootsRequest: ListRootsResult,
    ListToolsRequest: ListToolsResult,
    ReadResourceRequest: ReadResourceResult,
}

# Type aliases and unions

# Type alias for clientnotification
ClientNotification = (
    CancelledNotification
    | InitializedNotification
    | ProgressNotification
    | RootsListChangedNotification
)

# Type alias for clientrequest
ClientRequest = (
    InitializeRequest
    | PingRequest
    | ListResourcesRequest
    | ListResourceTemplatesRequest
    | ReadResourceRequest
    | SubscribeRequest
    | UnsubscribeRequest
    | ListPromptsRequest
    | GetPromptRequest
    | ListToolsRequest
    | CallToolRequest
    | SetLevelRequest
    | CompleteRequest
)

# Type alias for clientresult
ClientResult = Result | CreateMessageResult | ListRootsResult | ElicitResult

# Type alias for contentblock
ContentBlock = (
    TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource
)

# Type alias for jsonrpcmessage
JSONRPCMessage = JSONRPCRequest | JSONRPCNotification | JSONRPCResponse | JSONRPCError

# Type alias for logginglevel
LoggingLevel = Literal[
    "alert", "critical", "debug", "emergency", "error", "info", "notice", "warning"
]

# Type alias for primitiveschemadefinition
PrimitiveSchemaDefinition = StringSchema | NumberSchema | BooleanSchema | EnumSchema

# Type alias for progresstoken
ProgressToken = str | int

# Type alias for requestid
RequestId = str | int

# Type alias for role
Role = Literal["assistant", "user"]

# Type alias for servernotification
ServerNotification = (
    CancelledNotification
    | ProgressNotification
    | ResourceListChangedNotification
    | ResourceUpdatedNotification
    | PromptListChangedNotification
    | ToolListChangedNotification
    | LoggingMessageNotification
)

# Type alias for serverrequest
ServerRequest = PingRequest | CreateMessageRequest | ListRootsRequest | ElicitRequest

# Type alias for serverresult
ServerResult = (
    Result
    | InitializeResult
    | ListResourcesResult
    | ListResourceTemplatesResult
    | ReadResourceResult
    | ListPromptsResult
    | GetPromptResult
    | ListToolsResult
    | CallToolResult
    | CompleteResult
)
