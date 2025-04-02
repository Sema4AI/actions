<!-- markdownlint-disable -->

# module `sema4ai.actions.cli`

# Functions

______________________________________________________________________

## `main`

Entry point for running actions from sema4ai-actions.

**Args:**

- <b>`args`</b>:  The command line arguments.

- <b>`exit`</b>:  Determines if the process should exit right after executing the command.

- <b>`plugin_manager`</b>:  Provides a way to customize internal functionality (should not be used by external clients in general).

**Returns:**
The exit code for the process.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/cli.py#L32)

```python
main(
    args=None,
    exit: bool = True,
    plugin_manager: Optional[ForwardRef('_PluginManager')] = None
) → int
```
