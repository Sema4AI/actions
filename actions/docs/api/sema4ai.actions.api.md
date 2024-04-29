<!-- markdownlint-disable -->

# module `sema4ai.actions.api`

This module contains the public API for the actions.

These should be kept backward compatible (breakage here can still occur, but  it should not be taken lightly).

# Functions

______________________________________________________________________

## `collect_lint_errors`

Provides lint errors from the contents of a file containing the `@action`s.

**Args:**

- <b>`contents_to_lint`</b>:  The contents which should be linted.

**Returns:**
A list with the diagnostics found.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/api.py#L68)

```python
collect_lint_errors(contents_to_lint: str) → list[DiagnosticsTypedDict]
```

______________________________________________________________________

# Class `DiagnosticsTypedDict`

______________________________________________________________________

# Class `PositionTypedDict`

______________________________________________________________________

# Class `RangeTypedDict`
