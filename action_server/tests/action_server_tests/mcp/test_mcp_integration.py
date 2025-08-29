from typing import Any, Literal

import pytest
from action_server_tests.fixtures import run_async_in_new_thread
from sema4ai.action_server._selftest import ActionServerProcess

from mcp import ClientSession


async def check_mcp_server(
    port: int,
    connection_mode: Literal["mcp", "sse"],
    headers: dict[str, str] | None = None,
    use_sema4ai_mcp: bool = True,
):
    """
    This method is meant to check that the `resources/no_conda/mcp` implementation
    is working.
    """
    from pydantic.networks import AnyUrl

    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.types import (
        CallToolResult,
        GetPromptResult,
        Prompt,
        ReadResourceResult,
        TextContent,
        TextResourceContents,
    )

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

            tool_names = [tool.name for tool in tools]
            assert "greet_mcp" in tool_names, (
                f"greet_mcp tool not found. Available tools: {tool_names}"
            )

            greet_tool = next(tool for tool in tools if tool.name == "greet_mcp")
            assert greet_tool is not None, (
                f"'greet_mcp' tool not found. Available tools: {tool_names}"
            )

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
                "title": "greet_mcpArguments",
                "type": "object",
            }

            assert input_schema in (expected_action_server, expected_mcp), (
                "Found: %s\nExpected: %s or %s",
                input_schema,
                expected_action_server,
                expected_mcp,
            )

            # -- Test tool call.

            tool_result = await session.call_tool(
                greet_tool.name, {"name": "John", "title": "Mr."}
            )

            assert isinstance(tool_result, CallToolResult)
            tool_content = tool_result.content[0]
            assert isinstance(tool_content, TextContent)
            assert tool_content.text == "Hello Mr. John.", (
                f"Expected: Hello Mr. John., got: {tool_content.text}"
            )

            # -- Test prompts.

            prompts_list = await session.list_prompts()
            prompts = prompts_list.prompts
            found = {prompt.name for prompt in prompts}
            assert found == {
                "my_prompt",
                "my_prompt_with_optional_arg",
            }, f"Found: {found}. Expected: {'my_prompt', 'my_prompt_with_optional_arg'}"

            # Check the schema of the prompt with optional argument.
            prompt_with_optional_arg: Prompt = next(
                prompt
                for prompt in prompts
                if prompt.name == "my_prompt_with_optional_arg"
            )
            as_dict = prompt_with_optional_arg.model_dump()
            assert as_dict["name"] == "my_prompt_with_optional_arg"
            expected_arguments = [
                {
                    "name": "name",
                    "description": (
                        "The name of the person to greet." if use_sema4ai_mcp else None
                    ),
                    "required": False,
                }
            ]
            assert as_dict["arguments"] == expected_arguments, (
                f"Found: {as_dict['arguments']}. Expected: {expected_arguments}"
            )

            # Check the schema of the prompt without optional argument.
            prompt_without_optional_arg: Prompt = next(
                prompt for prompt in prompts if prompt.name == "my_prompt"
            )
            as_dict = prompt_without_optional_arg.model_dump()
            assert as_dict["name"] == "my_prompt"
            expected_arguments = [
                {
                    "name": "name",
                    "description": (
                        "The name of the person to greet." if use_sema4ai_mcp else None
                    ),
                    "required": True,
                }
            ]
            assert as_dict["arguments"] == expected_arguments, (
                f"Found: {as_dict['arguments']}. Expected: {expected_arguments}"
            )

            # Get the prompt.
            prompt_result = await session.get_prompt(
                "my_prompt_with_optional_arg", {"name": "John"}
            )
            assert isinstance(prompt_result, GetPromptResult)

            # The format differs between sema4ai MCP and standard MCP
            if use_sema4ai_mcp:
                # sema4ai MCP explicitly sets description=None
                expected_prompt_result = {
                    "meta": None,
                    "description": None,
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": "This is the built in prompt for John.",
                                "annotations": None,
                                "meta": None,
                            },
                        }
                    ],
                }
            else:
                # Standard MCP now includes the prompt's description from docstring
                expected_prompt_result = {
                    "meta": None,
                    "description": "\n        Prompt with an optional argument.\n\n        Args:\n            name: The name of the person to greet.\n        ",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": "This is the built in prompt for John.",
                                "annotations": None,
                                "meta": None,
                            },
                        }
                    ],
                }

            found_prompt_result = prompt_result.model_dump()
            assert found_prompt_result == expected_prompt_result, (
                f"Found: {found_prompt_result}. Expected: {expected_prompt_result}"
            )

            # -- Test resources (simple).

            resources_list = await session.list_resources()
            resources = resources_list.resources
            uris = [str(resource.uri) for resource in resources]
            assert ["custom://my/resource/simple"] == uris

            # Read (simple) resource.
            resource = await session.read_resource(resources[0].uri)
            assert isinstance(resource, ReadResourceResult)
            resource_content = resource.contents[0]
            assert isinstance(resource_content, TextResourceContents)
            assert (
                resource_content.text == "This is a simple resource without a template."
            )

            # -- Test resources (template).

            resource_templates_list = await session.list_resource_templates()
            resource_templates = resource_templates_list.resourceTemplates
            uris = [
                str(resource_template.uriTemplate)
                for resource_template in resource_templates
            ]
            assert ["custom://my/resource/{name}"] == uris

            # Read (template) resource.
            uri_template: str = resource_templates[0].uriTemplate
            uri: AnyUrl = AnyUrl(uri_template.replace("{name}", "John"))
            resource = await session.read_resource(uri)
            assert isinstance(resource, ReadResourceResult)
            resource_content = resource.contents[0]
            assert isinstance(resource_content, TextResourceContents)
            assert resource_content.text == "This is the built in resource for John."

            return "ok"


async def check_mcp_server_with_actions(
    port: int,
    connection_mode: Literal["mcp", "sse"],
    headers: dict[str, str] | None = None,
):
    """
    This method is meant to check that the `resources/no_conda/greeter` actions
    work as mcp tools.
    """

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

            tool_names = [tool.name for tool in tools]
            assert "greet" in tool_names, (
                f"greet tool not found. Available tools: {tool_names}"
            )

            greet_tool = next(tool for tool in tools if tool.name == "greet")
            assert greet_tool is not None, (
                f"'greet' tool not found. Available tools: {tool_names}"
            )

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

            # -- Test tool call.

            tool_result = await session.call_tool(
                greet_tool.name, {"name": "John", "title": "Mr."}
            )

            assert isinstance(tool_result, CallToolResult)
            tool_content = tool_result.content[0]
            assert isinstance(tool_content, TextContent)
            assert tool_content.text == "Hello Mr. John.", (
                f"Expected: Hello Mr. John., got: {tool_content.text}"
            )

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

    yield port
    process.stop()


def test_mcp_integration(mcp_server_port: int) -> None:
    """
    Tests that we can check using the "simple_mcp_server.py" (based on the
    standard MCP server implementation using their python SDK).
    """
    from functools import partial

    assert (
        run_async_in_new_thread(
            partial(
                check_mcp_server,
                mcp_server_port,
                "mcp",
                use_sema4ai_mcp=False,
            )
        )
        == "ok"
    )


@pytest.mark.integration_test
def test_mcp_integration_with_actions_in_no_conda_greeter(
    action_server_process: ActionServerProcess,
) -> None:
    """
    Tests that run the mcp server based on `sema4ai.mcp` bundled in the
    action server.
    """
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
                check_mcp_server_with_actions,
                action_server_process.port,
                connection_mode="mcp",  # sse is checked in another test.
            )
        )
        == "ok"
    )


@pytest.mark.parametrize("connection_mode", ["mcp"])
@pytest.mark.integration_test
def test_mcp_integration_with_actions_in_no_conda_mcp(
    action_server_process: ActionServerProcess,
    connection_mode: Literal["mcp", "sse"],
) -> None:
    from functools import partial

    from action_server_tests.fixtures import get_in_resources

    root_dir = get_in_resources("no_conda", "mcp")

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


@pytest.mark.integration_test
@pytest.mark.parametrize("scenario", ["env_var", "request_header"])
def test_mcp_integration_secrets(
    action_server_process: ActionServerProcess,
    scenario: Literal["env_var", "request_header"],
) -> None:
    from functools import partial

    from action_server_tests.fixtures import get_in_resources

    root_dir = get_in_resources("no_conda", "mcp")

    action_server_process.start(
        db_file="server.db",
        cwd=str(root_dir),
        actions_sync=True,
        timeout=60 * 10,
        env={
            "MY_SECRET": "FooSecret",
        }
        if scenario == "env_var"
        else None,
    )

    async def check_with_secrets():
        from mcp.client.streamable_http import streamablehttp_client

        port = action_server_process.port
        async with streamablehttp_client(
            f"http://localhost:{port}/mcp",
            headers={"x-my-secret": "FooSecret"}
            if scenario == "request_header"
            else None,
        ) as (
            read_stream,
            write_stream,
            *_,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_list = await session.list_tools()
                tool_names = [tool.name for tool in tools_list.tools]
                assert "check_secrets" in tool_names, (
                    f"'check_secrets' tool not found. Available tools: {tool_names}"
                )
                result = await session.call_tool("check_secrets", {})
                assert result.content[0].text == "FooSecret", (
                    f"Expected 'FooSecret', got: {result.content[0].text}"
                )
        return "ok"

    assert run_async_in_new_thread(partial(check_with_secrets)) == "ok"
