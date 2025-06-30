from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable

from sema4ai.mcp_core.mcp_models import InitializeResult
from sema4ai.mcp_core.mcp_models._generated_mcp_models import CallToolResult, Tool

if TYPE_CHECKING:
    import httpx

DEFAULT_TIMEOUT: float | None = 10.0


def is_debugger_active() -> bool:
    import sys

    if "pydevd" not in sys.modules:
        return False

    try:
        import pydevd  # type:ignore
    except ImportError:
        return False

    return bool(pydevd.get_global_debugger())


if is_debugger_active():
    DEFAULT_TIMEOUT = None


class MCPSession:
    timeout: float | None = DEFAULT_TIMEOUT

    def __init__(
        self,
        url: str,
        session_id: str,
        client: "httpx.AsyncClient",
        initialize_result: InitializeResult,
        next_id: Callable[[], int | str],
    ):
        self.url = url
        self.session_id = session_id
        self.client = client
        self.initialize_result = initialize_result
        self._next_id = next_id

    def next_id(self) -> int | str:
        return self._next_id()

    async def list_tools(self) -> list[Tool]:
        from sema4ai.mcp_core.mcp_models import build_result_model
        from sema4ai.mcp_core.mcp_models._generated_mcp_models import (
            ListToolsRequest,
            ListToolsResult,
        )

        if self.initialize_result.capabilities.tools is None:
            return []  # Tools aren't supported by this server

        request = ListToolsRequest(
            id=self.next_id(),
        )
        response = await self.client.post(
            self.url,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.session_id,
            },
            json=request.to_dict(),
            timeout=self.timeout,
        )
        assert response.status_code == 200
        try:
            data = response.json()
        except Exception:
            raise Exception(f"Expected a json response, got {response.text}")

        if data["jsonrpc"] != "2.0":
            raise Exception(f"Expected a jsonrpc 2.0 response, got {data['jsonrpc']}")

        if "result" not in data:
            raise Exception(f"Expected a result in the response, got {data}")

        result = build_result_model(request, data["result"])
        if not isinstance(result, ListToolsResult):
            raise Exception(f"Expected a ListToolsResult, got {type(result)} - {result}")
        return result.tools

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult:
        from sema4ai.mcp_core.mcp_models import build_result_model
        from sema4ai.mcp_core.mcp_models._generated_mcp_models import (
            CallToolRequest,
            CallToolRequestParams,
        )

        request = CallToolRequest(
            params=CallToolRequestParams(name=tool_name, arguments=arguments),
            id=self.next_id(),
        )

        response = await self.client.post(
            self.url,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.session_id,
            },
            json=request.to_dict(),
            timeout=self.timeout,
        )
        assert response.status_code == 200
        try:
            data = response.json()
        except Exception:
            raise Exception(f"Expected a json response, got {response.text}")

        if data["jsonrpc"] != "2.0":
            raise Exception(f"Expected a jsonrpc 2.0 response, got {data['jsonrpc']}")

        if "result" not in data:
            raise Exception(f"Expected a result in the response, got {data}")

        result = build_result_model(request, data["result"])
        if not isinstance(result, CallToolResult):
            raise Exception(f"Expected a CallToolResult, got {type(result)} - {result}")
        return result


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

    async def _initial_handshake(
        self, client: "httpx.AsyncClient"
    ) -> tuple[InitializeResult, "httpx.Response"]:
        import asyncio

        from sema4ai.mcp_core.mcp_models import (
            ClientCapabilities,
            Implementation,
            InitializedNotification,
            InitializedNotificationParams,
            InitializeRequest,
            InitializeRequestParams,
            build_result_model,
        )

        initialize_request_id = self._next_id()
        initialize_request = InitializeRequest(
            params=InitializeRequestParams(
                clientInfo=Implementation(name=self.client_name, version=self.client_version),
                capabilities=ClientCapabilities(),
                protocolVersion="2025-06-18",
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

        error = data.get("error")
        if error is not None:
            raise Exception(f"Expected no error in the response, got {error}")

        if data["id"] != initialize_request_id:
            raise Exception(
                f"Expected the resulting id to match the initialization request id ({initialize_request_id}), got {data['id']}"
            )

        if "result" not in data:
            raise Exception(f"Expected a result in the response, got {data}")

        result = build_result_model(initialize_request, data["result"])
        if not isinstance(result, InitializeResult):
            raise Exception(f"Expected an InitializeResult, got {type(result)} - {result}")

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
        return result, response

    @asynccontextmanager
    async def create_session(
        self,
    ) -> AsyncIterator[MCPSession]:
        import httpx

        async with httpx.AsyncClient() as client:
            # Send initialize request
            result, response = await self._initial_handshake(client)

            # Get session ID from headers
            session_id = response.headers.get("Mcp-Session-Id")  # type: ignore
            assert session_id is not None
            session = MCPSession(self.url, session_id, client, result, self._next_id)
            try:
                yield session
            finally:
                # Delete the session now DELETE on /mcp
                await client.delete(self.url, headers={"Mcp-Session-Id": session_id})
