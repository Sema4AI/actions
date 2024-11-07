import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Union

from sema4ai.actions._protocols import JSONValue

log = logging.getLogger(__name__)


def _check_that_name_is_valid_in_filesystem(name: str):
    invalid_characters = r'<>:"/\|?*'
    if any(char in name for char in invalid_characters):
        raise ValueError(
            f"Name {name} contains invalid characters: {invalid_characters}"
        )

    # Reserved names:
    # CON, PRN, AUX, NUL
    # COM1, COM2, COM3, COM4, COM5, COM6, COM7, COM8, COM9
    # LPT1, LPT2, LPT3, LPT4, LPT5, LPT6, LPT7, LPT8, LPT9
    name_without_extension = os.path.splitext(name)[0]
    if name_without_extension in [
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
    ]:
        raise ValueError(f"Name {name} is reserved and cannot be used.")

    # Filenames cannot end in a space or dot.
    if name.endswith(" ") or name.endswith("."):
        raise ValueError(f"Name {name} cannot end in a space or dot.")


def _get_client_and_thread_id():
    from sema4ai.actions._action import get_current_action_context

    from ._client import _Client

    client = _Client()
    if not client.is_local_mode():
        action_context = get_current_action_context()
        if not action_context:
            raise RuntimeError(
                "No action context found, as such it's not possible to upload files!"
            )

        value = action_context.value
        if not isinstance(value, dict):
            raise RuntimeError(
                "Action context value is not a dictionary, as such it's not possible to upload files!"
            )

        invocation_context = value.get("invocation_context")
        if not invocation_context:
            raise RuntimeError(
                "No invocation context found in the action context, as such it's not possible to upload files!"
            )
        if not isinstance(invocation_context, dict):
            raise RuntimeError(
                "invocation_context is not a dictionary, as such it's not possible to upload files!"
            )

        thread_id = invocation_context.get("thread_id")
        if not thread_id:
            raise RuntimeError(
                "No thread_id found in the invocation_context, as such it's not possible to upload files!"
            )
        if not isinstance(thread_id, str):
            raise RuntimeError(
                f"thread_id is not a string (found: {thread_id} ({type(thread_id)})), as such it's not possible to upload files!"
            )
    else:
        thread_id = "local"  # Ok, we're in local mode, so we don't need the thread_id!
    return client, thread_id


@lru_cache
def _get_mimetype_module():
    KNOWN_MIMETYPES = [
        ("text/x-yaml", ".yml"),
        ("text/x-yaml", ".yaml"),
    ]
    import mimetypes

    for type_, ext in KNOWN_MIMETYPES:
        mimetypes.add_type(type_, ext)

    return mimetypes


def attach_file_content(
    name: str,
    data: bytes,
    content_type="application/octet-stream",
) -> None:
    """
    Set the content of a file to be used in the current chat.

    Arguments:
        name: Name of the file (must be a valid name to be used to save files in the filesystem).
        data: Raw content of the file.
        content_type: Content type (or mimetype) of the file.

    Note:
        The way that the contents are stored may depend on how the action is being run.
        If the action is being run locally it could be saved in the local filesystem,
        whereas when running in the cloud it could be saved in a different place, such
        as an S3 bucket.
    """
    if not isinstance(data, bytes):
        raise ValueError(f"data must be bytes. Received: {type(data)}")

    # Now, verify that the name does not contain any path separators or other characters that are not allowed in the filesystem.
    _check_that_name_is_valid_in_filesystem(name)

    client, thread_id = _get_client_and_thread_id()

    client.set_bytes(name, data, thread_id, content_type)


def get_file_content(name: str) -> bytes:
    """
    Get the content of a file in the current action chat.

    Arguments:
        name: Name of file.
    Returns:
        Raw content of the file

    Raises:
        Exception: If the file does not exist (or if it was not possible to retrieve it).
    """
    client, thread_id = _get_client_and_thread_id()
    return client.get_bytes(name, thread_id)


def attach_file(
    path: Union[os.PathLike, str],
    content_type: str | None = None,
    name: str | None = None,
) -> None:
    """
    Attaches a file to the current chat.

    Arguments:
        path: Path to the file which should be attached.
        content_type: Content type (or mimetype) of the file.
        name: Name of file (if not given the original name of the file will be used).

    Note:
        The way that the contents are stored may depend on how the action is being run.
        If the action is being run locally it could be saved in the local filesystem,
        whereas when running in the cloud it could be saved in a different place, such
        as an S3 bucket.
    """

    if content_type is None:
        mimetypes = _get_mimetype_module()

        content_type, _ = mimetypes.guess_type(path)
        if content_type is not None:
            log.info("Detected content type %r", content_type)
        else:
            content_type = "application/octet-stream"
            log.info("Unable to detect content type, using %r", content_type)

    p = Path(path)

    if name is None:
        name = p.name

    if not p.exists():
        raise IOError(f"Error: unable to attach file that does not exist: {p}")
    attach_file_content(name, p.read_bytes(), content_type)


def get_file(name: str) -> Path:
    """
    Get the content of a file in the current action chat, saves it to a temporary file
    and returns the path to it.

    Arguments:
        name: Name of the file to retrieve.
    Returns:
        Raw content of the file

    Raises:
        Exception: If the file does not exist.
    """
    import tempfile

    file_content = get_file_content(name)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
    return Path(temp_file_path)


def attach_json(name: str, contents: JSONValue) -> None:
    """
    Attach a file with JSON content to the current chat.

    Arguments:
        name: Name of the JSON file.
        contents: JSON-serializable content.

    Note:
        The way that the contents are stored may depend on how the action is being run.
        If the action is being run locally it could be saved in the local filesystem,
        whereas when running in the cloud it could be saved in a different place, such
        as an S3 bucket.
    """
    import json

    json_data = json.dumps(contents).encode("utf-8")
    attach_file_content(name, json_data, "application/json")


def get_json(name: str) -> JSONValue:
    """
    Get the JSON content of a file in the current action chat.

    Arguments:
        name: Name of the file with the JSON content to retrieve.

    Returns:
        Deserialized JSON content.

    Note:
        The way that the contents are stored may depend on how the action is being run.
        If the action is being run locally it could be saved in the local filesystem,
        whereas when running in the cloud it could be saved in a different place, such
        as an S3 bucket.

    Raises:
        Exception: If the file does not exist (or if it was not possible to retrieve it
        or if the content is not valid JSON).
    """
    import json

    content = get_file_content(name)
    return json.loads(content.decode("utf-8"))


def attach_text(name: str, contents: str) -> None:
    """
    Attach a file with text content to the current chat.

    Arguments:
        name: Name of the text file.
        contents: Text content.

    Note:
        The way that the contents are stored may depend on how the action is being run.
        If the action is being run locally it could be saved in the local filesystem,
        whereas when running in the cloud it could be saved in a different place, such
        as an S3 bucket.
    """
    attach_file_content(name, contents.encode("utf-8"), "text/plain")


def get_text(name: str) -> str:
    """
    Get the text content of a file in the current action chat.

    Arguments:
        name: Name of the file with the text content to retrieve.
    Returns:
        Text content of the file.

    Raises:
        Exception: If the file does not exist (or if it was not possible to retrieve it
        or if the content is not valid UTF-8).
    """
    content = get_file_content(name)
    return content.decode("utf-8")


__all__ = [
    "JSONValue",
    "FileId",
    "attach_file_content",
    "get_file_content",
    "attach_file",
    "attach_json",
    "get_json",
    "attach_text",
    "get_text",
]
