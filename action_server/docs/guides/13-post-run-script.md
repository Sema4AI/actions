# Post run scripts

In the `Action Server`, it's possible to customize a command to be invoked right after
an action is run by setting the `S4_ACTION_SERVER_POST_RUN_CMD` environment variable.

The command set is by default parsed using `shlex.split` (https://docs.python.org/3/library/shlex.html#shlex.split)
and then a substitution is done per-argument to make a replacement of some variables using the rules from `string.Template` (`https://docs.python.org/3/library/string.html#string.Template`) -- i.e.: variables are expected to be in the format `$name`.

The available variables are:

- `$base_artifacts_dir`
- `$run_artifacts_dir`
- `$run_id`

### Note

The command will be run directly in the `Action Server`, not in the context of the action. As such,
the command line executed should not rely on anything related to the action (it's possible that
not even `python` is available as it'll just use whathever environment is used to start
the `Action Server`, so, if some utility is needed, make sure it's already in the `PATH` used
to start the `Action Server`).

As it's using `shlex.split`, paths should be passed with `/` and not `\`, even on Windows.
