import uvicorn
from fastapi.applications import FastAPI
from starlette.middleware.cors import CORSMiddleware

from sema4ai.mcp_core.mcp_handler import DefaultMcpMessageHandler
from sema4ai.mcp_core.mcp_models._generated_mcp_models import (
    CallToolRequest,
    CallToolResult,
)
from sema4ai.mcp_core.transport import create_streamable_http_router


class TestsMessagesHandler(DefaultMcpMessageHandler):
    def __init__(self) -> None:
        from sema4ai.mcp_core.mcp_models._generated_mcp_models import (
            Tool,
            ToolInputschemaParams,
        )

        super().__init__()
        self.register_tool(
            Tool(
                name="test",
                description="Test tool",
                inputSchema=ToolInputschemaParams(type="object", properties={}),
            ),
            self._handle_test_tool_request,
        )

    async def _handle_test_tool_request(self, request: CallToolRequest) -> CallToolResult:
        from sema4ai.mcp_core.mcp_models._generated_mcp_models import TextContent

        return CallToolResult(
            content=[TextContent(text="Test tool response")],
        )


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the MCP server"""
    from sema4ai.mcp_core.transport import StreamableHttpMCPSessionHandler

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    router = create_streamable_http_router(StreamableHttpMCPSessionHandler(TestsMessagesHandler))
    app.include_router(router)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
