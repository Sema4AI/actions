# Post run scripts

In the `Action Server`, it's possible to customize a command to be invoked right after
an action is run by setting the `SEMA4AI_ACTION_SERVER_POST_RUN_CMD` environment variable.

The command set is by default parsed using `shlex.split` (https://docs.python.org/3/library/shlex.html#shlex.split)
and then a substitution is done per-argument to make a replacement of some variables using the rules from `string.Template` (`https://docs.python.org/3/library/string.html#string.Template`) -- i.e.: variables are expected to be in the format `$name`.

The available variables are:

- `$base_artifacts_dir`
- `$run_artifacts_dir`
- `$run_id`
- `$action_name`
- `$workroom_base_url` (optional)
- `$agent_id` (optional)
- `$invoked_on_behalf_of_user_id` (optional)
- `$thread_id` (optional)
- `$tenant_id` (optional)

Note: the variables marked as optional may not be present in the substitution (if they are not passed in the 'x-action-context' header).

The same variables are also available as environment variables (with `SEMA4AI_ACTION_SERVER_POST_RUN_` prefix):

- `SEMA4AI_ACTION_SERVER_POST_RUN_BASE_ARTIFACTS_DIR`
- `SEMA4AI_ACTION_SERVER_POST_RUN_RUN_ARTIFACTS_DIR`
- `SEMA4AI_ACTION_SERVER_POST_RUN_RUN_ID`
- `SEMA4AI_ACTION_SERVER_POST_RUN_ACTION_NAME`
- `SEMA4AI_ACTION_SERVER_POST_RUN_WORKROOM_BASE_URL` (optional)
- `SEMA4AI_ACTION_SERVER_POST_RUN_AGENT_ID` (optional)
- `SEMA4AI_ACTION_SERVER_POST_RUN_INVOKED_ON_BEHALF_OF_USER_ID` (optional)
- `SEMA4AI_ACTION_SERVER_POST_RUN_THREAD_ID` (optional)
- `SEMA4AI_ACTION_SERVER_POST_RUN_TENANT_ID` (optional)

### Note

The command will be run directly in the `Action Server`, not in the context of the action. As such,
the command line executed should not rely on anything related to the action (it's possible that
not even `python` is available as it'll just use whatever environment is used to start
the `Action Server`, so, if some utility is needed, make sure it's already in the `PATH` used
to start the `Action Server`).

As it's using `shlex.split`, paths should be passed with `/` and not `\`, even on Windows.
