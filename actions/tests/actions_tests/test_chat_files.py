import pytest


@pytest.fixture
def dummy_server(tmpdir):
    from pathlib import Path

    from actions_tests.files_dummy_server import FilesDummyServer

    ret = FilesDummyServer(Path(tmpdir) / "files")
    ret.start()
    yield ret
    ret.stop()


def test_client_local_mode(tmpdir):
    from pathlib import Path

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
    from pathlib import Path

    monkeypatch.setenv("SEMA4AI_FILE_MANAGEMENT_URL", Path(tmpdir).as_uri())

    from sema4ai.actions import chat

    chat.attach_file_content("my-file.txt", b"some text")
    assert chat.get_file_content("my-file.txt") == b"some text"

    with pytest.raises(IOError):
        # By default, the file is not overwritten!
        chat.attach_file_content("my-file.txt", b"another text")

    # Previous content is preserved
    assert chat.get_file_content("my-file.txt") == b"some text"
