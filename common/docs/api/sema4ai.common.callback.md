<!-- markdownlint-disable -->

# module `sema4ai.common.callback`

# Functions

______________________________________________________________________

# Class `Callback`

A helper class to register callbacks and call them when notified.

**Example:**
with callback.register(lambda x: print(x)):...callback(1) # Will call all callbacks registered passing 1 as argument.

Note that it's thread safe to register/unregister callbacks while callbacks are being notified, but it's not thread-safe to register/unregister at the same time in multiple threads.

### `__init__`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/callback.py#L31)

```python
__init__(reversed=False, raise_exceptions=False)
```

## Methods

______________________________________________________________________

### `register`

Register a callback to be called when the callback is notified.

**Returns:**
An OnExitContextManager which can be used as a context manager to automatically unregister the callback when the context manager is exited.

**Example:**
with callback.register(lambda: print("Hello, world!")):...callback() # Will call all callbacks registered.

Note: it's not thread safe to register/unregister callbacks in multiple threads (a callback may end up not being registered if that's the case).

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/callback.py#L36)

```python
register(callback) → OnExitContextManager
```

______________________________________________________________________

### `unregister`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/callback.py#L59)

```python
unregister(callback) → None
```
