from typing import Any, Union

import uvicorn
from fastapi.applications import FastAPI
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware

from sema4ai.mcp_core.mcp_models import (
    Implementation,
    InitializeRequest,
    InitializeResult,
    MCPBaseModel,
    ServerCapabilities,
)
from sema4ai.mcp_core.transport import IMCPImplementation, McpTransport


class SampleMCPImplementation(IMCPImplementation):
    """Sample implementation that handles initialization."""

    async def handle_message(
        self, mcp_models: list[MCPBaseModel]
    ) -> list[MCPBaseModel] | MCPBaseModel | EventSourceResponse:
        """Handle an MCP request.

        Args:
            mcp_models: The MCP models to handle (one or more).

        Returns:
            A list of MCP models or an EventSourceResponse
        """

        single_model = len(mcp_models) == 1

        for model in mcp_models:
            if isinstance(model, InitializeRequest):
                assert (
                    single_model
                ), f"Error: InitializeRequest cannot be batched, received: {mcp_models}"

                return InitializeResult(
                    capabilities=ServerCapabilities(),
                    protocolVersion="1.0",
                    serverInfo=Implementation(name="test-server", version="1.0.0"),
                )

        raise NotImplementedError(f"TODO: Implement support to handle: {mcp_models}")


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

    # Create the transport instance with sample implementation
    transport = McpTransport(app, SampleMCPImplementation())

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
