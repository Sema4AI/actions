from functools import cache
from typing import Any, Callable, Coroutine

from sema4ai.mcp_core.mcp_models._generated_mcp_models import (
    CallToolRequest,
    CallToolResult,
    InitializeRequest,
    InitializeResult,
    ListToolsRequest,
    ListToolsResult,
    Result,
    ServerCapabilities,
    Tool,
)
from sema4ai.mcp_core.protocols import IMCPRequestModel, IMessageHandler


@cache
def convert_from_camel_to_underscores(text: str) -> str:
    """Convert a camel case string to a snake case string."""

    return "".join(["_" + i.lower() if i.isupper() else i for i in text]).lstrip("_")


class DefaultMcpMessageHandler(IMessageHandler):
    """Default implementation of the IMessageHandler protocol."""

    def __init__(
        self,
        server_name: str = "sema4ai-mcp-core",
        server_version: str = "1.0.0",
        server_capabilities: ServerCapabilities | None = None,
    ) -> None:
        self._tools: list[Tool] = []
        self._tool_handlers: dict[
            str, Callable[[CallToolRequest], Coroutine[Any, Any, Result]]
        ] = {}
        self.server_name = server_name
        self.server_version = server_version
        self.server_capabilities = server_capabilities or ServerCapabilities()

    @property
    def protocol_version(self) -> str:
        """Get the protocol version that this server implements."""
        return "2025-06-18"

    def register_tool(
        self,
        tool: Tool,
        handler: Callable[[CallToolRequest], Coroutine[Any, Any, Result]],
    ) -> None:
        """Register a tool and its handler."""
        from sema4ai.mcp_core.mcp_models._generated_mcp_models import (
            ServerCapabilitiesToolsParams,
        )

        if tool.name in self._tool_handlers:
            raise ValueError(f"Tool {tool.name} is already registered")

        self._tools.append(tool)
        self._tool_handlers[tool.name] = handler
        if self.server_capabilities.tools is None:
            self.server_capabilities.tools = ServerCapabilitiesToolsParams(
                listChanged=True,
            )

    async def handle_request(self, request: IMCPRequestModel) -> Result:
        """Handle an MCP message."""
        import inspect

        name = f"on_{convert_from_camel_to_underscores(request.__class__.__name__)}"

        if not hasattr(self, name):
            raise ValueError(
                f"No handler found for request: {request.__class__.__name__} (expected: {name} in {self.__class__.__name__})"
            )

        result = getattr(self, name)(request)
        if inspect.isawaitable(result):
            result = await result

        if not isinstance(result, Result):
            raise ValueError(f"Expected Result, got {type(result)}")

        return result

    async def on_initialize_request(self, request: InitializeRequest) -> InitializeResult:
        """Handle an initialize request (MCP message handling)."""
        from sema4ai.mcp_core.mcp_models._generated_mcp_models import Implementation

        if not isinstance(request, InitializeRequest):
            raise ValueError(f"Expected InitializeRequest, got {type(request)}")

        return InitializeResult(
            capabilities=self.server_capabilities,
            protocolVersion=self.protocol_version,
            serverInfo=Implementation(name=self.server_name, version=self.server_version),
        )

    async def on_list_tools_request(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle a list tools request (MCP message handling)."""
        if not isinstance(request, ListToolsRequest):
            raise ValueError(f"Expected ListToolsRequest, got {type(request)}")

        return ListToolsResult(
            tools=self._tools,
        )

    async def on_call_tool_request(self, request: CallToolRequest) -> CallToolResult:
        """Handle a call tool request (MCP message handling)."""
        if not isinstance(request, CallToolRequest):
            raise ValueError(f"Expected CallToolRequest, got {type(request)}")

        if request.params.name not in self._tool_handlers:
            raise ValueError(f"Unknown tool: {request.params.name}")

        handler = self._tool_handlers[request.params.name]
        result = await handler(request)

        if not isinstance(result, CallToolResult):
            raise ValueError(f"Expected CallToolResult, got {type(result)}")

        return result
