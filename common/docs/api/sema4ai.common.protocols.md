<!-- markdownlint-disable -->

# module `sema4ai.common.protocols`

# Functions

______________________________________________________________________

## `check_implements`

Helper to check if a class implements some protocol.

:important: It must be the last method in a class due to https://github.com/python/mypy/issues/9266

**Example:**

def __typecheckself__(self) -> None: \_: IExpectedProtocol = check_implements(self)

Mypy should complain if `self` is not implementing the IExpectedProtocol.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L8)

```python
check_implements(x: ~T) → ~T
```

______________________________________________________________________

# Class `ActionResult`

### `__init__`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L45)

```python
__init__(success: bool, message: str | None = None, result: Optional[~T] = None)
```

## Methods

______________________________________________________________________

### `as_dict`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L52)

```python
as_dict() → ActionResultDict[~T]
```

______________________________________________________________________

### `make_failure`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L60)

```python
make_failure(message: str) → ActionResult[T]
```

______________________________________________________________________

### `make_success`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L64)

```python
make_success(result: ~T) → ActionResult[T]
```

______________________________________________________________________

# Class `ActionResultDict`

______________________________________________________________________

# Class `ICancelMonitorListener`

______________________________________________________________________

# Class `IMonitor`

## Methods

______________________________________________________________________

### `add_cancel_listener`

Adds a listener that'll be called when the monitor is cancelled.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L88)

```python
add_cancel_listener(listener: ICancelMonitorListener)
```

______________________________________________________________________

### `cancel`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L75)

```python
cancel() → None
```

______________________________________________________________________

### `check_cancelled`

raises CancelledError (from concurrent.futures import CancelledError) if cancelled.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L78)

```python
check_cancelled() → None
```

______________________________________________________________________

### `is_cancelled`

returns True if cancelled, False otherwise.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/protocols.py#L83)

```python
is_cancelled() → bool
```

# Enums

______________________________________________________________________

## `Sentinel`

### Values

- **SENTINEL** = 0
- **USE_DEFAULT_TIMEOUT** = 1
