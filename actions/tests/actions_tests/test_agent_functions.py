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


def test_prompt_no_validation_with_dicts(agent_dummy_server):
    """Test that prompt_generate handles validation correctly: dicts are not validated."""
    import os

    from sema4ai.actions.agent import prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Test 1: Invalid dict structure - should pass without validation (escape hatch behavior)
    invalid_dict_prompt = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": "Hello",
                        # Missing 'kind' field which would be required for Pydantic models
                    }
                ],
            }
        ],
        "temperature": "not_a_float",  # Invalid type for Pydantic models
        "max_output_tokens": "not_an_int",  # Invalid type for Pydantic models
    }

    # This should work without raising validation errors since it's a dict
    response = prompt_generate(prompt=invalid_dict_prompt, thread_id="test-thread-id")
    assert response is not None

    # Test 2: Invalid dict with wrong content type - should pass without validation
    invalid_content_dict = {
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
    }

    # This should work without raising validation errors since it's a dict
    response = prompt_generate(prompt=invalid_content_dict, thread_id="test-thread-id")
    assert response is not None


def test_prompt_generate_with_pydantic_models(agent_dummy_server):
    """Test prompt_generate with Pydantic models to ensure validation and model_dump() works correctly."""
    import os

    from sema4ai.actions.agent import (
        OpenAIPlatformParameters,
        Prompt,
        PromptTextContent,
        PromptUserMessage,
        prompt_generate,
    )

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Create a prompt using Pydantic models
    prompt = Prompt(
        messages=[
            PromptUserMessage(content=[PromptTextContent(text="Hello, how are you?")])
        ],
        temperature=0.7,
        max_output_tokens=256,
    )

    # Create a platform config using Pydantic model
    platform_config = OpenAIPlatformParameters(
        openai_api_key="sk_123123", kind="openai"
    )

    # Call prompt_generate with Pydantic models
    response = prompt_generate(prompt=prompt, platform_config=platform_config)

    # Check that the request was made correctly
    assert agent_dummy_server.last_request is not None
    assert (
        agent_dummy_server.last_request["body"]["prompt"]["messages"][0]["content"][0][
            "text"
        ]
        == "Hello, how are you?"
    )
    assert agent_dummy_server.last_request["body"]["platform_config_raw"] is not None

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )


def test_prompt_generate_with_dicts_no_validation(agent_dummy_server):
    """Test that prompt_generate accepts invalid dicts without validation (escape hatch behavior)."""
    import os

    from sema4ai.actions.agent import prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Test with invalid dict structure - should pass without validation
    invalid_prompt = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": "Hello",
                        # Missing 'kind' field which would be required for Pydantic models
                    }
                ],
            }
        ],
        "temperature": "not_a_float",  # Invalid type for Pydantic models
        "max_output_tokens": "not_an_int",  # Invalid type for Pydantic models
    }

    # This should work without raising validation errors
    response = prompt_generate(prompt=invalid_prompt, thread_id="test-thread-id")

    # Check that the request was made correctly
    assert agent_dummy_server.last_request is not None
    assert agent_dummy_server.last_request["thread_id"] == "test-thread-id"
    assert (
        agent_dummy_server.last_request["body"]["prompt"]["messages"][0]["content"][0][
            "text"
        ]
        == "Hello"
    )

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )


def test_prompt_generate_pydantic_validation_errors(agent_dummy_server):
    """Test that prompt_generate raises Pydantic validation errors when called with invalid Pydantic models."""
    import os

    import pytest
    from pydantic import ValidationError
    from sema4ai.actions.agent import (
        Prompt,
        PromptTextContent,
        PromptUserMessage,
        prompt_generate,
    )

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Test 1: Invalid Pydantic model structure - missing required fields
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt=Prompt(
                messages=[
                    PromptUserMessage(
                        content=[
                            PromptTextContent(text="Hello")
                            # This should work fine
                        ]
                    )
                ],
                temperature="not_a_float",  # Invalid type - should raise validation error
            ),
            thread_id="test-thread-id",
        )

    # Check that the error message contains information about the validation failure
    error_msg = str(exc_info.value)
    assert "temperature" in error_msg.lower()

    # Test 2: Invalid content type in user message
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt=Prompt(
                messages=[
                    PromptUserMessage(
                        content=[
                            PromptTextContent(
                                text="Hello", kind="invalid_kind"
                            )  # Invalid kind value
                        ]
                    )
                ]
            ),
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "kind" in error_msg.lower()

    # Test 3: Invalid max_output_tokens type (should be int or None)
    with pytest.raises(ValidationError) as exc_info:
        prompt_generate(
            prompt=Prompt(
                messages=[PromptUserMessage(content=[PromptTextContent(text="Hello")])],
                max_output_tokens="not_an_int",  # Invalid type - should be int
            ),
            thread_id="test-thread-id",
        )

    error_msg = str(exc_info.value)
    assert "max_output_tokens" in error_msg.lower()


def test_prompt_generate_mixed_dict_and_pydantic(agent_dummy_server):
    """Test prompt_generate with mixed dict and Pydantic model inputs."""
    import os

    from sema4ai.actions.agent import OpenAIPlatformParameters, prompt_generate

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Create a prompt as dict (no validation)
    prompt_dict = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": "Hello from dict",
                        # Missing 'kind' field - would fail Pydantic validation
                    }
                ],
            }
        ],
        "temperature": 0.5,
    }

    # Create platform config as Pydantic model (should be validated and model_dump() called)
    platform_config = OpenAIPlatformParameters(
        openai_api_key="sk_123123", kind="openai"
    )

    # Call prompt_generate with mixed inputs
    response = prompt_generate(prompt=prompt_dict, platform_config=platform_config)

    # Check that the request was made correctly
    assert agent_dummy_server.last_request is not None
    assert (
        agent_dummy_server.last_request["body"]["prompt"]["messages"][0]["content"][0][
            "text"
        ]
        == "Hello from dict"
    )
    assert agent_dummy_server.last_request["body"]["platform_config_raw"] is not None

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )


def test_prompt_generate_model_dump_behavior(agent_dummy_server):
    """Test that model_dump() is called correctly for Pydantic models."""
    import os

    from sema4ai.actions.agent import (
        OpenAIPlatformParameters,
        Prompt,
        PromptTextContent,
        PromptUserMessage,
        prompt_generate,
    )

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Create Pydantic models
    prompt = Prompt(
        messages=[
            PromptUserMessage(
                content=[PromptTextContent(text="Test model_dump behavior")]
            )
        ],
        temperature=0.8,
        max_output_tokens=512,
    )

    platform_config = OpenAIPlatformParameters(
        openai_api_key="sk_test_key", kind="openai"
    )

    # Call prompt_generate
    response = prompt_generate(prompt=prompt, platform_config=platform_config)

    # Verify that the request body contains the dumped data (not Pydantic objects)
    request_body = agent_dummy_server.last_request["body"]

    # Check that prompt is a dict (not a Pydantic model)
    assert isinstance(request_body["prompt"], dict)
    assert request_body["prompt"]["temperature"] == 0.8
    assert request_body["prompt"]["max_output_tokens"] == 512

    # Check that platform_config_raw is a dict (not a Pydantic model)
    assert isinstance(request_body["platform_config_raw"], dict)
    assert request_body["platform_config_raw"]["openai_api_key"] == "sk_test_key"
    assert request_body["platform_config_raw"]["kind"] == "openai"

    # Check the response
    assert (
        response["content"][0]["text"]
        == "The random number I picked between 1 and 100 is 73."
    )
