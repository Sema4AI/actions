from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

from sema4ai.mcp_core.mcp_models import InitializeResult

if TYPE_CHECKING:
    import httpx


class MCPSession:
    def __init__(self, url: str, session_id: str, client: "httpx.AsyncClient"):
        self.url = url
        self.session_id = session_id
        self.client = client


class MCPClient:
    def __init__(
        self,
        base_url: str,
        transport_url: str = "mcp",
        *,
        client_name: str = "sema4ai-mcp-client",
        client_version: str = "1.0.0",
    ):
        import itertools
        from functools import partial
        from urllib.parse import urljoin

        self.base_url = base_url
        self.url = urljoin(base_url, transport_url)
        self._next_id = partial(next, itertools.count(1))
        self.client_name = client_name
        self.client_version = client_version

    async def _initial_handshake(self, client: "httpx.AsyncClient") -> InitializeResult:
        import asyncio

        from sema4ai.mcp_core.mcp_models import (
            ClientCapabilities,
            Implementation,
            InitializedNotification,
            InitializedNotificationParams,
            InitializeRequest,
            InitializeRequestParams,
            JSONRPCResponse,
            create_mcp_model,
        )

        initialize_request_id = self._next_id()
        initialize_request = InitializeRequest(
            params=InitializeRequestParams(
                clientInfo=Implementation(
                    name=self.client_name, version=self.client_version
                ),
                capabilities=ClientCapabilities(),
                protocolVersion="2025-03-26",
            ),
            id=initialize_request_id,
        )

        url = self.url
        response = await client.post(
            url,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            json=initialize_request.to_dict(),
            timeout=None,
        )

        if response.status_code != 200:
            raise Exception(
                f"Expected a 200 response when initializing session, got {response.status_code} - {response.text}"
            )

        try:
            data = response.json()
        except Exception:
            raise Exception(f"Expected a json response, got {response.text}")

        if data["jsonrpc"] != "2.0":
            raise Exception(f"Expected a jsonrpc 2.0 response, got {data['jsonrpc']}")

        if data["id"] != initialize_request_id:
            raise Exception(
                f"Expected the resulting id to match the initialization request id ({initialize_request_id}), got {data['id']}"
            )

        if "result" not in data:
            raise Exception(f"Expected a result in the response, got {data}")

        try:
            JSONRPCResponse.from_dict(data)
        except Exception:
            raise Exception(f"Expected a JSONRPCResponse, got {data}")

        result = response_model.result
        if not isinstance(result, InitializeResult):
            raise Exception(
                f"Expected an InitializeResult, got {type(result)} - {result}"
            )

        # Ok, initialization request was successful, now, send a notification to the server
        # to let it know that we are ready to receive requests
        notification_request = InitializedNotification(
            params=InitializedNotificationParams(),
        )
        # Sending the initialization notification in a separate task is fine, we don't need to wait for it.
        asyncio.create_task(
            client.post(
                self.url,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
                json=notification_request.to_dict(),
            )
        )
        return model

    @asynccontextmanager
    async def create_session(
        self,
    ) -> AsyncIterator[MCPSession]:
        import httpx

        async with httpx.AsyncClient() as client:
            # Send initialize request
            response = await self._initial_handshake(client)

            # Get session ID from headers
            session_id = response.headers.get("Mcp-Session-Id")
            assert session_id is not None
            session = MCPSession(self.url, session_id, client)
            try:
                yield session
            finally:
                # Delete the session now DELETE on /mcp
                await client.delete(self.url, headers={"Mcp-Session-Id": session_id})
