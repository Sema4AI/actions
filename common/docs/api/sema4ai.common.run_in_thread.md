<!-- markdownlint-disable -->

# module `sema4ai.common.run_in_thread`

# Functions

______________________________________________________________________

## `run_in_thread`

Runs a given target in a thread returning a Future which can be used to track its result.

**Args:**

- <b>`target`</b>: The target to run in a thread. Will be called with no arguments.
- <b>`kwargs`</b>: Additional arguments to pass to the thread creation function.

**Returns:**
A Future which can be used to track the result of the thread.

**Example:**
future = run_in_thread(lambda: 1 + 1, daemon=True)result = future.result()print(result)

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/run_in_thread.py#L8)

```python
run_in_thread(target: Callable[[], ~T], **kwargs) → Future[~T]
```

______________________________________________________________________

## `run_in_thread_asyncio`

Runs a given target in a thread returning an asyncio Future which can be awaited in an asyncio loop.

**Args:**

- <b>`target`</b>: The target to run in a thread. Will be called with no arguments.
- <b>`kwargs`</b>: Additional arguments to pass to the thread creation function.

**Returns:**
An asyncio Future which can be awaited in an asyncio loop.

**Example:**
future = run_in_thread_asyncio(lambda: 1 + 1)result = await futureprint(result)

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/run_in_thread.py#L44)

```python
run_in_thread_asyncio(target: Callable[[], ~T], **kwargs) → Future[~T]
```
