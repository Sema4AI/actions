import json
from typing import Iterator

import httpx
import pytest


@pytest.fixture()
def mcp_server() -> Iterator[str]:
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


@pytest.mark.asyncio
async def test_mcp_initialize(mcp_server: str):
    """Test the MCP initialization request."""
    from sema4ai.mcp_core.mcp_models import (
        ClientCapabilities,
        Implementation,
        InitializeRequest,
        InitializeRequestParamsParams,
    )

    async with httpx.AsyncClient() as client:
        # Send initialize request
        initialize_request = InitializeRequest(
            method="initialize",
            params=InitializeRequestParamsParams(
                clientInfo=Implementation(name="test-client", version="1.0.0"),
                capabilities=ClientCapabilities(),
                protocolVersion="1.0",
            ),
        )

        response = await client.post(
            f"{mcp_server}/mcp",
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            json=initialize_request.to_dict(),
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

        return session_id


@pytest.mark.asyncio
async def test_mcp_notification(mcp_server: str):
    """Test sending a notification to the MCP server."""
    session_id = await test_mcp_initialize(mcp_server)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{mcp_server}/mcp",
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Mcp-Session-Id": session_id,
            },
            json={
                "jsonrpc": "2.0",
                "method": "test_notification",
                "params": {"message": "test"},
            },
        )

        assert response.status_code == 202


@pytest.mark.asyncio
async def test_mcp_request_stream(mcp_server: str):
    """Test sending a request and receiving a stream response."""
    session_id = await test_mcp_initialize(mcp_server)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{mcp_server}/mcp",
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "Mcp-Session-Id": session_id,
            },
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "test_request",
                "params": {"message": "test"},
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # Read the SSE stream
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                assert data["jsonrpc"] == "2.0"
                assert data["method"] == "test"
                break
