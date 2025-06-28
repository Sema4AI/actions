import uvicorn
from fastapi.applications import FastAPI
from starlette.middleware.cors import CORSMiddleware

from sema4ai.mcp_core.transport import create_streamable_http_router


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

    router = create_streamable_http_router(StreamableHttpMCPSessionHandler())
    app.include_router(router)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
