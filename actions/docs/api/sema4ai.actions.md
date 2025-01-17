<!-- markdownlint-disable -->

# module `sema4ai.actions`

Sema4.ai Actions enables running your AI actions in the Sema4.ai Action Server.

To use:

Mark actions with:

```
from sema4ai.actions import action

@action
def my_action():
    ...
```

And then go to a parent folder containing the action and serve them by  running `action-server start`.

Note that it's also possible to programmatically run actions (without the Action Server) with:

Run all the actions in a .py file:

`python -m sema4ai.actions run <path_to_file>`

Run all the actions in files named *action*.py:

`python -m sema4ai.actions run <directory>`

Run only actions with a given name:

`python -m sema4ai.actions run <directory or file> -t <action_name>`

# Variables

- **RowValue**

# Functions

______________________________________________________________________

## `action`

Decorator for actions (entry points) which can be executed by `sema4ai.actions`.

i.e.:

If a file such as actions.py has the contents below:

```python
from sema4ai.actions import action

@action
def enter_user() -> str:
    ...
```

It'll be executable by sema4ai actions as:

python -m sema4ai.actions run actions.py -a enter_user

**Args:**

- <b>`func`</b>:  A function which is an action to `sema4ai.actions`.
- <b>`is_consequential`</b>:  Whether the action is consequential or not. This will add `x-openai-isConsequential: true` to the action metadata and shown in OpenApi spec.
- <b>`display_name`</b>:  A name to be displayed for this action. If given will be used as the openapi.json summary for this action.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/__init__.py#L61)

```python
action(*args, **kwargs)
```

______________________________________________________________________

## `action_cache`

Provides decorator which caches return and clears it automatically when the current action has been run.

A decorator which automatically cache the result of the given function and will return it on any new invocation until sema4ai-actions finishes running the current action.

The function may be either a generator with a single yield (so, the first yielded value will be returned and when the cache is released the generator will be resumed) or a function returning some value.

**Args:**

- <b>`func`</b>:  wrapped function.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/__init__.py#L157)

```python
action_cache(func)
```

______________________________________________________________________

## `get_current_action`

Provides the action which is being currently run or None if not currently running an action.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/__init__.py#L192)

```python
get_current_action() → Optional[IAction]
```

______________________________________________________________________

## `get_output_dir`

Provide the output directory being used for the run or None if there's no output dir configured.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/__init__.py#L179)

```python
get_output_dir() → Optional[Path]
```

______________________________________________________________________

## `session_cache`

Provides decorator which caches return and clears automatically when all actions have been run.

A decorator which automatically cache the result of the given function and will return it on any new invocation until sema4ai-actions finishes running all actions.

The function may be either a generator with a single yield (so, the first yielded value will be returned and when the cache is released the generator will be resumed) or a function returning some value.

**Args:**

- <b>`func`</b>:  wrapped function.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/__init__.py#L135)

```python
session_cache(func)
```

______________________________________________________________________

## `setup`

Run code before any actions start, or before each separate action.

Receives as an argument the action or actions that will be run.

Can be used as a decorator without arguments:

```python
from sema4ai.actions import setup

@setup
def my_fixture(action):
    print(f"Before action: {action.name}")
```

Alternatively, can be called with a `scope` argument to decide when the fixture is run:

```python
from sema4ai.actions import setup

@setup(scope="action")
def before_each(action):
    print(f"Running action '{action.name}'")

@setup(scope="session")
def before_all(actions):
    print(f"Running {len(actions)} action(s)")
```

By default, runs setups in `action` scope.

The `setup` fixture also allows running code after the execution, if it `yield`s the execution to the action(s):

```python
import time
from sema4ai.actions import setup

@setup
def measure_time(action):
    start = time.monotonic()
    yield  # Action executes here
    duration = time.monotonic() - start
    print(f"Action took {duration} seconds")

@action
def my_long_action():
    ...
```

**Note:** If fixtures are defined in another file, they need to be imported in the main actions file to be taken into use

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_fixtures.py#L26)

```python
setup(
    *args,
    **kwargs
) → Union[Callable[[IAction], Any], Callable[[Callable[[IAction], Any]], Callable[[IAction], Any]], Callable[[Callable[[Sequence[IAction]], Any]], Callable[[Sequence[IAction]], Any]]]
```

______________________________________________________________________

## `teardown`

Run code after actions have been run, or after each separate action.

Receives as an argument the action or actions that were executed, which contain (among other things) the resulting status and possible error message.

Can be used as a decorator without arguments:

```python
from sema4ai.actions import teardown

@teardown
def my_fixture(action):
    print(f"After action: {action.name})
```

Alternatively, can be called with a `scope` argument to decide when the fixture is run:

```python
from sema4ai.actions import teardown

@teardown(scope="action")
def after_each(action):
    print(f"Action '{action.name}' status is '{action.status}'")

@teardown(scope="session")
def after_all(actions):
    print(f"Executed {len(actions)} action(s)")
```

By default, runs teardowns in `action` scope.

**Note:** If fixtures are defined in another file, they need to be imported in the main actions file to be taken into use

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_fixtures.py#L150)

```python
teardown(
    *args,
    **kwargs
) → Union[Callable[[IAction], Any], Callable[[Callable[[IAction], Any]], Callable[[IAction], Any]], Callable[[Callable[[Sequence[IAction]], Any]], Callable[[Sequence[IAction]], Any]]]
```

______________________________________________________________________

# Class `IAction`

## Properties

- `failed`

Returns true if the action failed. (in which case usually exc_info is not None).

- `input_schema`

The input schema from the function signature.

**Example:**

```
{
    "properties": {
        "value": {
            "type": "integer",
            "description": "Some value.",
            "title": "Value",
            "default": 0
        }
    },
    "type": "object"
}
```

- `lineno`

The line where the action is declared.

- `managed_params_schema`

The schema for the managed parameters.

**Example:**

```
{
    "my_password": {
        "type": "Secret"
    },
    "request": {
        "type": "Request"
    }
}
```

- `name`

The name of the action.

- `output_schema`

The output schema based on the function signature.

**Example:**

```
{
    "type": "string",
    "description": ""
}
```

## Methods

______________________________________________________________________

### `run`

Runs the action and returns its result.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_protocols.py#L138)

```python
run() → Any
```

______________________________________________________________________

# Class `OAuth2Secret`

This class should be used to specify that OAuth2 secrets should be received.

The way to use it is by declaring a variable with the 'OAuth2Secret' type in the @action along with its accepted provider and scope as Literals.

**Example:**

```
from sema4ai.actions import action, OAuth2Secret

@action
def add_column_to_spreadsheet(
    spreadsheet_name: str,
    google_oauth2_secret: OAuth2Secret[
        Literal["google"],
        list[
            Literal[
                "https://www.googleapis.com/auth/spreadsheets",
            ]
        ],
    ]
):
    ...
    add_column(spreadsheet_name, google_oauth2_secret.access_token)
```

Note: this class is abstract and is not meant to be instanced by clients. An instance can be created from one of the factory methods (`model_validate`or `from_action_context`).

## Properties

- `access_token`

- `metadata`

- `provider`

- `scopes`

## Methods

______________________________________________________________________

### `from_action_context`

Creates an OAuth2 Secret given the action context (which may be encrypted in memory until the actual secret value is requested).

**Args:**

- <b>`action_context`</b>:  The action context which has the secret.

- <b>`path`</b>:  The path inside of the action context for the secret datarequested (Example: 'secrets/my_secret_name').

Return: An OAuth2Secret instance collected from the passed action context.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_secret/__init__.py#L169)

```python
from_action_context(action_context: 'ActionContext', path: str) → OAuth2Secret
```

______________________________________________________________________

### `model_validate`

Creates an OAuth2 Secret given a dict with the information (expected when the user is passing the arguments using a json input).

**Args:**

- <b>`value`</b>:  The dict containing the information to build the OAuth2 Secret.

Return: An OAuth2Secret instance with the given value.

Note: the model_validate method is used for compatibility with the pydantic API.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_secret/__init__.py#L144)

```python
model_validate(value: dict) → OAuth2Secret
```

______________________________________________________________________

# Class `Request`

Contains the information exposed in a request (such as headers and cookies).

May be extended in the future to provide more information.

## Properties

- `cookies`

Provides the cookies received in the request.

- `headers`

Provides the headers received in the request (excluding `cookies` which are available in `cookies`).

## Methods

______________________________________________________________________

### `model_validate`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_request.py#L100)

```python
model_validate(dct: dict) → Request
```

______________________________________________________________________

# Class `Response`

The response class provides a way for the user to signal that the action completed successfully with a given result or the action completed with some error (which the LLM can later show).

## Properties

- `model_extra`

Get extra fields set during validation.

**Returns:**
A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`.

- `model_fields_set`

Returns the set of fields that have been explicitly set on this model instance.

**Returns:**
A set of strings representing the fields that have been set, i.e. that were not filled from defaults.

______________________________________________________________________

# Class `list`

Built-in mutable sequence.

If no argument is given, the constructor creates a new empty list. The argument must be an iterable if specified.

______________________________________________________________________

# Class `Secret`

This class should be used to receive secrets.

The way to use it is by declaring a variable with the 'Secret' type in the @action.

**Example:**

```
from sema4ai.actions import action, Secret

@action
def my_action(password: Secret):
    login(password.value)
```

Note: this class is abstract and is not meant to be instanced by clients. An instance can be created from one of the factory methods (`model_validate`or `from_action_context`).

## Properties

- `value`

## Methods

______________________________________________________________________

### `from_action_context`

Creates a secret given the action context (which may be encrypted in memory until the actual secret value is requested).

**Args:**

- <b>`action_context`</b>:  The action context which has the secret.

- <b>`path`</b>:  The path inside of the action context for the secret datarequested (Example: 'secrets/my_secret_name').

Return: A Secret instance collected from the passed action context.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_secret/__init__.py#L78)

```python
from_action_context(action_context: 'ActionContext', path: str) → Secret
```

______________________________________________________________________

### `model_validate`

Creates a secret given a string (expected when the user is passing the arguments using a json input).

**Args:**

- <b>`value`</b>:  The raw-text value to be used in the secret.

Return: A Secret instance with the given value.

Note: the model_validate method is used for compatibility with the pydantic API.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_secret/__init__.py#L60)

```python
model_validate(value: str) → Secret
```

______________________________________________________________________

# Class `Table`

Table is a simple data structure that represents a table with columns and rows.

It's meant to be used to represent the result of a table-like operation.

### `__init__`

**Args:**

- <b>`columns`</b>:  The columns of the table.
- <b>`rows`</b>:  The rows of the table.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_table.py#L19)

```python
__init__(columns: list[str], rows: list[list[str | int | float | bool | None]])
```

## Properties

- `model_extra`

Get extra fields set during validation.

**Returns:**
A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`.

- `model_fields_set`

Returns the set of fields that have been explicitly set on this model instance.

**Returns:**
A set of strings representing the fields that have been set, i.e. that were not filled from defaults.

## Methods

______________________________________________________________________

### `get_row_as_dict`

Get a row from the table as a dictionary.

**Args:**

- <b>`index`</b>:  The index of the row to get.

**Returns:**
The row at the given index as a dictionary.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_table.py#L82)

```python
get_row_as_dict(index: int) → dict[str, str | int | float | bool | None]
```

______________________________________________________________________

### `iter_as_dicts`

Iterate over the rows of the table as dictionaries.

**Returns:**
An iterator over the rows of the table as dictionaries.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/_table.py#L51)

```python
iter_as_dicts() → Iterator[dict[str, str | int | float | bool | None]]
```

# Exceptions

______________________________________________________________________

## `ActionError`

This is a custom error which actions returning a `Response` are expected to raise if an "expected" exception happens.

When this exception is raised sema4ai-actions will automatically convert it to an "expected" where its error message is the exception.

i.e.: sema4ai-actions does something as:

```python
try
    ...
except ActionError as e:
    return Response(error=e.message)
```

# Enums

______________________________________________________________________

## `Status`

Action state

### Values

- **NOT_RUN** = NOT_RUN
- **PASS** = PASS
- **FAIL** = FAIL
