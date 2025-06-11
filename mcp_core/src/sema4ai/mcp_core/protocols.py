from enum import Enum
from typing import TYPE_CHECKING, Any, Iterator, Protocol, Type, TypeVar

from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

if TYPE_CHECKING:
    from sema4ai.mcp_core.mcp_base_model import MCPBaseModel

T = TypeVar("T")


class MessageType(Enum):
    REQUEST = "request"
    NOTIFICATION = "notification"
    RESPONSE = "response"
    RESULT = "result"
    OTHER = "other"


class IMCPRequestModel(Protocol):
    """Protocol defining the interface for an MCP request model."""

    id: str

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""

    @classmethod
    def get_message_type(cls) -> MessageType:
        """Get the type of message this class represents."""


class IMessageHandler(Protocol):
    """Protocol defining the interface for handling MCP messages."""

    async def handle_request(self, request: IMCPRequestModel) -> "MCPBaseModel":
        """Handle an MCP request."""


class IMessagesGenerator(Protocol):
    """Protocol defining the interface for generating MCP messages from the server
    that are not related to a specific request."""

    async def generate_messages(self) -> Iterator["MCPBaseModel"]:
        """Generate MCP messages from the server that are not related to a specific request."""


class IStreamableHttpMCPSessionHandler(Protocol):
    """Protocol defining the interface for managing a session.

    Implementors can decide to use a database or a simple in-memory store to store the session handlers,
    how to handle session expiration, or even always return the same handler if there should be only one session.
    """

    async def obtain_session_handler(
        self, request: Request, session_id: str | None
    ) -> "IStreamableHttpMCPHandler":
        """Obtain an MCP session (i.e.: creates a new session if session_id is None
        or returns the existing session handler if session_id is provided).

        Args:
            session_id: The ID of the session or none if not specified.

        Raises:
            KeyError: If the session handler is not found given the request and session_id.
        """

    async def get_session_handler(
        self, request: Request, session_id: str
    ) -> "IStreamableHttpMCPHandler":
        """Get the session handler given a request and a session ID.

        Args:
            request: The request object
            session_id: The ID of the session

        Raises:
            KeyError: If the session handler is not found given the request and session_id.
        """

    async def end_session(self, request: Request, session_id: str) -> None:
        """End an MCP session.

        Args:
            session_id: The ID of the session
        """


class IStreamableHttpMCPHandler(Protocol):
    """Low-level protocol defining the interface for handling MCP messages."""

    session_id: str

    async def handle_sse_stream(self, last_event_id: str | None) -> EventSourceResponse:
        """Handle an SSE stream.

        Args:
            last_event_id: The last event ID

        Returns:
            An EventSourceResponse for streaming responses
        """

    async def handle_requests(
        self, request: list[IMCPRequestModel]
    ) -> "MCPBaseModel | EventSourceResponse":
        """Handle an MCP request.

        Args:
            request: The MCP request to handle

        Returns:
            Either a response model or an EventSourceResponse for streaming responses
        """

    async def handle_notifications(self, notifications: list["MCPBaseModel"]) -> None:
        """Handle an MCP notification.

        Args:
            notifications: The MCP notifications to handle
        """

    async def handle_responses(self, responses: list["MCPBaseModel"]) -> None:
        """Handle an MCP response.

        Args:
            responses: The MCP responses to handle (from a request the server sent to the client)
        """
