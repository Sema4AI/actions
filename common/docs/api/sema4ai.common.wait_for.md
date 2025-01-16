<!-- markdownlint-disable -->

# module `sema4ai.common.wait_for`

# Variables

- **DEFAULT_TIMEOUT**

# Functions

______________________________________________________________________

## `wait_for_condition`

Note: wait_for_non_error_condition or wait_for_expected_func_return are usually a better APIs to use as the error message is automatically built.

**Args:**

- <b>`condition`</b>: A function that returns True or False.
- <b>`msg`</b>: A message to be displayed if the condition is not met.
- <b>`timeout`</b>: The maximum time to wait for the condition to be met.
- <b>`sleep`</b>: The time to sleep between each check.

**Example:**
wait_for_condition(lambda: x == 1, msg="X did not become 1", timeout=10, sleep=1/20.0)

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/wait_for.py#L4)

```python
wait_for_condition(condition, msg=None, timeout=10, sleep=0.05)
```

______________________________________________________________________

## `wait_for_non_error_condition`

**Args:**

- <b>`generate_error_or_none`</b>: A function that returns an error message or None.
- <b>`timeout`</b>: The maximum time to wait for the condition to be met.
- <b>`sleep`</b>: The time to sleep between each check.

**Example:**
def generate_error_or_none():return "X is not 1" if x != 1 else Nonewait_for_non_error_condition(generate_error_or_none, timeout=10, sleep=1/20.0)

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/wait_for.py#L38)

```python
wait_for_non_error_condition(generate_error_or_none, timeout=10, sleep=0.05)
```

______________________________________________________________________

## `wait_for_expected_func_return`

**Args:**

- <b>`func`</b>: A function that returns a value.
- <b>`expected_return`</b>: The expected return value.
- <b>`timeout`</b>: The maximum time to wait for the condition to be met.
- <b>`sleep`</b>: The time to sleep between each check.

**Example:**
wait_for_expected_func_return(lambda: x, 1, timeout=10, sleep=1/20.0)

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/wait_for.py#L72)

```python
wait_for_expected_func_return(func, expected_return, timeout=10, sleep=0.05)
```
