<!-- markdownlint-disable -->

# module `sema4ai.common.system_mutex`

To use, create a SystemMutex, check if it was acquired (get_mutex_aquired()) and if acquired the mutex is kept until the instance is collected or release_mutex is called.

I.e.:

mutex = SystemMutex('my_unique_name')if mutex.get_mutex_aquired():print('acquired')else:print('not acquired')

Or to keep trying to get the mutex until a given timeout elapses:

with timed_acquire_mutex('mutex_name'):# Do something without any racing condition with other processes...

License: Dual-licensed under LGPL and Apache 2.0

Copyright: Brainwy Software Author: Fabio Zadrozny

# Functions

______________________________________________________________________

## `timed_acquire_mutex`

Acquires the mutex given its name, a number of attempts and a time to sleep between each attempt.

:throws RuntimeError if it was not possible to get the mutex in the given time.

To be used as:

with timed_acquire_mutex('mutex_name'): # Do something without any racing condition with other processes...

:param check_reentrant: Should only be False if this mutex is expected to be released ina different thread.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/system_mutex.py#L340)

```python
timed_acquire_mutex(
    mutex_name,
    timeout=20,
    sleep_time=0.15,
    check_reentrant=True,
    base_dir=None,
    raise_error_on_timeout=False
) → ContextManager
```

______________________________________________________________________

# Class `SystemMutex`

### `__init__`

:param check_reentrant: Should only be False if this mutex is expected to be released ina different thread.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/system_mutex.py#L231)

```python
__init__(mutex_name, check_reentrant=True, log_info=False, base_dir=None)
```

## Properties

- `disposed`

## Methods

______________________________________________________________________

### `get_mutex_aquired`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/system_mutex.py#L319)

```python
get_mutex_aquired()
```

______________________________________________________________________

### `release_mutex`

[**Link to source**](https://github.com/sema4ai/actions/tree/master/common/src/sema4ai/common/system_mutex.py#L322)

```python
release_mutex()
```
