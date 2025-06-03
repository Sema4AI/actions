from typing import Any, Literal

import pytest
from mcp import ClientSession

from sema4ai.action_server._selftest import ActionServerProcess


def run_async_in_new_thread(async_func: Any) -> Any:
    import asyncio

    from sema4ai.common.run_in_thread import run_in_thread

    def func_in_thread():
        return asyncio.run(async_func())

    fut = run_in_thread(func_in_thread)
    return fut.result()


async def check_mcp_server(
    port: int,
    connection_mode: Literal["mcp", "sse"],
    headers: dict[str, str] | None = None,
):
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.types import CallToolResult, TextContent

    client_protocol: Any
    if connection_mode == "mcp":
        client_protocol = streamablehttp_client
    else:
        assert connection_mode == "sse"
        client_protocol = sse_client

    async with client_protocol(
        f"http://localhost:{port}/{connection_mode}", headers=(headers or {})
    ) as connection_info:
        read_stream, write_stream = connection_info[:2]
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_list = await session.list_tools()
            tools = tools_list.tools
            assert len(tools) > 0
            greet_tool = next(
                tool for tool in tools if tool.name in ["greet", "greeter/greet"]
            )
            assert greet_tool is not None

            input_schema = greet_tool.inputSchema
            expected_action_server = {
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the person to greet.",
                        "title": "Name",
                    },
                    "title": {
                        "type": "string",
                        "description": "The title for the persor (Mr., Mrs., ...).",
                        "title": "Title",
                        "default": "Mr.",
                    },
                },
                "type": "object",
                "required": ["name"],
            }

            expected_mcp = {
                "properties": {
                    "name": {"title": "Name", "type": "string"},
                    "title": {"default": "Mr.", "title": "title", "type": "string"},
                },
                "required": ["name"],
                "title": "greetArguments",
                "type": "object",
            }

            assert input_schema in (expected_action_server, expected_mcp), (
                "Found: %s\nExpected: %s or %s",
                input_schema,
                expected_action_server,
                expected_mcp,
            )

            tool_result = await session.call_tool(
                greet_tool.name, {"name": "John", "title": "Mr."}
            )

            assert isinstance(tool_result, CallToolResult)
            content = tool_result.content[0]
            assert isinstance(content, TextContent)
            assert (
                content.text == "Hello Mr. John."
            ), f"Expected: Hello Mr. John., got: {content.text}"
            return "ok"


@pytest.fixture()
def mcp_server_port():
    import os
    import re
    import sys

    from action_server_tests.fixtures import get_in_resources
    from sema4ai.common.process import Process
    from sema4ai.common.wait_for import wait_for_condition

    cp = os.environ.copy()
    cp["PYTHONPATH"] = os.pathsep.join([x for x in sys.path if x])
    cp["PYTHONIOENCODING"] = "utf-8"
    process = Process(
        [sys.executable, "simple_mcp_server.py", "0"],
        cwd=get_in_resources("mcp_server"),
        env=cp,
    )

    port = None
    lines = []

    def on_output(line):
        nonlocal port
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

    yield port
    process.stop()


def test_mcp_integration(mcp_server_port: int) -> None:
    from functools import partial

    assert (
        run_async_in_new_thread(partial(check_mcp_server, mcp_server_port, "mcp"))
        == "ok"
    )


@pytest.mark.parametrize("connection_mode", ["mcp", "sse"])
@pytest.mark.integration_test
def test_mcp_integration_with_actions(
    action_server_process: ActionServerProcess,
    connection_mode: Literal["mcp", "sse"],
) -> None:
    from functools import partial

    from action_server_tests.fixtures import get_in_resources

    root_dir = get_in_resources("no_conda", "greeter")

    action_server_process.start(
        db_file="server.db",
        cwd=str(root_dir),
        actions_sync=True,
        timeout=60 * 10,
    )
    assert (
        run_async_in_new_thread(
            partial(
                check_mcp_server,
                action_server_process.port,
                connection_mode=connection_mode,
            )
        )
        == "ok"
    )


@pytest.mark.parametrize("connection_mode", ["mcp", "sse"])
@pytest.mark.integration_test
def test_mcp_integration_with_actions_and_api_key(
    action_server_process: ActionServerProcess,
    connection_mode: Literal["mcp", "sse"],
) -> None:
    from functools import partial

    from action_server_tests.fixtures import get_in_resources

    root_dir = get_in_resources("no_conda", "greeter")

    action_server_process.start(
        db_file="server.db",
        cwd=str(root_dir),
        actions_sync=True,
        timeout=60 * 10,
        additional_args=["--api-key=Foo"],
    )
    assert (
        run_async_in_new_thread(
            partial(
                check_mcp_server,
                action_server_process.port,
                connection_mode=connection_mode,
                headers={"Authorization": "Bearer Foo"},
            )
        )
        == "ok"
    )

    with pytest.raises(
        Exception
    ):  # If we don't pass the headers we should get an exception
        run_async_in_new_thread(
            partial(
                check_mcp_server,
                action_server_process.port,
                connection_mode=connection_mode,
            )
        )

    with pytest.raises(
        Exception
    ):  # If we pass the wrong headers we should get an exception
        run_async_in_new_thread(
            partial(
                check_mcp_server,
                action_server_process.port,
                connection_mode=connection_mode,
                headers={"Authorization": "Bearer Bar"},
            )
        )
