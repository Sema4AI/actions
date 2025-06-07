import uvicorn


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the MCP server"""
    from fastapi.applications import FastAPI
    from starlette.middleware.cors import CORSMiddleware

    from sema4ai.mcp_core.transport import McpTransport

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    # Create the transport instance
    transport = McpTransport()
    app = transport.app

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
