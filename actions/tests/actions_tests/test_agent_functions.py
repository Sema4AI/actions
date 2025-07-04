from pathlib import Path

import pytest
from actions_tests.agent_dummy_server import AgentDummyServer


@pytest.fixture
def agent_dummy_server():
    server = AgentDummyServer()
    server.start()
    yield server
    server.stop()


def test_prompt_generate_with_thread_id(agent_dummy_server):
    """Test prompt_generate with thread_id parameter."""
    import os

    from sema4ai.actions.agent import prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Create a simple prompt as a dictionary
    prompt = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "kind": "text",
                        "text": "Pick a random number between 1 and 100 and tell me what it is.",
                    }
                ],
            }
        ],
        "temperature": 0.0,
        "max_output_tokens": 512,
    }

    # Call prompt_generate with thread_id
    response = prompt_generate(prompt=prompt, thread_id="test-thread-id")

    # Check that the request was made correctly
    assert agent_dummy_server.last_request is not None
    assert agent_dummy_server.last_request["thread_id"] == "test-thread-id"
    assert (
        agent_dummy_server.last_request["body"]["prompt"]["messages"][0]["content"][0][
            "text"
        ]
        == "Pick a random number between 1 and 100 and tell me what it is."
    )

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )


def test_prompt_generate_with_agent_id(agent_dummy_server):
    """Test prompt_generate with agent_id parameter."""
    import os

    from sema4ai.actions.agent import prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Create a simple prompt as a dictionary
    prompt = {
        "messages": [
            {
                "role": "user",
                "content": [{"kind": "text", "text": "Hello, how are you?"}],
            }
        ],
        "temperature": 0.7,
        "max_output_tokens": 256,
    }

    # Call prompt_generate with agent_id
    response = prompt_generate(prompt=prompt, agent_id="test-agent-id")

    # Check that the request was made correctly
    assert agent_dummy_server.last_request is not None
    assert agent_dummy_server.last_request["agent_id"] == "test-agent-id"
    assert (
        agent_dummy_server.last_request["body"]["prompt"]["messages"][0]["content"][0][
            "text"
        ]
        == "Hello, how are you?"
    )

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )


def test_prompt_generate_with_platform_config(agent_dummy_server):
    """Test prompt_generate with platform_config parameter."""
    import os

    from sema4ai.actions.agent import OpenAIPlatformParameters, prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Create a simple prompt as a dictionary
    prompt = {
        "messages": [
            {
                "role": "user",
                "content": [{"kind": "text", "text": "What's the weather like?"}],
            }
        ],
        "temperature": 0.5,
        "max_output_tokens": 128,
    }

    # Create a platform config
    platform_config = OpenAIPlatformParameters(
        openai_api_key="sk_123123", kind="openai"
    )

    # Call prompt_generate with platform_config
    response = prompt_generate(prompt=prompt, platform_config=platform_config)

    # Check that the request was made correctly
    assert agent_dummy_server.last_request is not None
    assert (
        agent_dummy_server.last_request["body"]["prompt"]["messages"][0]["content"][0][
            "text"
        ]
        == "What's the weather like?"
    )
    assert agent_dummy_server.last_request["body"]["platform_config_raw"] is not None

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )


def test_prompt_generate_complex_prompt(agent_dummy_server):
    """Test prompt_generate with the complex prompt structure from the user query."""
    import os

    from sema4ai.actions.agent import prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Create the complex prompt structure as a dictionary
    prompt = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "kind": "text",
                        "text": "Pick a random number between 1 and 100 and tell me what it is.",
                    }
                ],
            },
            {
                "role": "agent",
                "content": [
                    {
                        "kind": "tool_use",
                        "tool_name": "get_range",
                        "tool_call_id": "225817d8-8804-4576-a926-98debb930940",
                        "tool_input_raw": {"max_value": 100, "min_value": 1},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "kind": "tool_result",
                        "tool_name": "get_range",
                        "tool_call_id": "225817d8-8804-4576-a926-98debb930940",
                        "content": [{"kind": "text", "text": "73"}],
                    }
                ],
            },
        ],
        "tools": [
            {
                "name": "get_range",
                "description": "Get a random number between a minimum and maximum value",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "min_value": {
                            "type": "integer",
                            "description": "The minimum value of the range",
                        },
                        "max_value": {
                            "type": "integer",
                            "description": "The maximum value of the range",
                        },
                    },
                    "required": ["min_value", "max_value"],
                },
            }
        ],
        "temperature": 0.0,
        "max_output_tokens": 512,
    }

    # Call prompt_generate with thread_id
    response = prompt_generate(prompt=prompt, thread_id="test-thread-id")

    # Check that the request was made correctly
    assert agent_dummy_server.last_request is not None
    assert agent_dummy_server.last_request["thread_id"] == "test-thread-id"

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )


def test_get_thread_id_from_headers(datadir: Path):
    """Test get_thread_id function using headers."""
    import json

    from devutils.fixtures import sema4ai_actions_run

    # Create a simple action inline for testing
    action_code = '''
from sema4ai.actions import action
from sema4ai.actions.agent import get_thread_id

@action
def action_get_thread_id():
    """Action to test get_thread_id function."""
    thread_id = get_thread_id()
    result = f"thread_id: {thread_id}"
    return result
'''

    # Write the action to a temporary file
    action_file = datadir / "temp_action.py"
    action_file.write_text(action_code)

    # Test getting thread_id from headers
    json_input_contents = {
        "request": {
            "headers": {
                "x-invoked_for_thread_id": "thread-id-from-header",
            }
        },
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_get_thread_id",
        datadir,
        f"--json-input={input_json}",
        "--print-result",
    ]

    result = sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    output = result.stdout.decode("utf-8")
    assert "thread_id: thread-id-from-header" in output


def test_get_agent_id_from_headers(datadir: Path):
    """Test get_agent_id function using headers."""
    import json

    from devutils.fixtures import sema4ai_actions_run

    # Create a simple action inline for testing
    action_code = '''
from sema4ai.actions import action
from sema4ai.actions.agent import get_agent_id

@action
def action_get_agent_id():
    """Action to test get_agent_id function."""
    agent_id = get_agent_id()
    result = f"agent_id: {agent_id}"
    return result
'''

    # Write the action to a temporary file
    action_file = datadir / "temp_action.py"
    action_file.write_text(action_code)

    # Test getting agent_id from headers
    json_input_contents = {
        "request": {
            "headers": {
                "x-invoked_for_agent_id": "agent-id-from-header",
            }
        },
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_get_agent_id",
        datadir,
        f"--json-input={input_json}",
        "--print-result",
    ]

    result = sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    output = result.stdout.decode("utf-8")
    assert "agent_id: agent-id-from-header" in output


def test_get_thread_id_from_invocation_context(datadir: Path):
    """Test get_thread_id function using invocation context."""
    import base64
    import json

    from devutils.fixtures import sema4ai_actions_run

    # Create a simple action inline for testing
    action_code = '''
from sema4ai.actions import action
from sema4ai.actions.agent import get_thread_id

@action
def action_get_thread_id():
    """Action to test get_thread_id function."""
    thread_id = get_thread_id()
    result = f"thread_id: {thread_id}"
    return result
'''

    # Write the action to a temporary file
    action_file = datadir / "temp_action.py"
    action_file.write_text(action_code)

    # Test getting thread_id from invocation context
    invocation_context = base64.b64encode(
        json.dumps(
            {
                "thread_id": "thread-id-from-context",
                "agent_id": "agent-id-from-context",
            }
        ).encode("utf-8")
    ).decode("ascii")

    json_input_contents = {
        "request": {"headers": {"x-action-invocation-context": invocation_context}},
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_get_thread_id",
        datadir,
        f"--json-input={input_json}",
        "--print-result",
    ]

    result = sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    output = result.stdout.decode("utf-8")
    assert "thread_id: thread-id-from-context" in output


def test_get_agent_id_from_invocation_context(datadir: Path):
    """Test get_agent_id function using invocation context."""
    import base64
    import json

    from devutils.fixtures import sema4ai_actions_run

    # Create a simple action inline for testing
    action_code = '''
from sema4ai.actions import action
from sema4ai.actions.agent import get_agent_id

@action
def action_get_agent_id():
    """Action to test get_agent_id function."""
    agent_id = get_agent_id()
    result = f"agent_id: {agent_id}"
    return result
'''

    # Write the action to a temporary file
    action_file = datadir / "temp_action.py"
    action_file.write_text(action_code)

    # Test getting agent_id from invocation context
    invocation_context = base64.b64encode(
        json.dumps(
            {
                "thread_id": "thread-id-from-context",
                "agent_id": "agent-id-from-context",
            }
        ).encode("utf-8")
    ).decode("ascii")

    json_input_contents = {
        "request": {"headers": {"x-action-invocation-context": invocation_context}},
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_get_agent_id",
        datadir,
        f"--json-input={input_json}",
        "--print-result",
    ]

    result = sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    output = result.stdout.decode("utf-8")
    assert "agent_id: agent-id-from-context" in output


def test_prompt_validation_errors(agent_dummy_server):
    """Test that prompt_generate raises Pydantic validation errors when called with invalid dict data."""
    import os

    import pytest
    from pydantic import ValidationError

    from sema4ai.actions.agent import prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Test 1: Invalid message structure - missing required fields
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": "Hello",
                                # Missing 'kind' field which is required
                            }
                        ],
                    }
                ]
            },
            thread_id="test-thread-id",
        )

    # Check that the error message contains information about the validation failure
    error_msg = str(exc_info.value)
    assert "kind" in error_msg.lower()

    # Test 2: Invalid content type in user message
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": "Hello",
                                "kind": "invalid_kind",  # Invalid kind value
                            }
                        ],
                    }
                ]
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "kind" in error_msg.lower()

    # Test 3: Invalid tool definition structure
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "tools": [
                    {
                        "name": "test_tool",
                        # Missing required 'description' and 'input_schema' fields
                    }
                ],
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "description" in error_msg.lower() or "input_schema" in error_msg.lower()

    # Test 4: Invalid tool_choice value (should be "auto", "any", or a string)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "tool_choice": 123,  # Invalid type - should be string
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "tool_choice" in error_msg.lower()

    # Test 5: Invalid message role
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [
                    {
                        "role": "invalid_role",  # Invalid role
                        "content": [{"text": "Hello", "kind": "text"}],
                    }
                ]
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "role" in error_msg.lower()

    # Test 6: Invalid tool input schema
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "input_schema": "invalid_schema",  # Should be dict, not string
                    }
                ],
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "input_schema" in error_msg.lower()

    # Test 7: Invalid stop_sequences (should be list of strings)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "stop_sequences": ["valid", 123, "also_valid"],  # Mixed types
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "stop_sequences" in error_msg.lower()

    # Test 8: Invalid temperature type (should be float or None)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "temperature": "not_a_float",  # Invalid type - should be float
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "temperature" in error_msg.lower()

    # Test 9: Invalid max_output_tokens type (should be int or None)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "max_output_tokens": "not_an_int",  # Invalid type - should be int
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "max_output_tokens" in error_msg.lower()

    # Test 10: Invalid top_p type (should be float or None)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "top_p": "not_a_float",  # Invalid type - should be float
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "top_p" in error_msg.lower()

    # Test 11: Invalid seed type (should be int or None)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "seed": "not_an_int",  # Invalid type - should be int
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "seed" in error_msg.lower()

    # Test 12: Invalid system_instruction type (should be str or None)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "system_instruction": 123,  # Invalid type - should be string
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "system_instruction" in error_msg.lower()

    # Test 13: Invalid messages type (should be list)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": "not_a_list"  # Invalid type - should be list
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "messages" in error_msg.lower()

    # Test 14: Invalid tools type (should be list)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt={
                "messages": [],
                "tools": "not_a_list",  # Invalid type - should be list
            },
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "tools" in error_msg.lower()
