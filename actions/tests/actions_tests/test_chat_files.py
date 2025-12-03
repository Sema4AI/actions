from pathlib import Path
from unittest.mock import patch

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


def test_client_local_mode_list_files(tmpdir):
    from sema4ai.actions.chat import _client

    p = Path(tmpdir)
    uri = p.as_uri()
    client = _client._Client(uri)
    assert client.is_local_mode()

    # Initially empty
    files = client.list_files(thread_id="some-thread-id")
    assert files == []

    # Add some files
    client.set_bytes("test1.txt", b"content1", thread_id="some-thread-id")
    client.set_bytes("test2.json", b"content2", thread_id="some-thread-id")
    client.set_bytes("test3.pdf", b"content3", thread_id="some-thread-id")

    # List files
    files = client.list_files(thread_id="some-thread-id")
    assert len(files) == 3
    assert "test1.txt" in files
    assert "test2.json" in files
    assert "test3.pdf" in files


def test_client_server_write_to_local(dummy_server):
    from sema4ai.actions.chat import _client

    uri = f"http://localhost:{dummy_server.get_port()}"
    client = _client._Client(uri)
    assert not client.is_local_mode()

    client.set_bytes("test.txt", b"some-content", thread_id="some-thread-id")
    assert client.get_bytes("test.txt", thread_id="some-thread-id") == b"some-content"


def test_client_server_list_files(dummy_server):
    from sema4ai.actions.chat import _client

    uri = f"http://localhost:{dummy_server.get_port()}"
    client = _client._Client(uri)
    assert not client.is_local_mode()

    # Initially empty
    files = client.list_files(thread_id="some-thread-id")
    assert files == []

    # Add some files
    client.set_bytes("test1.txt", b"content1", thread_id="some-thread-id")
    client.set_bytes("test2.json", b"content2", thread_id="some-thread-id")
    client.set_bytes("test3.pdf", b"content3", thread_id="some-thread-id")

    # List files
    files = client.list_files(thread_id="some-thread-id")
    assert len(files) == 3
    assert "test1.txt" in files
    assert "test2.json" in files
    assert "test3.pdf" in files


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


def test_actions_list_files_api(monkeypatch, tmpdir):
    monkeypatch.setenv("SEMA4AI_FILE_MANAGEMENT_URL", Path(tmpdir).as_uri())

    from sema4ai.actions import chat

    # Initially empty
    files = chat.list_files()
    assert files == []

    # Add some files
    chat.attach_file_content("file1.txt", b"content1")
    chat.attach_file_content("file2.json", b"content2")
    chat.attach_file_content("file3.pdf", b"content3")

    # List files
    files = chat.list_files()
    assert len(files) == 3
    assert "file1.txt" in files
    assert "file2.json" in files
    assert "file3.pdf" in files


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


class TestFilenameValidationWindows:
    """Test filename validation on Windows platform."""

    @patch("sys.platform", new="win32")
    def test_valid_names(self):
        """Test valid filenames that should pass on Windows."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        valid_names = [
            "valid_name.txt",
            "my-file.json",
            "file123.pdf",
            "file_with_underscores.doc",
            "file-with-dashes.txt",
            "CaseSensitive.TXT",
            "unicode_文件.txt",
        ]
        for name in valid_names:
            _check_that_name_is_valid_in_filesystem(name)  # Should not raise

    @pytest.mark.parametrize(
        "filename",
        [
            "report<draft>.txt",
            "output>final.log",
            "meeting:notes.doc",
            'project"alpha".json',
            "docs/readme.txt",
            "path\\to\\file.pdf",
            "data|backup.csv",
            "query?results.xml",
            "search*.txt",
        ],
        ids=[
            "less-than",
            "greater-than",
            "colon",
            "quote",
            "forward-slash",
            "backslash",
            "pipe",
            "question",
            "asterisk",
        ],
    )
    @patch("sys.platform", new="win32")
    def test_invalid_characters(self, filename):
        """Test rejection of invalid characters on Windows."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        with pytest.raises(ValueError, match="invalid characters"):
            _check_that_name_is_valid_in_filesystem(filename)

    @patch("sys.platform", new="win32")
    def test_control_characters(self):
        """Test rejection of control characters on Windows."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        # Test various control characters
        for i in range(32):
            with pytest.raises(ValueError, match="control characters"):
                _check_that_name_is_valid_in_filesystem(f"file{chr(i)}name.txt")

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
            "CON.txt",
            "PRN.doc",
            "LPT1.pdf",
            "filename.txt ",
            "filename.txt.",
        ],
    )
    @patch("sys.platform", new="win32")
    def test_invalid_names(self, invalid_name):
        """Test rejection of Windows invalid names."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        # Test uppercase
        with pytest.raises(ValueError):
            _check_that_name_is_valid_in_filesystem(invalid_name)

        # Test lowercase
        with pytest.raises(ValueError):
            _check_that_name_is_valid_in_filesystem(invalid_name.lower())

        # Test mixed case
        with pytest.raises(ValueError):
            _check_that_name_is_valid_in_filesystem(invalid_name.capitalize())


class TestFilenameValidationUnix:
    """Test filename validation on Unix-like platforms (Linux, macOS)."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            "valid_name.txt",
            "file:with:colons.txt",
            "file*with*stars.txt",
            "file?with?questions.txt",
            "file<with>brackets.txt",
            'file"with"quotes.txt',
            "file|with|pipes.txt",
            "filename ",
            "filename.txt ",
            "filename.",
            "filename.txt.",
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
            "file:with:colons.txt",
        ],
    )
    @patch("sys.platform", new="linux")
    def test_valid_unix_names(self, valid_name):
        """Test that Unix allows characters restricted on Windows."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        _check_that_name_is_valid_in_filesystem(valid_name)  # Should not raise

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "file/name.txt",
            "file\0name.txt",
        ],
    )
    @patch("sys.platform", new="linux")
    def test_invalid_unix_names(self, invalid_name):
        """Test rejection of forward slash on Unix."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        with pytest.raises(ValueError):
            _check_that_name_is_valid_in_filesystem(invalid_name)


class TestFilenameValidationEdgeCases:
    """Test edge cases for filename validation."""

    @patch("sys.platform", new="linux")
    def test_empty_string(self):
        """Test rejection of empty string."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        with pytest.raises(ValueError, match="is not valid"):
            _check_that_name_is_valid_in_filesystem("")

    @patch("sys.platform", new="linux")
    def test_current_directory_dot(self):
        """Test rejection of current directory reference."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        with pytest.raises(ValueError, match="is not valid"):
            _check_that_name_is_valid_in_filesystem(".")

    @patch("sys.platform", new="linux")
    def test_parent_directory_dotdot(self):
        """Test rejection of parent directory reference."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        with pytest.raises(ValueError, match="is not valid"):
            _check_that_name_is_valid_in_filesystem("..")

    @patch("sys.platform", new="linux")
    def test_unicode_characters(self):
        """Test that Unicode characters are allowed."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        unicode_names = [
            "文件.txt",
            "файл.pdf",
            "αρχείο.doc",
            "ファイル.json",
            "🎉celebration.txt",
        ]
        for name in unicode_names:
            _check_that_name_is_valid_in_filesystem(name)  # Should not raise

    @patch("sys.platform", new="linux")
    def test_very_long_name(self):
        """Test very long filename (most filesystems have limits, but we don't enforce them)."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        # Most filesystems limit to 255 bytes, but we don't enforce that
        long_name = "a" * 300 + ".txt"
        _check_that_name_is_valid_in_filesystem(long_name)  # Should not raise

    @patch("sys.platform", new="win32")
    def test_windows_backslash_rejected(self):
        """Test that backslash is rejected on Windows."""
        from sema4ai.actions.chat import _check_that_name_is_valid_in_filesystem

        with pytest.raises(ValueError, match="invalid characters"):
            _check_that_name_is_valid_in_filesystem("file\\name.txt")
