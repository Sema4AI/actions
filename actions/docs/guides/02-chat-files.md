## Working with Files in Chat Actions

The `sema4ai.actions.chat` module provides functionality to attach and retrieve files during chat interactions.

### Default File Storage Location

By default, files are stored in a local directory at:
```
file://<path-to-action>/devdata/chat-files
```

This location can be overridden by setting the `SEMA4AI_FILE_MANAGEMENT_URL` environment variable to a different URL.
This is useful for:
- Development: Use a local directory
- Production: Use a cloud storage service

### Available Functions

The module provides several functions to work with files:

1. **Attaching Files**:
   ```python
   from sema4ai.actions.chat import attach_file, attach_file_content, attach_json, attach_text

   # Attach an existing file
   attach_file("path/to/file.txt")

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
   file_path = get_file("myfile.txt")

   # Get raw content
   content = get_file_content("myfile.txt")

   # Get JSON data
   data = get_json("data.json")

   # Get text content
   text = get_text("note.txt")
   ```

### Usage Example

Here's a complete example showing how to use these functions in an action:

```python
from sema4ai.actions import action
from sema4ai.actions.chat import attach_file, get_file

@action
def process_file(file_path: str) -> str:
    """
    Process a file and return its contents.

    Args:
        file_path: Path to the file to process.

    Returns:
        A message indicating the file was processed.
    """
    # Attach the file to the chat
    attach_file(file_path)

    # Get the file content
    file_content = get_file(file_path)

    # Process the file...

    return f"File {file_path} was processed successfully"
```
