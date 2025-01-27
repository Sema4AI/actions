from pathlib import Path

import pytest


@pytest.fixture
def dummy_server(tmpdir):
    from actions_tests.files_dummy_server import FilesDummyServer

    ret = FilesDummyServer(Path(tmpdir) / "files")
    ret.start()
    yield ret
    ret.stop()


def test_client_local_mode(tmpdir):
    from sema4ai.actions.chat import _client

    p = Path(tmpdir)
    uri = p.as_uri()
    client = _client._Client(uri)
    assert client.is_local_mode()

    client.set_bytes("test.txt", b"some-content", thread_id="some-thread-id")
    assert client.get_bytes("test.txt", thread_id="some-thread-id") == b"some-content"


def test_client_server_write_to_local(dummy_server):
    from sema4ai.actions.chat import _client

    uri = f"http://localhost:{dummy_server.get_port()}"
    client = _client._Client(uri)
    assert not client.is_local_mode()

    client.set_bytes("test.txt", b"some-content", thread_id="some-thread-id")
    assert client.get_bytes("test.txt", thread_id="some-thread-id") == b"some-content"


def test_client_server_write_to_url(dummy_server):
    from sema4ai.actions.chat import _client

    dummy_server.set_write_to_local(False)

    uri = f"http://localhost:{dummy_server.get_port()}"
    client = _client._Client(uri)
    assert not client.is_local_mode()

    client.set_bytes("test.txt", b"some-content", thread_id="some-thread-id")
    assert (
        client.get_bytes("test.txt", thread_id="some-thread-id")
        == b"content-gotten-from-download"
    )


def test_actions_file_api(monkeypatch, tmpdir):
    monkeypatch.setenv("SEMA4AI_FILE_MANAGEMENT_URL", Path(tmpdir).as_uri())

    from sema4ai.actions import chat

    chat.attach_file_content("my-file.txt", b"some text")
    assert chat.get_file_content("my-file.txt") == b"some text"

    # By default, the file is not overwritten!
    chat.attach_file_content("my-file.txt", b"another text")

    # Previous content is preserved
    assert chat.get_file_content("my-file.txt") == b"another text"


def test_actions_with_agent_headers_call_from_agent_server(datadir: Path):
    import json

    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    json_input_contents = {
        "custom_cls": {"filename": str(json_output), "price": 100},
        "request": {
            "headers": {
                "x-action_invocation_id": "call-id-3vvrnSc",
                "x-invoked_by_assistant_id": "assistant-id-36eb74b3",
                "x-invoked_for_thread_id": "thread-id-95542b5c",
                "x-invoked_on_behalf_of_user_id": "user-id-7b89641f",
            }
        },
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_agent_headers",
        datadir,
        f"--json-input={input_json}",
        "--print-input",
        "--print-result",
    ]

    env = {
        "SEMA4AI_FILE_MANAGEMENT_URL": "http://localhost:8000",
    }
    result = sema4ai_actions_run(
        args, returncode=0, cwd=str(datadir), additional_env=env
    )
    # assert json_output.read_text() == "value-in-header"
    output = result.stdout.decode("utf-8")
    assert "thread_id: thread-id-95542b5c" in output


def test_actions_with_agent_headers_call_with_invocation_context(datadir: Path):
    import base64
    import json

    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"

    invocation_context = base64.b64encode(
        json.dumps(
            {
                "agent_id": "agent-id-123",
                "invoked_on_behalf_of_user_id": "user-id-123",
                "thread_id": "thread-id-123",
                "tenant_id": "tenant-id-123",
                "action_invocation_id": "action-invocation-id-123",
            }
        ).encode("utf-8")
    ).decode("ascii")

    json_input_contents = {
        "custom_cls": {"filename": str(json_output), "price": 100},
        "request": {"headers": {"x-action-invocation-context": invocation_context}},
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_agent_headers",
        datadir,
        f"--json-input={input_json}",
        "--print-input",
        "--print-result",
    ]

    env = {
        "SEMA4AI_FILE_MANAGEMENT_URL": "http://localhost:8000",
    }
    result = sema4ai_actions_run(
        args, returncode=0, cwd=str(datadir), additional_env=env
    )
    # assert json_output.read_text() == "value-in-header"
    output = result.stdout.decode("utf-8")
    assert "thread_id: thread-id-123" in output
