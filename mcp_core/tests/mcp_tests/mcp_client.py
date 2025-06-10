from contextlib import asynccontextmanager
from typing import AsyncIterator


class MCPSession:
    def __init__(self, url: str, session_id: str):
        self.url = url
        self.session_id = session_id


class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    @asynccontextmanager
    async def create_session(self) -> AsyncIterator[MCPSession]:
        from urllib.parse import urljoin

        import httpx

        from sema4ai.mcp_core.mcp_models import (
            ClientCapabilities,
            Implementation,
            InitializeRequest,
            InitializeRequestParamsParams,
        )

        async with httpx.AsyncClient() as client:
            # Send initialize request
            initialize_request = InitializeRequest(
                params=InitializeRequestParamsParams(
                    clientInfo=Implementation(name="test-client", version="1.0.0"),
                    capabilities=ClientCapabilities(),
                    protocolVersion="1.0",
                ),
                id=1,
            )

            url = urljoin(self.base_url, "mcp")
            response = await client.post(
                url,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
                json=initialize_request.to_dict(),
                timeout=None,
            )

            assert response.status_code == 200
            try:
                data = response.json()
            except Exception:
                raise Exception(f"Expected a json response, got {response.text}")
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data

            # Get session ID from headers
            session_id = response.headers.get("Mcp-Session-Id")
            assert session_id is not None
            session = MCPSession(url, session_id)
            try:
                yield session
            finally:
                # Cleanup if needed
                pass
