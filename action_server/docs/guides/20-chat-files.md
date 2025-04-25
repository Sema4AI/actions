## Working with Files in Chat Actions

The `sema4ai.actions.chat` module provides functionality to attach and retrieve files during chat interactions.

### Why These APIs Are Needed

These APIs are essential because when running in the cloud (Workroom), actions don't have access to the local filesystem.

`CAVEAT`: It's possible to access files locally when developing an action in VSCode, but then, later on, when running in the cloud, where
multiple servers may be involved, files stored in one action will NOT be available in a new action invocation.

As such, the `sema4ai.actions.chat` module was created to provide a consistent way to handle files across both local and cloud environments.

`NOTE`: Data shared through these APIs are properly isolated between different chat threads, so, for instance, files uploaded in one chat thread are not available in another.

### Available Functions

The module provides several functions to work with files:

1. **Attaching Files**:

   ```python
   from sema4ai.actions.chat import attach_file, attach_file_content, attach_json, attach_text

   # Attach an existing file
   attach_file("/full/path/to/file.txt")

   # Attach raw content
   attach_file_content("myfile.txt", b"raw content", "text/plain")

   # Attach JSON data
   attach_json("data.json", {"key": "value"})

   # Attach text content
   attach_text("note.txt", "This is a text note")
   ```

2. **Retrieving Files**:

   ```python
   from sema4ai.actions.chat import get_file, get_file_content, get_json, get_text

   # Get file as Path object
   # Note: under the scenes this will `get_file_content`, create a temp file and return a Path object for the temporary file.
   file_path = get_file("myfile.txt")

   # Get raw content
   content = get_file_content("myfile.txt")

   # Get JSON data
   data = get_json("data.json")

   # Get text content
   text = get_text("note.txt")
   ```

`IMPORTANT`: When running in the cloud, all interactions will pass the data through network calls (and as such may fail due to network issues).

`NOTE`: If the file is not found, an exception will be raised.

`NOTE`: The name of the file will be the name of the file in the chat. It must only have valid characters for a filename
and may not contain any path separators (like `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`).

### Usage Example

Here's a complete example showing how to make an action that can add data and retrieve it later:

```python
from sema4ai.actions import action, Response
from sema4ai.actions.chat import get_json, attach_json


@action
def add_note(note: str) -> Response[bool]:
    """
    Add a note.

    Args:
        note: The note to add.

    Returns:
        A boolean indicating whether the note was added successfully.
    """

    try:
        notes = get_json("notes.json")
    except Exception:
        notes = []

    notes.append(note)
    attach_json("notes.json", notes)

    return Response(True)


@action
def get_notes(search: str="") -> Response[list[str]]:
    """
    Get the notes previously added.

    Args:
        search: The search query to filter the notes.

    Returns:
        The notes which were found.
    """

    try:
        notes = get_json("notes.json")
    except Exception:
        notes = []

    if search:
        notes = [note for note in notes if search.lower() in note.lower()]

    return Response(notes)
```

### File Storage Location

The storage location for files depends on the environment and how the action is being run:

1. **In VSCode with Sema4.ai Extension**:
   When running actions in VSCode with the Sema4.ai Extension, files are stored in a local directory at:

   ```
   file://<path-to-action-package>/devdata/chat-files
   ```

   This is the default behavior specifically for the VSCode development environment.

2. **In Production (Workroom)**:
   When running in production through Workroom, files are automatically stored in cloud storage.

3. **Custom Configuration**:
   For other development environments or custom setups, you can override the storage location by setting the `SEMA4AI_FILE_MANAGEMENT_URL` environment variable.
