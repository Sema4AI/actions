import json
from typing import AsyncIterator, Iterator

import httpx
import pytest
import pytest_asyncio
from mcp_tests.mcp_client import MCPClient, MCPSession


@pytest.fixture()
def mcp_server_base_url() -> Iterator[str]:
    import os
    import re
    import sys

    from sema4ai.common.process import Process
    from sema4ai.common.wait_for import wait_for_condition

    cp = os.environ.copy()
    cp["PYTHONPATH"] = os.pathsep.join([x for x in sys.path if x])
    cp["PYTHONIOENCODING"] = "utf-8"

    curdir = os.path.dirname(os.path.abspath(__file__))
    mcp_core_server_file = os.path.join(curdir, "_mcp_core_server.py")
    assert os.path.exists(
        mcp_core_server_file
    ), f"MCP server file not found: {mcp_core_server_file}"

    process = Process(
        [sys.executable, mcp_core_server_file, "0"],
        cwd=os.path.abspath("."),
        env=cp,
    )

    port = None
    lines = []

    def on_output(line):
        nonlocal port
        print(f"on_output: {line}")
        lines.append(line)
        if port is None:
            match = re.search(r"running on http://[^:]+:(\d+)", line)
            if match:
                port = int(match.group(1))

    process.on_stdout.register(on_output)
    process.on_stderr.register(on_output)
    process.start()

    wait_for_condition(lambda: port is not None)

    if port is None:
        process.stop()
        raise RuntimeError(
            "Could not determine MCP server port after 10 seconds. output: "
            + "\n".join(lines)
        )

    yield f"http://127.0.0.1:{port}"
    process.stop()


@pytest_asyncio.fixture
async def mcp_session(mcp_server_base_url: str) -> AsyncIterator[MCPSession]:
    client = MCPClient(mcp_server_base_url)
    async with client.create_session() as session:
        assert session.session_id is not None
        yield session


@pytest.mark.asyncio
async def test_mcp_session_initialization(mcp_server_base_url: str):
    """Test the MCP initialization request."""

    mcp_client = MCPClient(mcp_server_base_url)
    async with mcp_client.create_session() as session:
        assert session.session_id is not None

    # Test that the session is deleted after the context manager is exited
    async with httpx.AsyncClient() as client:
        response = await client.get(
            mcp_client.url,
            headers={
                "Accept": "text/event-stream",
                "Mcp-Session-Id": session.session_id,
            },
        )
        assert response.status_code == 404
        assert json.loads(response.text) == {"detail": "Session not found"}


@pytest.mark.asyncio
async def test_mcp_session_bad_requests(mcp_server_base_url: str):
    mcp_client = MCPClient(mcp_server_base_url)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            mcp_client.url,
            headers={},
        )
        assert response.status_code == 405
        assert json.loads(response.text) == {
            "detail": "text/event-stream not included in Accept header"
        }

        response = await client.get(
            mcp_client.url,
            headers={"Accept": "text/event-stream"},
        )
        assert response.status_code == 400
        assert json.loads(response.text) == {"detail": "Mcp-Session-Id is required"}


@pytest.mark.asyncio
async def test_mcp_notification(mcp_session: MCPSession):
    """Test sending a notification to the MCP server."""
    from sema4ai.mcp_core.mcp_models import (
        CancelledNotification,
        CancelledNotificationParams,
    )

    session_id = mcp_session.session_id

    async with httpx.AsyncClient() as client:
        response = await client.post(
            mcp_session.url,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Mcp-Session-Id": session_id,
            },
            json=CancelledNotification(
                params=CancelledNotificationParams(requestId=1),
            ).to_dict(),
        )

        assert response.status_code == 202


@pytest.mark.asyncio
async def test_mcp_tool_call(mcp_session: MCPSession):
    pass


# @pytest.mark.asyncio
# async def test_mcp_tool_call(mcp_session: MCPSession):
#     """Test sending a request and receiving a stream response."""

#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             f"{mcp_server_base_url}/mcp",
#             headers={
#                 "Accept": "application/json, text/event-stream",
#                 "Content-Type": "application/json",
#                 "Mcp-Session-Id": session_id,
#             },
#             json={
#                 "jsonrpc": "2.0",
#                 "id": 2,
#                 "method": "test_request",
#                 "params": {"message": "test"},
#             },
#             timeout=5.0,
#         )

#         assert response.status_code == 200
#         assert response.headers["content-type"] == "text/event-stream"

#         # Read the SSE stream
#         async for line in response.aiter_lines():
#             if line.startswith("data: "):
#                 data = json.loads(line[6:])
#                 assert data["jsonrpc"] == "2.0"
#                 assert data["method"] == "test"
#                 break
