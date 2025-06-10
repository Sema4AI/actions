import asyncio
import logging
from typing import Literal

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

log = logging.getLogger(__name__)


_DONE: Literal["DONE"] = "DONE"


class StreamableHttpMCPHandler(IMCPHandler):
    """Base MCP low-level implementation (base framework to handle MCP requests using streamable HTTP)."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._initialized = False

    async def handle_requests(
        self, mcp_models: list[MCPBaseModel]
    ) -> MCPBaseModel | EventSourceResponse:
        """Handle an MCP request.

        Args:
            mcp_models: The MCP models to handle (one or more).

        Returns:
            One MCP model or an EventSourceResponse
        """
        from sema4ai.mcp_core.mcp_models import JSONRPCResponse

        single_model = len(mcp_models) == 1

        if not self._initialized:
            for model in mcp_models:
                if isinstance(model, InitializeRequest):
                    if self._initialized:
                        raise ValueError(
                            f"Error: InitializeRequest cannot be sent more than once, received: {mcp_models}"
                        )
                    if not single_model:
                        raise ValueError(
                            f"Error: InitializeRequest cannot be batched, received: {mcp_models}"
                        )
                    self._initialized = True

                    response = JSONRPCResponse(
                        id=model.id,
                        result=InitializeResult(
                            capabilities=ServerCapabilities(),
                            protocolVersion="2025-03-26",
                            serverInfo=Implementation(name="test-server", version="1.0.0"),
                        ),
                    )
                    return response

        return await self._handle_requests(mcp_models)

    async def _process_mcp_requests(
        self,
        queue: asyncio.Queue[dict[str, str] | Literal["DONE"]],
        mcp_models: list[MCPBaseModel],
    ) -> None:
        """Process MCP requests and put results in the queue."""
        from sema4ai.mcp_core.mcp_models import create_json_rpc_error

        try:
            for model in mcp_models:
                # Process each model and put results in queue
                # For now, just echo the model as JSON
                pass

            # Signal completion
            await queue.put(_DONE)
        except Exception as e:
            # Handle errors by sending them to the queue
            await queue.put(create_json_rpc_error(str(e)))
            await queue.put(_DONE)

    async def event_generator(self, queue: asyncio.Queue[dict[str, str] | Literal["DONE"]]):
        """Generate SSE events from the queue."""
        from sema4ai.mcp_core.mcp_models import create_json_rpc_error

        while True:
            try:
                # Get next item from queue
                item = await queue.get()

                # Check if we're done
                if item == _DONE:
                    break

                yield item

            except Exception as e:
                log.exception(e)
                yield create_json_rpc_error(str(e))
                break
            finally:
                queue.task_done()

    async def _handle_requests(
        self, mcp_models: list[MCPBaseModel]
    ) -> MCPBaseModel | EventSourceResponse:
        """Handle MCP requests using an async queue and EventSourceResponse."""

        # A queue to store the results of the requests (or other messages to be sent to the client)
        # until a "DONE" message is put in the queue.
        queue: asyncio.Queue[dict[str, str] | Literal["DONE"]] = asyncio.Queue()

        _task = asyncio.create_task(self._process_mcp_requests(queue, mcp_models))

        return EventSourceResponse(self.event_generator(queue))

    async def handle_notifications(self, mcp_models: list[MCPBaseModel]) -> None:
        """Handle MCP notifications (sent from the client to the server)."""

    async def handle_responses(self, mcp_models: list[MCPBaseModel]) -> None:
        """Handle MCP responses (something requested by the server and answered by the client)."""

    async def handle_sse_stream(self, last_event_id: str | None) -> EventSourceResponse:
        """Handle SSE stream requests (sent from the server to the client)."""

        async def event_generator():
            if False:
                yield {"data": "test"}

        return EventSourceResponse(event_generator())


class StreamableHttpMCPSessionHandler(IMCPSessionHandler):
    """Base MCP session handler that handles sessions."""

    def __init__(self) -> None:
        self._handlers: dict[str, IMCPHandler] = {}

    async def obtain_session_handler(self, request: Request, session_id: str | None) -> IMCPHandler:
        """Obtain an MCP session handler."""
        import uuid

        if session_id is None:
            session_id = str(uuid.uuid4())
        self._handlers[session_id] = StreamableHttpMCPHandler(session_id)
        return self._handlers[session_id]

    async def get_session_handler(self, request: Request, session_id: str) -> IMCPHandler:
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

    router = create_streamable_http_router(StreamableHttpMCPSessionHandler())
    app.include_router(router)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
