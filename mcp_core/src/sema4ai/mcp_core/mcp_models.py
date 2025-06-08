from typing import Any, TypeVar, Literal, Type
from dataclasses import dataclass, field
from sema4ai.mcp_core.mcp_base_model import BaseModel

T = TypeVar("T")


@dataclass
class Annotations(BaseModel):
    """Optional annotations for the client. The client can use annotations to inform how
    objects are used or displayed"""

    audience: "None | list[Role]" = field(default=None)
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(item)
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["audience"] = value

        # Process priority
        value = data.get("priority")
        kwargs["priority"] = value

        return cls(**kwargs)


@dataclass
class AudioContent(BaseModel):
    """Audio provided to or from an LLM."""

    data: "str"
    mimeType: "str"
    type: "Literal['audio']"
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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
class BlobResourceContents(BaseModel):
    blob: "str"
    uri: "str"
    mimeType: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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
class CallToolRequest(BaseModel):
    """Used by the client to invoke a tool provided by the server."""

    method: "Literal['tools/call']"
    params: "CallToolRequestParamsParams"

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
            value = CallToolRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CallToolRequestParamsParams(BaseModel):
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
class CallToolResult(BaseModel):
    """The server's response to a tool call. Any errors that originate from the tool
    SHOULD be reported inside the result object, with `isError` set to true, _not_ as
    an MCP protocol-level error response. Otherwise, the LLM would not be able to see
    that an error occurred and self-correct. However, any errors in _finding_ the
    tool, an error indicating that the server does not support tool calls, or any
    other exceptional conditions, should be reported as an MCP error response."""

    content: "list[TextContent | ImageContent | AudioContent | EmbeddedResource]"
    _meta: "None | dict[str, Any]" = field(default=None)
    isError: "None | bool" = field(default=None)

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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        # Try to disambiguate using const fields
                        type_value = item.get("type")
                        type_to_class = {}
                        required_props_map = {}
                        type_to_class["text"] = TextContent
                        type_to_class["image"] = ImageContent
                        type_to_class["audio"] = AudioContent
                        type_to_class["resource"] = EmbeddedResource
                        if type_value is not None and type_value in type_to_class:
                            converted_items.append(
                                type_to_class[type_value].from_dict(item)
                            )
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
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["content"] = value

        # Process isError
        value = data.get("isError")
        kwargs["isError"] = value

        return cls(**kwargs)


@dataclass
class CancelledNotification(BaseModel):
    """This notification can be sent by either side to indicate that it is cancelling a
    previously-issued request. The request SHOULD still be in-flight, but due to
    communication latency, it is always possible that this notification MAY arrive
    after the request has already finished. This notification indicates that the
    result will be unused, so any associated processing SHOULD cease. A client MUST
    NOT attempt to cancel its `initialize` request."""

    method: "Literal['notifications/cancelled']"
    params: "CancelledNotificationParamsParams"

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
            value = CancelledNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CancelledNotificationParamsParams(BaseModel):
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
class ClientCapabilities(BaseModel):
    """Capabilities a client may support. Known capabilities are defined here, in this
    schema, but this is not a closed set: any client can define its own, additional
    capabilities."""

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
class ClientCapabilitiesRootsParams(BaseModel):
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
class CompleteRequest(BaseModel):
    """A request from the client to the server, to ask for completion options."""

    method: "Literal['completion/complete']"
    params: "CompleteRequestParamsParams"

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
            value = CompleteRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CompleteRequestParamsParams(BaseModel):
    argument: "CompleteRequestParamsParamsArgumentParams"
    ref: "PromptReference | ResourceReference"

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
            value = CompleteRequestParamsParamsArgumentParams.from_dict(value)
        kwargs["argument"] = value

        # Process ref
        value = data.get("ref")
        if value is not None:
            if isinstance(value, dict):
                # Try to disambiguate using const fields
                type_value = value.get("type")
                type_to_class = {}
                required_props_map = {}
                type_to_class["ref/prompt"] = PromptReference
                type_to_class["ref/resource"] = ResourceReference
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
class CompleteRequestParamsParamsArgumentParams(BaseModel):
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
class CompleteResult(BaseModel):
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
class CompleteResultCompletionParams(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(item)
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["values"] = value

        return cls(**kwargs)


@dataclass
class CreateMessageRequest(BaseModel):
    """A request from the server to sample an LLM via the client. The client has full
    discretion over which model to select. The client should also inform the user
    before beginning sampling, to allow them to inspect the request (human in the
    loop) and decide whether to approve it."""

    method: "Literal['sampling/createMessage']"
    params: "CreateMessageRequestParamsParams"

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
            value = CreateMessageRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class CreateMessageRequestParamsParams(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(SamplingMessage.from_dict(item))
                    else:
                        converted_items.append(item)
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(item)
                    else:
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
class CreateMessageResult(BaseModel):
    """The client's response to a sampling/create_message request from the server. The
    client should inform the user before returning the sampled message, to allow them
    to inspect the response (human in the loop) and decide whether to allow the server
    to see it."""

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
class EmbeddedResource(BaseModel):
    """The contents of a resource, embedded into a prompt or tool call result. It is up
    to the client how best to render embedded resources for the benefit of the LLM
    and/or the user."""

    resource: "TextResourceContents | BlobResourceContents"
    type: "Literal['resource']"
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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
class GetPromptRequest(BaseModel):
    """Used by the client to get a prompt provided by the server."""

    method: "Literal['prompts/get']"
    params: "GetPromptRequestParamsParams"

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
            value = GetPromptRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class GetPromptRequestParamsParams(BaseModel):
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
class GetPromptResult(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(PromptMessage.from_dict(item))
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["messages"] = value

        return cls(**kwargs)


@dataclass
class ImageContent(BaseModel):
    """An image provided to or from an LLM."""

    data: "str"
    mimeType: "str"
    type: "Literal['image']"
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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
class Implementation(BaseModel):
    """Describes the name and version of an MCP implementation."""

    name: "str"
    version: "str"

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

        # Process version
        value = data.get("version")
        kwargs["version"] = value

        return cls(**kwargs)


@dataclass
class InitializeRequest(BaseModel):
    """This request is sent from the client to the server when it first connects, asking
    it to begin initialization."""

    method: "Literal['initialize']"
    params: "InitializeRequestParamsParams"

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
            value = InitializeRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class InitializeRequestParamsParams(BaseModel):
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
class InitializeResult(BaseModel):
    """After receiving an initialize request from the client, the server sends this
    response."""

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
class InitializedNotification(BaseModel):
    """This notification is sent from the client to the server after initialization has
    finished."""

    method: "Literal['notifications/initialized']"
    params: "None | InitializedNotificationParamsParams" = field(default=None)

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
            value = InitializedNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class InitializedNotificationParamsParams(BaseModel):
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
class JSONRPCError(BaseModel):
    """A response to a request that indicates an error occurred."""

    error: "JSONRPCErrorErrorParams"
    id: "RequestId"
    jsonrpc: "Literal['2.0']"

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
class JSONRPCErrorErrorParams(BaseModel):
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
class JSONRPCNotification(BaseModel):
    """A notification which does not expect a response."""

    jsonrpc: "Literal['2.0']"
    method: "str"
    params: "None | JSONRPCNotificationParamsParams" = field(default=None)

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
            value = JSONRPCNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCNotificationParamsParams(BaseModel):
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
class JSONRPCRequest(BaseModel):
    """A request that expects a response."""

    id: "RequestId"
    jsonrpc: "Literal['2.0']"
    method: "str"
    params: "None | JSONRPCRequestParamsParams" = field(default=None)

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
            value = JSONRPCRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCRequestParamsParams(BaseModel):
    _meta: "None | JSONRPCRequestParamsParams_metaParams" = field(default=None)

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
            value = JSONRPCRequestParamsParams_metaParams.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class JSONRPCRequestParamsParams_metaParams(BaseModel):
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
class JSONRPCResponse(BaseModel):
    """A successful (non-error) response to a request."""

    id: "RequestId"
    jsonrpc: "Literal['2.0']"
    result: "Result"

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
class ListPromptsRequest(BaseModel):
    """Sent from the client to request a list of prompts and prompt templates the server
    has."""

    method: "Literal['prompts/list']"
    params: "None | ListPromptsRequestParamsParams" = field(default=None)

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
            value = ListPromptsRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListPromptsRequestParamsParams(BaseModel):
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
class ListPromptsResult(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(Prompt.from_dict(item))
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["prompts"] = value

        return cls(**kwargs)


@dataclass
class ListResourceTemplatesRequest(BaseModel):
    """Sent from the client to request a list of resource templates the server has."""

    method: "Literal['resources/templates/list']"
    params: "None | ListResourceTemplatesRequestParamsParams" = field(default=None)

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
            value = ListResourceTemplatesRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListResourceTemplatesRequestParamsParams(BaseModel):
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
class ListResourceTemplatesResult(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(ResourceTemplate.from_dict(item))
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["resourceTemplates"] = value

        return cls(**kwargs)


@dataclass
class ListResourcesRequest(BaseModel):
    """Sent from the client to request a list of resources the server has."""

    method: "Literal['resources/list']"
    params: "None | ListResourcesRequestParamsParams" = field(default=None)

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
            value = ListResourcesRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListResourcesRequestParamsParams(BaseModel):
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
class ListResourcesResult(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(Resource.from_dict(item))
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["resources"] = value

        return cls(**kwargs)


@dataclass
class ListRootsRequest(BaseModel):
    """Sent from the server to request a list of root URIs from the client. Roots allow
    servers to ask for specific directories or files to operate on. A common example
    for roots is providing a set of repositories or directories a server should
    operate on. This request is typically used when the server needs to understand the
    file system structure or access specific locations that the client has permission
    to read from."""

    method: "Literal['roots/list']"
    params: "None | ListRootsRequestParamsParams" = field(default=None)

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
            value = ListRootsRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListRootsRequestParamsParams(BaseModel):
    _meta: "None | ListRootsRequestParamsParams_metaParams" = field(default=None)

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
            value = ListRootsRequestParamsParams_metaParams.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class ListRootsRequestParamsParams_metaParams(BaseModel):
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
class ListRootsResult(BaseModel):
    """The client's response to a roots/list request from the server. This result
    contains an array of Root objects, each representing a root directory or file that
    the server can operate on."""

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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(Root.from_dict(item))
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["roots"] = value

        return cls(**kwargs)


@dataclass
class ListToolsRequest(BaseModel):
    """Sent from the client to request a list of tools the server has."""

    method: "Literal['tools/list']"
    params: "None | ListToolsRequestParamsParams" = field(default=None)

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
            value = ListToolsRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ListToolsRequestParamsParams(BaseModel):
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
class ListToolsResult(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(Tool.from_dict(item))
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["tools"] = value

        return cls(**kwargs)


# Type alias for logginglevel
LoggingLevel = Literal[
    "alert", "critical", "debug", "emergency", "error", "info", "notice", "warning"
]


@dataclass
class LoggingMessageNotification(BaseModel):
    """Notification of a log message passed from server to client. If no
    logging/setLevel request has been sent from the client, the server MAY decide
    which messages to send automatically."""

    method: "Literal['notifications/message']"
    params: "LoggingMessageNotificationParamsParams"

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
            value = LoggingMessageNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class LoggingMessageNotificationParamsParams(BaseModel):
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
        if value is not None:
            value = LoggingLevel.from_dict(value)
        kwargs["level"] = value

        # Process logger
        value = data.get("logger")
        kwargs["logger"] = value

        return cls(**kwargs)


@dataclass
class ModelHint(BaseModel):
    """Hints to use for model selection. Keys not declared here are currently left
    unspecified by the spec and are up to the client to interpret."""

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
class ModelPreferences(BaseModel):
    """The server's preferences for model selection, requested of the client during
    sampling. Because LLMs can vary along multiple dimensions, choosing the "best"
    model is rarely straightforward. Different models excel in different areas—some
    are faster but less capable, others are more capable but more expensive, and so
    on. This interface allows servers to express their priorities across multiple
    dimensions to help clients make an appropriate selection for their use case. These
    preferences are always advisory. The client MAY ignore them. It is also up to the
    client to decide how to interpret these preferences and how to balance them
    against other considerations."""

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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(ModelHint.from_dict(item))
                    else:
                        converted_items.append(item)
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
class Notification(BaseModel):
    method: "str"
    params: "None | NotificationParamsParams" = field(default=None)

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
            value = NotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class NotificationParamsParams(BaseModel):
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
class PaginatedRequest(BaseModel):
    method: "str"
    params: "None | PaginatedRequestParamsParams" = field(default=None)

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
            value = PaginatedRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class PaginatedRequestParamsParams(BaseModel):
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
class PaginatedResult(BaseModel):
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
class PingRequest(BaseModel):
    """A ping, issued by either the server or the client, to check that the other party
    is still alive. The receiver must promptly respond, or else may be disconnected."""

    method: "Literal['ping']"
    params: "None | PingRequestParamsParams" = field(default=None)

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
            value = PingRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class PingRequestParamsParams(BaseModel):
    _meta: "None | PingRequestParamsParams_metaParams" = field(default=None)

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
            value = PingRequestParamsParams_metaParams.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class PingRequestParamsParams_metaParams(BaseModel):
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
class ProgressNotification(BaseModel):
    """An out-of-band notification used to inform the receiver of a progress update for
    a long-running request."""

    method: "Literal['notifications/progress']"
    params: "ProgressNotificationParamsParams"

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
            value = ProgressNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ProgressNotificationParamsParams(BaseModel):
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


# Type alias for progresstoken
ProgressToken = str | int


@dataclass
class Prompt(BaseModel):
    """A prompt or prompt template that the server offers."""

    name: "str"
    arguments: "None | list[PromptArgument]" = field(default=None)
    description: "None | str" = field(default=None)

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
        if value is not None:
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(PromptArgument.from_dict(item))
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["arguments"] = value

        # Process description
        value = data.get("description")
        kwargs["description"] = value

        # Process name
        value = data.get("name")
        kwargs["name"] = value

        return cls(**kwargs)


@dataclass
class PromptArgument(BaseModel):
    """Describes an argument that a prompt can accept."""

    name: "str"
    description: "None | str" = field(default=None)
    required: "None | bool" = field(default=None)

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

        return cls(**kwargs)


@dataclass
class PromptListChangedNotification(BaseModel):
    """An optional notification from the server to the client, informing it that the
    list of prompts it offers has changed. This may be issued by servers without any
    previous subscription from the client."""

    method: "Literal['notifications/prompts/list_changed']"
    params: "None | PromptListChangedNotificationParamsParams" = field(default=None)

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
            value = PromptListChangedNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class PromptListChangedNotificationParamsParams(BaseModel):
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
class PromptMessage(BaseModel):
    """Describes a message returned as part of a prompt. This is similar to
    `SamplingMessage`, but also supports the embedding of resources from the MCP
    server."""

    content: "TextContent | ImageContent | AudioContent | EmbeddedResource"
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
class PromptReference(BaseModel):
    """Identifies a prompt."""

    name: "str"
    type: "Literal['ref/prompt']"

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

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class ReadResourceRequest(BaseModel):
    """Sent from the client to the server, to read a specific resource URI."""

    method: "Literal['resources/read']"
    params: "ReadResourceRequestParamsParams"

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
            value = ReadResourceRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ReadResourceRequestParamsParams(BaseModel):
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
class ReadResourceResult(BaseModel):
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        # Try to disambiguate using const fields
                        type_value = item.get("type")
                        type_to_class = {}
                        required_props_map = {}
                        required_props_map[TextResourceContents] = ["text", "uri"]
                        required_props_map[BlobResourceContents] = ["blob", "uri"]
                        if type_value is not None and type_value in type_to_class:
                            converted_items.append(
                                type_to_class[type_value].from_dict(item)
                            )
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
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["contents"] = value

        return cls(**kwargs)


@dataclass
class Request(BaseModel):
    method: "str"
    params: "None | RequestParamsParams" = field(default=None)

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
            value = RequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class RequestParamsParams(BaseModel):
    _meta: "None | RequestParamsParams_metaParams" = field(default=None)

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
            value = RequestParamsParams_metaParams.from_dict(value)
        kwargs["_meta"] = value

        return cls(**kwargs)


@dataclass
class RequestParamsParams_metaParams(BaseModel):
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


# Type alias for requestid
RequestId = str | int


@dataclass
class Resource(BaseModel):
    """A known resource that the server is capable of reading."""

    name: "str"
    uri: "str"
    annotations: "None | Annotations" = field(default=None)
    description: "None | str" = field(default=None)
    mimeType: "None | str" = field(default=None)
    size: "None | int" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class ResourceContents(BaseModel):
    """The contents of a specific resource or sub-resource."""

    uri: "str"
    mimeType: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
        # Process mimeType
        value = data.get("mimeType")
        kwargs["mimeType"] = value

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class ResourceListChangedNotification(BaseModel):
    """An optional notification from the server to the client, informing it that the
    list of resources it can read from has changed. This may be issued by servers
    without any previous subscription from the client."""

    method: "Literal['notifications/resources/list_changed']"
    params: "None | ResourceListChangedNotificationParamsParams" = field(default=None)

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
            value = ResourceListChangedNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ResourceListChangedNotificationParamsParams(BaseModel):
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
class ResourceReference(BaseModel):
    """A reference to a resource or resource template definition."""

    type: "Literal['ref/resource']"
    uri: "str"

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
class ResourceTemplate(BaseModel):
    """A template description for resources available on the server."""

    name: "str"
    uriTemplate: "str"
    annotations: "None | Annotations" = field(default=None)
    description: "None | str" = field(default=None)
    mimeType: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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

        # Process uriTemplate
        value = data.get("uriTemplate")
        kwargs["uriTemplate"] = value

        return cls(**kwargs)


@dataclass
class ResourceUpdatedNotification(BaseModel):
    """A notification from the server to the client, informing it that a resource has
    changed and may need to be read again. This should only be sent if the client
    previously sent a resources/subscribe request."""

    method: "Literal['notifications/resources/updated']"
    params: "ResourceUpdatedNotificationParamsParams"

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
            value = ResourceUpdatedNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ResourceUpdatedNotificationParamsParams(BaseModel):
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
class Result(BaseModel):
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


# Type alias for role
Role = Literal["assistant", "user"]


@dataclass
class Root(BaseModel):
    """Represents a root directory or file that the server can operate on."""

    uri: "str"
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

        # Process uri
        value = data.get("uri")
        kwargs["uri"] = value

        return cls(**kwargs)


@dataclass
class RootsListChangedNotification(BaseModel):
    """A notification from the client to the server, informing it that the list of roots
    has changed. This notification should be sent whenever the client adds, removes,
    or modifies any root. The server should then request an updated list of roots
    using the ListRootsRequest."""

    method: "Literal['notifications/roots/list_changed']"
    params: "None | RootsListChangedNotificationParamsParams" = field(default=None)

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
            value = RootsListChangedNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class RootsListChangedNotificationParamsParams(BaseModel):
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
class SamplingMessage(BaseModel):
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
class ServerCapabilities(BaseModel):
    """Capabilities that a server may support. Known capabilities are defined here, in
    this schema, but this is not a closed set: any server can define its own,
    additional capabilities."""

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
class ServerCapabilitiesPromptsParams(BaseModel):
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
class ServerCapabilitiesResourcesParams(BaseModel):
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
class ServerCapabilitiesToolsParams(BaseModel):
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
class SetLevelRequest(BaseModel):
    """A request from the client to the server, to enable or adjust logging."""

    method: "Literal['logging/setLevel']"
    params: "SetLevelRequestParamsParams"

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
            value = SetLevelRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class SetLevelRequestParamsParams(BaseModel):
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
        if value is not None:
            value = LoggingLevel.from_dict(value)
        kwargs["level"] = value

        return cls(**kwargs)


@dataclass
class SubscribeRequest(BaseModel):
    """Sent from the client to request resources/updated notifications from the server
    whenever a particular resource changes."""

    method: "Literal['resources/subscribe']"
    params: "SubscribeRequestParamsParams"

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
            value = SubscribeRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class SubscribeRequestParamsParams(BaseModel):
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
class TextContent(BaseModel):
    """Text provided to or from an LLM."""

    text: "str"
    type: "Literal['text']"
    annotations: "None | Annotations" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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
class TextResourceContents(BaseModel):
    text: "str"
    uri: "str"
    mimeType: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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
class Tool(BaseModel):
    """Definition for a tool the client can call."""

    inputSchema: "ToolInputschemaParams"
    name: "str"
    annotations: "None | ToolAnnotations" = field(default=None)
    description: "None | str" = field(default=None)

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}"
            )
        kwargs = {}
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

        return cls(**kwargs)


@dataclass
class ToolInputschemaParams(BaseModel):
    """A JSON Schema object defining the expected parameters for the tool."""

    type: "Literal['object']"
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
            if isinstance(value, list):
                converted_items = []
                for item in value:
                    if isinstance(item, dict):
                        converted_items.append(item)
                    else:
                        converted_items.append(item)
                value = converted_items
        kwargs["required"] = value

        # Process type
        value = data.get("type")
        kwargs["type"] = value

        return cls(**kwargs)


@dataclass
class ToolAnnotations(BaseModel):
    """Additional properties describing a Tool to clients. NOTE: all properties in
    ToolAnnotations are **hints**. They are not guaranteed to provide a faithful
    description of tool behavior (including descriptive properties like `title`).
    Clients should never make tool use decisions based on ToolAnnotations received
    from untrusted servers."""

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
class ToolListChangedNotification(BaseModel):
    """An optional notification from the server to the client, informing it that the
    list of tools it offers has changed. This may be issued by servers without any
    previous subscription from the client."""

    method: "Literal['notifications/tools/list_changed']"
    params: "None | ToolListChangedNotificationParamsParams" = field(default=None)

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
            value = ToolListChangedNotificationParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class ToolListChangedNotificationParamsParams(BaseModel):
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
class UnsubscribeRequest(BaseModel):
    """Sent from the client to request cancellation of resources/updated notifications
    from the server. This should follow a previous resources/subscribe request."""

    method: "Literal['resources/unsubscribe']"
    params: "UnsubscribeRequestParamsParams"

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
            value = UnsubscribeRequestParamsParams.from_dict(value)
        kwargs["params"] = value

        return cls(**kwargs)


@dataclass
class UnsubscribeRequestParamsParams(BaseModel):
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


_class_map: dict[str, Type[BaseModel]] = {
    "tools/call": CallToolRequest,
    "notifications/cancelled": CancelledNotification,
    "completion/complete": CompleteRequest,
    "sampling/createMessage": CreateMessageRequest,
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
