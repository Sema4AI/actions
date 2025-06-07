def test_mcp_core():
    import uvicorn

    def run_server(host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server"""
        from sema4ai.mcp_core.transport import McpTransport

        # Create the transport instance
        transport = McpTransport()
        app = transport.app

        uvicorn.run(app, host=host, port=port)

    if __name__ == "__main__":
        run_server()
