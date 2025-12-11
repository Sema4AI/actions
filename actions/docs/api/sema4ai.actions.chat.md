<!-- markdownlint-disable -->

# module `sema4ai.actions.chat`

# Variables

- **JSONValue**

# Functions

______________________________________________________________________

## `attach_file_content`

Set the content of a file to be used in the current chat.

**Arguments:**

- <b>`name`</b>: Name of the file (must be a valid name to be used to save files in the filesystem).
- <b>`data`</b>: Raw content of the file.
- <b>`content_type`</b>: Content type (or mimetype) of the file.

**Note:**

> The way that the contents are stored may depend on how the action is being run. If the action is being run locally it could be saved in the local filesystem, whereas when running in the cloud it could be saved in a different place, such as an S3 bucket.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L204)

```python
attach_file_content(
    name: str,
    data: bytes,
    content_type='application/octet-stream'
) → None
```

______________________________________________________________________

## `get_file_content`

Get the content of a file in the current action chat.

**Arguments:**

- <b>`name`</b>: Name of file.

**Returns:**
Raw content of the file

**Raises:**

- <b>`Exception`</b>: If the file does not exist (or if it was not possible to retrieve it).

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L234)

```python
get_file_content(name: str) → bytes
```

______________________________________________________________________

## `attach_file`

Attaches a file to the current chat.

**Arguments:**

- <b>`path`</b>: Path to the file which should be attached.
- <b>`content_type`</b>: Content type (or mimetype) of the file.
- <b>`name`</b>: Name of file (if not given the original name of the file will be used).

**Note:**

> The way that the contents are stored may depend on how the action is being run. If the action is being run locally it could be saved in the local filesystem, whereas when running in the cloud it could be saved in a different place, such as an S3 bucket.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L250)

```python
attach_file(
    path: Union[PathLike, str],
    content_type: str | None = None,
    name: str | None = None
) → None
```

______________________________________________________________________

## `attach_json`

Attach a file with JSON content to the current chat.

**Arguments:**

- <b>`name`</b>: Name of the JSON file.
- <b>`contents`</b>: JSON-serializable content.

**Note:**

> The way that the contents are stored may depend on how the action is being run. If the action is being run locally it could be saved in the local filesystem, whereas when running in the cloud it could be saved in a different place, such as an S3 bucket.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L313)

```python
attach_json(
    name: str,
    contents: Optional[Dict[str, ForwardRef('JSONValue')], List[ForwardRef('JSONValue')], str, int, float, bool]
) → None
```

______________________________________________________________________

## `get_json`

Get the JSON content of a file in the current action chat.

**Arguments:**

- <b>`name`</b>: Name of the file with the JSON content to retrieve.

**Returns:**
Deserialized JSON content.

**Note:**

> The way that the contents are stored may depend on how the action is being run. If the action is being run locally it could be saved in the local filesystem, whereas when running in the cloud it could be saved in a different place, such as an S3 bucket.

**Raises:**

- <b>`Exception`</b>: If the file does not exist (or if it was not possible to retrieve itor if the content is not valid JSON).

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L333)

```python
get_json(
    name: str
) → Union[Dict[str, ForwardRef('JSONValue')], List[ForwardRef('JSONValue')], str, int, float, bool, NoneType]
```

______________________________________________________________________

## `attach_text`

Attach a file with text content to the current chat.

**Arguments:**

- <b>`name`</b>: Name of the text file.
- <b>`contents`</b>: Text content.

**Note:**

> The way that the contents are stored may depend on how the action is being run. If the action is being run locally it could be saved in the local filesystem, whereas when running in the cloud it could be saved in a different place, such as an S3 bucket.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L359)

```python
attach_text(name: str, contents: str) → None
```

______________________________________________________________________

## `get_text`

Get the text content of a file in the current action chat.

**Arguments:**

- <b>`name`</b>: Name of the file with the text content to retrieve.

**Returns:**
Text content of the file.

**Raises:**

- <b>`Exception`</b>: If the file does not exist (or if it was not possible to retrieve itor if the content is not valid UTF-8).

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L376)

```python
get_text(name: str) → str
```

______________________________________________________________________

## `get_file`

Get the content of a file in the current action chat, saves it to a temporary file and returns the path to it.

**Arguments:**

- <b>`name`</b>: Name of the file to retrieve.

**Returns:**
Raw content of the file

**Raises:**

- <b>`Exception`</b>: If the file does not exist.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L290)

```python
get_file(name: str) → Path
```

______________________________________________________________________

## `list_files`

Lists all files in the current chat thread.

**Returns:**
A list of filenames in the thread.

**Raises:**

- <b>`RuntimeError`</b>: If unable to get client or thread_id.
- <b>`ValueError`</b>: If the API request fails in remote mode.

**Example:**

` from sema4ai.actions import chat`
` files = chat.list_files()`
` print(files)`
['document.pdf', 'data.json']

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/chat/__init__.py#L393)

```python
list_files() → list[str]
```
