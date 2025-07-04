from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field

# TODO: Remove this once the files module is implemented
UploadedFile = Any


class PromptTextContent(BaseModel):
    """Represents a text message in the agent system.

    This class handles plain text content, ensuring that the text is non-empty
    and properly typed.
    """

    text: Annotated[
        str,
        Field(description="The actual text content of the message"),
    ]

    kind: Annotated[
        Literal["text"],
        Field(
            default="text",
            description="Message kind identifier, always 'text'",
        ),
    ] = "text"


class PromptImageContent(BaseModel):
    """Represents an image message in the agent system.

    This class handles image content in either URL or base64 format, with support
    for different resolutions and image formats.
    """

    mime_type: Annotated[
        Literal["image/jpeg", "image/png", "image/gif", "image/webp"],
        Field(description="MIME type of the image"),
    ]

    value: Annotated[
        str | bytes,
        Field(
            description="The image data - either a URL or base64 encoded string, or raw bytes",
        ),
    ]

    kind: Annotated[
        Literal["image"],
        Field(
            default="image",
            description="Message kind identifier, always 'image'",
        ),
    ] = "image"

    sub_type: Annotated[
        Literal["url", "base64", "raw_bytes"],
        Field(
            default="url",
            description="Format of the image data - either a URL or base64"
            "encoded string, or raw bytes",
        ),
    ] = "url"

    detail: Annotated[
        Literal["low_res", "high_res"],
        Field(
            default="high_res",
            description="Resolution quality of the image",
        ),
    ] = "high_res"


class PromptAudioContent(BaseModel):
    """Represents an audio message in the agent system.

    This class handles audio content in base64 format, supporting
    common audio formats like WAV and MP3.
    """

    mime_type: Annotated[
        Literal["audio/wav", "audio/mp3"],
        Field(description="MIME type of the audio"),
    ]

    value: Annotated[
        str,
        Field(description="The base64 encoded audio data"),
    ]

    kind: Annotated[
        Literal["audio"],
        Field(
            default="audio",
            description="Message kind identifier, always 'audio'",
        ),
    ] = "audio"

    sub_type: Annotated[
        Literal["base64", "url"],
        Field(
            default="base64",
            description="Format of the audio data - url-based or base64-encoded",
        ),
    ] = "base64"


class PromptDocumentContent(BaseModel):
    """Represents a document message in the agent system.

    This class handles document content in either URL or base64 format, with support
    for different resolutions and image formats.
    """

    mime_type: Annotated[
        Literal[
            "application/pdf",
            "text/plain",
            "text/csv",
            "text/tab-separated-values",
            "text/markdown",
            "text/html",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
        Field(description="MIME type of the document"),
    ]

    value: Annotated[
        str | bytes | UploadedFile,
        Field(
            description="The document data - either an agent-server UploadedFile, "
            "base64 encoded string, or raw bytes",
        ),
    ]

    name: Annotated[
        str,
        Field(
            description="The name of the document",
        ),
    ]

    kind: Annotated[
        Literal["document"],
        Field(
            default="document",
            description="Message kind identifier, always 'document'",
        ),
    ] = "document"

    sub_type: Annotated[
        Literal["UploadedFile", "base64", "raw_bytes", "url"],
        Field(
            default="UploadedFile",
            description="Format of the document data - UploadedFile, base64 encoded string, raw bytes, or URL",
        ),
    ] = "UploadedFile"


class PromptToolResultContent(BaseModel):
    """Represents the result of a tool execution in the agent system.

    This class encapsulates the output from a tool execution, which can include
    text and image content, along with status information about the execution.
    """

    tool_name: Annotated[
        str,
        Field(description="Name of the tool that produced this result"),
    ]

    tool_call_id: Annotated[
        str,
        Field(
            description="Identifier linking this result to its original tool call",
        ),
    ]

    content: Annotated[
        list[
            Annotated[
                Union[
                    PromptTextContent,
                    PromptImageContent,
                    PromptAudioContent,
                    PromptDocumentContent,
                ],
                Field(discriminator="kind"),
            ]
        ],
        Field(
            description="List of content items produced by the tool execution",
        ),
    ]

    is_error: Annotated[
        bool,
        Field(
            default=False,
            description="Indicates whether the tool execution resulted in an error",
        ),
    ] = False

    kind: Annotated[
        Literal["tool_result"],
        Field(
            default="tool_result",
            description="Message kind identifier, always 'tool_result'",
        ),
    ] = "tool_result"


class PromptToolUseContent(BaseModel):
    """Represents a message containing a tool use request from an AI agent.

    This class handles tool usage requests from different LLM providers
    (OpenAI, Claude), normalizing their different input formats into a
    consistent structure.

    Raises:
        json.JSONDecodeError: If tool_input_raw is a string and cannot be
        parsed as valid JSON.
        AssertionError: If type field doesn't match the literal "tool_use".
    """

    tool_call_id: Annotated[
        str,
        Field(description="Unique identifier for this tool call"),
    ]

    tool_name: Annotated[
        str,
        Field(description="Name of the tool being requested"),
    ]

    tool_input_raw: Annotated[
        dict[str, Any] | str,
        Field(
            description="Raw tool input, either JSON string (OpenAI) or dict (Claude)",
        ),
    ]

    kind: Annotated[
        Literal["tool_use"],
        Field(
            default="tool_use",
            description="Message kind identifier, always 'tool_use'",
        ),
    ] = "tool_use"


class PromptAgentMessage(BaseModel):
    """Represents an agent message in the prompt."""

    content: Annotated[
        list[
            Annotated[
                Union[PromptTextContent, PromptToolUseContent],
                Field(discriminator="kind"),
            ]
        ],
        Field(description="The contents of the prompt message"),
    ]

    role: Annotated[
        Literal["agent"],
        Field(
            default="agent",
            description="The role of the message sender",
        ),
    ] = "agent"


class PromptUserMessage(BaseModel):
    """Represents a user message in the prompt."""

    content: Annotated[
        list[
            Annotated[
                Union[
                    PromptTextContent,
                    PromptImageContent,
                    PromptAudioContent,
                    PromptToolResultContent,
                    PromptDocumentContent,
                ],
                Field(discriminator="kind"),
            ],
        ],
        Field(description="The contents of the prompt message"),
    ]

    role: Annotated[
        Literal["user"],
        Field(
            default="user",
            description="The role of the message sender",
        ),
    ] = "user"


class ConversationHistoryParams(BaseModel):
    """Parameters for the conversation history special message."""

    maximum_number_of_turns: Annotated[
        int,
        Field(
            default=5,
            description="The maximum number of turns to include in the conversation history.",
        ),
    ] = 5

    token_budget_as_percentage: Annotated[
        float,
        Field(
            default=0.50,
            description="The token budget as a percentage of the total token budget.",
        ),
    ] = 0.50


class ConversationHistorySpecialMessage(BaseModel):
    """Special message for including the conversation history in a prompt."""

    role: Annotated[
        Literal["$conversation-history"], Field(default="$conversation-history")
    ] = "$conversation-history"

    params: Annotated[
        ConversationHistoryParams,
        Field(default_factory=ConversationHistoryParams),
    ]


class DocumentsParams(BaseModel):
    """Parameters for the documents special message."""

    maximum_number_of_documents: Annotated[
        int,
        Field(
            default=5,
            description="The maximum number of documents to include in the prompt.",
        ),
    ] = 5

    token_budget_as_percentage: Annotated[
        float,
        Field(
            default=0.50,
            description="The token budget as a percentage of the total token budget.",
        ),
    ] = 0.50


class DocumentsSpecialMessage(BaseModel):
    """Special message for including the documents in a prompt."""

    role: Annotated[Literal["$documents"], Field(default="$documents")] = "$documents"

    params: Annotated[
        DocumentsParams,
        Field(default_factory=DocumentsParams),
    ]


class MemoriesParams(BaseModel):
    """Parameters for the memories special message."""

    maximum_number_of_memories: Annotated[
        int,
        Field(
            default=20,
            description="The maximum number of memories to include in the prompt.",
        ),
    ] = 20

    token_budget_as_percentage: Annotated[
        float,
        Field(
            default=0.50,
            description="The token budget as a percentage of the total token budget.",
        ),
    ] = 0.50


class MemoriesSpecialMessage(BaseModel):
    """Special message for including the memories in a prompt."""

    role: Annotated[Literal["$memories"], Field(default="$memories")] = "$memories"

    params: Annotated[
        MemoriesParams,
        Field(default_factory=MemoriesParams),
    ]


class ToolDefinition(BaseModel):
    """Represents the definition of a tool."""

    name: Annotated[
        str,
        Field(description="The name of the tool"),
    ]

    description: Annotated[
        str,
        Field(description="The description of the tool"),
    ]

    input_schema: Annotated[
        dict[str, Any],
        Field(description="The schema of the tool input"),
    ]

    category: Annotated[
        Literal["client-exec-tool", "client-info-tool"],
        Field(
            description="The category of the tool",
            default="unknown",
        ),
    ] = "unknown"


class Prompt(BaseModel):
    """Represents a complete prompt for an AI model interaction.

    This class encapsulates all components needed for an AI interaction, including
    the system instruction, temperature setting, and the conversation history.
    The conversation history must follow a strict user-agent interleaving pattern
    (starting with a user message, then alternating between groups of
    user and agent messages).
    """

    system_instruction: Annotated[
        str | None,
        Field(
            default=None,
            description="Initial instruction that defines the AI's behavior and context",
        ),
    ] = None

    messages: Annotated[
        list[
            Annotated[
                Union[
                    PromptUserMessage,
                    PromptAgentMessage,
                    ConversationHistorySpecialMessage,
                    DocumentsSpecialMessage,
                    MemoriesSpecialMessage,
                ],
                Field(discriminator="role"),
            ]
        ],
        Field(
            default_factory=list,
            description="Raw prompt messages, including special messages "
            "These will be converted to the proper message types "
            "when the prompt is formatted",
        ),
    ] = []

    tools: Annotated[
        list[ToolDefinition],
        Field(
            default_factory=list,
            description="Definitions of the tools provided to the model for use when generating responses",
        ),
    ] = []

    tool_choice: Annotated[
        Literal["auto", "any"] | str,
        Field(
            default="auto",
            description="The tool to use for the prompt; if not provided, "
            "the model will decide which tool to use. You may specificy 'auto', "
            "'any', or the name of a specific tool.",
        ),
    ] = "auto"

    temperature: Annotated[
        float | None,
        Field(
            default=None,
            description="Sampling temperature for the model's responses "
            "(0.0 = deterministic, 1.0 = creative); if not provided, "
            "we'll default to 0.0 (unless sampling temperature is "
            "unsupported by the provider)",
        ),
    ] = None

    seed: Annotated[
        int | None,
        Field(
            default=None,
            description="Seed used in decoding. If not set, the request uses a randomly generated seed.",
        ),
    ] = None

    max_output_tokens: Annotated[
        int | None,
        Field(
            default=None,
            description="Maximum number of tokens to consider when sampling for this prompt.",
        ),
    ] = None

    stop_sequences: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Stop sequences to use for this prompt.",
        ),
    ] = None

    top_p: Annotated[
        float | None,
        Field(
            default=None,
            description="The maximum cumulative probability of tokens to consider when sampling. Optional.",
        ),
    ] = None
