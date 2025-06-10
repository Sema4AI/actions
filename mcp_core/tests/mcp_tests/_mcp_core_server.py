import uvicorn
from fastapi.applications import FastAPI
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from sema4ai.mcp_core.mcp_models import (
    Implementation,
    InitializeRequest,
    InitializeResult,
    MCPBaseModel,
    ServerCapabilities,
)
from sema4ai.mcp_core.protocols import IMCPHandler, IMCPSessionHandler
from sema4ai.mcp_core.transport import create_streamable_http_router


class SampleMCPImplementation(IMCPHandler):
    """Sample implementation that handles initialization."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    async def handle_message(
        self, mcp_models: list[MCPBaseModel]
    ) -> MCPBaseModel | EventSourceResponse:
        """Handle an MCP request.

        Args:
            mcp_models: The MCP models to handle (one or more).

        Returns:
            A list of MCP models or an EventSourceResponse
        """
        from sema4ai.mcp_core.mcp_models import JSONRPCResponse

        single_model = len(mcp_models) == 1

        for model in mcp_models:
            if isinstance(model, InitializeRequest):
                assert (
                    single_model
                ), f"Error: InitializeRequest cannot be batched, received: {mcp_models}"

                response = JSONRPCResponse(
                    id=model.id,
                    result=InitializeResult(
                        capabilities=ServerCapabilities(),
                        protocolVersion="1.0",
                        serverInfo=Implementation(name="test-server", version="1.0.0"),
                    ),
                )
                return response

        raise NotImplementedError(f"TODO: Implement support to handle: {mcp_models}")

    async def handle_notifications(self, mcp_models: list[MCPBaseModel]) -> None:
        """Handle MCP notifications."""
        # Sample implementation just ignores notifications
        pass

    async def handle_responses(self, mcp_models: list[MCPBaseModel]) -> None:
        """Handle MCP responses."""
        # Sample implementation just ignores responses
        pass

    async def handle_sse_stream(self, last_event_id: str | None) -> EventSourceResponse:
        """Handle SSE stream requests."""

        # Sample implementation returns an empty stream
        async def event_generator():
            if False:
                yield {"data": "test"}

        return EventSourceResponse(event_generator())


class SampleMCPSessionHandler(IMCPSessionHandler):
    """Sample session handler that handles sessions."""

    def __init__(self) -> None:
        self._handlers: dict[str, IMCPHandler] = {}

    async def obtain_session_handler(
        self, request: Request, session_id: str | None
    ) -> IMCPHandler:
        """Obtain an MCP session handler."""
        import uuid

        if session_id is None:
            session_id = str(uuid.uuid4())
        self._handlers[session_id] = SampleMCPImplementation(session_id)
        return self._handlers[session_id]

    async def get_session_handler(
        self, request: Request, session_id: str
    ) -> IMCPHandler:
        """Get an MCP session handler."""
        return self._handlers[session_id]

    async def end_session(self, request: Request, session_id: str) -> None:
        """End an MCP session."""
        self._handlers.pop(session_id, None)


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the MCP server"""
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    router = create_streamable_http_router(SampleMCPSessionHandler())
    app.include_router(router)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
