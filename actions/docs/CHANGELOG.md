# Changelog

## Unreleased

## 1.3.14 - 2025-06-23

- Added the following functions to interact with agents:
  - `get_all_agents()`: Fetch all available agents
  - `get_agent_by_name()`: Find agents by their name
  - `get_conversations()`: Retrieve all conversations for a specific agent
  - `get_conversation()`: Get conversations by agent name and conversation name
  - `get_conversation_messages()`: Fetch all messages from a specific conversation
  - `create_conversation()`: Create new conversations for agent communication
  - `send_message()`: Send messages to agents and receive the response
- The heuristics for finding actions/tools/etc. have been changed (**Backward Incompatible change**).
  - The new heuristics are:
    - Any python file will now be considered for having an action defined in it.
    - Any python file which contains text such as `@action`, `@query`, `@tool`, `@resource`, `@prompt`, `DataSourceSpec` will be loaded for definitions.
    - Directories that are considered to be "python library" directories will be ignored (for instance, `site-packages`, `lib/python`, etc).
    - Directories or files which match the `packaging/exclude` rules from `package.yaml` will be ignored.
  - It's still possible to pass a `--glob` argument, which (if given) will be used as a whitelist to accept a file.
  - **Note**: the previous heuristics was: all folders were checked recursively and for any file which matched `"*action*.py|*query*.py|*queries*.py|*predict*.py|*datasource*.py|*data_source*.py"` was loaded for actions by default.
- No longer calling `truststore.inject_into_ssl()` automatically (`sema4ai-http` should be used instead or clients that need it can do it explicitly) -- **Backward Incompatible change**.

## 1.3.13 - 2025-06-17

- Increased the maximum allowed docstring length from `300` to `1024` characters in the linting rules.
- Internal changes to support the `sema4ai-mcp` library.
- If an `async` method is marked with `@action`, `@tool`, etc, `asyncio.run` will be used to run it instead of failing.
- Updated pydantic dependency from `^2.0` to `^2.11.7`
- Updated templates to the latest library version

## 1.3.12 - 2025-06-16

- Add `list` and `dict` as supported types for `RowValue`.

## 1.3.11 - 2025-04-25

- Expose `sema4ai.actions.chat.get_file` to the public interface.
- Generate appropriate docs for `get_file` and guids for `chat` module.

## 1.3.10 - 2025-04-25

- Added a warning message when using the `@predict` decorator to inform users that it is deprecated.

## 1.3.9 - 2025-04-24

- Allow future 3.x versions of `robocorp-log`.

## 1.3.8 - 2025-04-02

- Update `sema4ai-http-helper` to 2.0.1 version.

## 1.3.7 - 2025-04-02

- Update to latest `sema4ai-http-helper` version.

## 1.3.6 - 2025-03-12

- Pass filename in multipart form data when uploading file.

## 1.3.5 - 2025-02-15

- Fixed error message to show correct url if upload fails.

## 1.3.4 - 2025-02-15

- Passing contents to the presigned post url as a multipart/form-data (as S3 expects).

## 1.3.3 - 2025-01-27

- Passing "x-action-invocation-context" instead of "x-action-context".
- Overwriting file if that's what the agent server requested.

## 1.3.2 - 2025-01-26

- Properly passing "x-action-context" to files chat API.

## 1.3.1 - 2025-01-25

- Improved `sema4ai.actions.chat` to properly get the `thread_id` under different conditions (new versions of ACE and when the
  action server is coupled directly with the agent server).

## 1.3.0 - 2024-12-30

- Improve heuristic for detecting that a parameter is a data source so that docstrings are not required for data source parameters.
- Support for `Union[DataSource, DataSource]` without `typing.Annotated`
  - i.e.: `def my_query(datasource: FilesDataSource | CustomersDataSource)`

## 1.2.0 - 2024-12-18

- Added a `Table` data model.
- It's now possible to use python types such as list/dict directly as action parameters/return type without requiring a pydantic model.
- When linting, if a parameter is a `DataSource` it's not required to have a docstring.
  - Note: as it works just on the AST, it currently just checks if the python name ends with `DataSource` (instead of doing full type inference).
- Verification of the return value is now done after the action is run (and not only in the Action Server) when `--print-result` is passed to `sema4ai.actions`.

## 1.1.4 - 2024-11-26

- Accept `*data_source*.py` and not just `*datasource*.py`.
- Modules are now loaded in a predictable order based on the module path.

## 1.1.3 - 2024-11-25

- Support for `sema4ai-data` `0.0.2`.
- Updated to use `'actions_spec_version': 'v2'` instead of `'actions-spec-version': 'v1'`.

## 1.1.2 - 2024-11-20

- Added linting for `@query` and `@predict` (missing docstring, missing return, etc).

## 1.1.1 - 2024-11-18

- Updates to work with the new `sema4ai-data` library (still provisional).

## 1.1.0 - 2024-11-14

- The `options` of an `Action` now have a `kind` (the default being `action`, but other actions kinds can be set, for instance, `sema4ai-data` will contribute `query` and `predict` kinds).
- The type `Annotated[DataSource, DataSourceSpec(...)]` is now handled as a managed argument.
- New `python -m sema4.actions metadata` command is available and will also include the `metadata` from `sema4ai-data` if it's available as well as the metadata (actions list) from the `actions` found.
- The search glob to identify modules which should be automatically loaded to find definitions is now `"*action*.py|*query*.py|*queries*.py|*predict*.py|*datasource*.py"` (previously it was `"*action*.py"`)
- Supports receiving an `x-data-context` header to initialize datasources in the `sema4ai-data` library.
- New `sema4ai.actions.chat` module which allows attaching files/data to the chat with the current agent.
  - The `SEMA4AI_FILE_MANAGEMENT_URL` environment variable is expected to be set with the URL of the file management service.
    - For local development, it's possible to use the `file://` scheme as the URL to save files in the local file system (which will store files in the given directory).
  - Note: in production it's expected that the `invocation_context` is available in the action context, with details on the current agent/thread id.
  - Note: this is new functionality in the `sema4ai-actions` library, but other components (as Agent Server/Control Room) may still not fully support this feature.
- Note: the `sema4ai-actions` metadata format is still provisional and may change in newer `1.1.x` releases.

## 1.0.1 - 2024-09-26

- When running in frozen mode, `robocorp.log` will no longer be imported when the action context is requested.

## 1.0.0 - 2024-09-25

- Updated required dependencies versions (in particular, cryptography is now "^43").
- Marking as 1.0 to signal that the library is now stable and ready to be used in production.

## 0.10.0 - 2024-06-21

- A model returned with a `pydantic` field with a `validation_alias` will no longer break.
  - `cls.model_json_schema(by_alias=False)` is now used to get the pydantic schema.
- A new `--json-output=<path>` can be used to dump the action result to a file when
  calling the `run` command.
  - Note: the dumped result will be a JSON object with `"result", "message" and "status"`

## 0.9.2 - 2024-06-17

- Accept `datetime.datetime` objects in pydantic models:
  - `mode="json"` used in `model_dump`

## 0.9.1 - 2024-05-29

- The folder containing the `package.yaml` is now always added to the PYTHONPATH (if running without
  a `package.yaml` for tests the `cwd` is considered the root and is added to the PYTHONPATH).

## 0.9.0 - 2024-05-29

- `pydantic` models can now be used as default values in `@action`.
- If there's an error, still print the result if there's a result (which is the case when using `sema4ai.actions.Response`).
- To create an `OAuth2Secret` using the input on VSCode, just the `access_token` suffices now.

## 0.8.0 - 2024-05-23

- API used from pydantic changed (using `model_dump` instead of `model_dump_json`).
- `pydantic v2` (onwards) is now a required dependency of `sema4ai-actions`.
- Improved support for error conditions:
  - A new class is now available in the public API: `sema4ai.actions.ActionError`
    - Raising an error of this type can be used to provide a custom message in case some error happens.
  - If an error of a different type is raised, the error type is now shown
    (without more details on the error to avoid possibly showing private information).
- A new class is now available in the public API: `sema4ai.actions.Response(result, error)` for
  more control over errors shown.
- See: [Structuring actions guide](./guides/09-structuring-actions.md) for more information.
- **Backward incompatible** change: only one action can be run at a time and an error is
  raised if more than one action would be run (the action server would only expect that
  a single action is run at a time and if more than one action would actually be run this
  should be an error).

## 0.7.0 - 2024-05-22

- New command line flag `--print-result` can be used to have the result of an `@action` printed to the terminal.
- New command line flag `--print-input` can be used to have the input of an `@action` printed to the terminal.
- Unsets `ROBOT_ROOT` when running actions so that all non-library code is considered user code when generating logs.
  - Fixes issue where logs were not properly generated when running an action from VSCode.

## 0.6.0 - 2024-05-16

- OAuth2 secrets can now be received in the arguments. Example:

  ```python
  from typing import Literal
  from sema4ai.actions import OAuth2Secret, action

  @action
  def read_spreadsheet(
      name: str,
      google_secret: OAuth2Secret[
          Literal["google"],
          list[
              Literal[
                  "https://www.googleapis.com/auth/spreadsheets.readonly",
                  "https://www.googleapis.com/auth/drive.readonly",
              ]
          ],
      ],
  ) -> str:
      return do_read_spreadsheet(name, google_secret.access_token)
  ```

## 0.5.0 - 2024-05-08

- Backward incompatible change: the argument docstring for secrets is now required
  to be documented in the arguments (and this information is now provided in the
  action server metadata).

## 0.4.0 - 2024-05-02

- A `display_name` may be set in an `@action` to control the summary of the
  action in the openapi.json (the default is the action signature name replacing
  `_` by spaces and making it a title).
- A public API function was added to collect linting errors from a file
  containing `@action`s (`sema4ai.actions.api.collect_lint_errors`).

## 0.3.1 - 2024-04-23

- Fixes `aes256-gcm` to use auth tag properly (instead of associated data).
- The `auth-tag` is always required when encryption is used now.

## 0.3.0 - 2024-04-22

- Branding change: `robocorp-actions` is now `sema4ai-actions`.
  - The namespace changed from `robocorp.actions` to `sema4ai.actions`.
  - The public API remains the same (so, the only change needed should be a rename of `from robocorp.actions import ...` to `from sema4ai.actions import ...`.
  - `robocorp.tasks` is no longer a dependency (rather, the needed code is now incorporated into `sema4ai-actions`).

## 0.2.1 - 2024-04-17

- Accepts `auth-tag` when using `aes256-gcm` for encrypting the `x-action-context` contents
  (previously it'd always be an empty string).

## 0.2.0 - 2024-04-10

- `python -m robocorp.actions list` now has information on the managed parameters
  (`managed_params_schema`, which is a dict from parameter name to parameter
  information is given for each task).
- Parameters in `@action` typed as `robocorp.actions.Secret` will now be considered
  managed parameters (the client must to provide the secret information when
  running the action).
- `X-Action-Context` containing the secrets can be passed (with optional encryption
  using `aes256-gcm`).
- Update **robocorp-tasks** dependency to `3.1.1`.

## 0.1.3 - 2024-04-09

- Update **robocorp-tasks** dependency to `3.0.3`.

## 0.1.2 - 2024-04-08

- Alignment with **robocorp-tasks** `3.0.2`.

## 0.1.1 - 2024-04-08

- Update package's main README.

## 0.1.0 - 2024-03-15

- `request: Request` is now a managed parameter when using `robocorp-actions`. Note
  that by default it'll be empty, but when called from the `Action Server`, it'll
  have `headers` and `cookies` available.

## 0.0.9 - 2024-03-13

- References in the schema are resolved (so, the schema for a field is valid when embedded inside a larger schema).

## 0.0.8 - 2024-03-11

- `pydantic` models are accepted as the input and output of `@action`s.

## 0.0.7 - 2024-01-31

- When actions are imported they're also automatically linted for the following errors:
  - Mising docstrings (error)
  - Mising docstrings docstring (error)
  - Return statement is found (error).
  - Each argument has a description in the docstring (error).
  - Arguments are properly typed (warning).
  - Return is properly typed (warning).
- Files named `*task*.py` are no longer loaded by default in actions.

## 0.0.6 - 2024-01-18

- Provides support for calling `main` multiple times.
  - Modules containing `@action` are no longer reimported anymore.
  - Any `@action` that was already imported is still available for running in a new `main` call.
  - `RC_TASKS_SKIP_SESSION_SETUP` env variable may be used to skip setup of new `@setup`s found.
  - `RC_TASKS_SKIP_SESSION_TEARDOWN` env variable may be used to skip teardon of `@teardown`s found.

## 0.0.5 - 2024-01-14

- Fix main README and update docs.

## 0.0.4 - 2024-01-09

- Arguments to `@action` may be passed in a json file (with `--json-input=<path to .json file>`).
- Requires `robocorp-tasks >= 2.8.0` now.

## 0.0.3 - 2024-01-05

- Pass `@action(is_consequential=True)` to add `x-openai-isConsequential` option to action openapi spec (when used with the action-server).

## 0.0.2 - 2023-12-13

- Properly depend on `robocorp-tasks` version `2.6.0`.

## 0.0.1 - 2023-11-29

It's possible to define an action such as:

```python
from robocorp.actions import action

@action
def convert_to_int(value: str) -> int:
    return int(value)
```

And call it as:

```python
python -m robocorp.action -- --value=2
```
