from functools import cache
from typing import Any, Callable, Coroutine

from sema4ai.mcp_core.mcp_models._generated_mcp_models import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Result,
    Tool,
)
from sema4ai.mcp_core.protocols import IMCPRequestModel, IMessageHandler


@cache
def convert_from_camel_to_underscores(text: str) -> str:
    """Convert a camel case string to a snake case string."""

    return "".join(["_" + i.lower() if i.isupper() else i for i in text]).lstrip("_")


class DefaultMcpMessageHandler(IMessageHandler):
    """Default implementation of the IMessageHandler protocol."""

    def __init__(self) -> None:
        self._tools: list[Tool] = []
        self._tool_handlers: dict[
            str, Callable[[CallToolRequest], Coroutine[Any, Any, Result]]
        ] = {}

    def register_tool(
        self,
        tool: Tool,
        handler: Callable[[CallToolRequest], Coroutine[Any, Any, Result]],
    ) -> None:
        """Register a tool and its handler."""
        if tool.name in self._tool_handlers:
            raise ValueError(f"Tool {tool.name} is already registered")

        self._tools.append(tool)
        self._tool_handlers[tool.name] = handler

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
            raise ValueError(f"Tool {request.params.name} not registered")

        handler = self._tool_handlers[request.params.name]
        result = await handler(request)

        if not isinstance(result, CallToolResult):
            raise ValueError(f"Expected CallToolResult, got {type(result)}")

        return result
