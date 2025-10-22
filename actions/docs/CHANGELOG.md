# Changelog

## Unreleased

## 1.6.0 - 2025-10-22

**BREAKING CHANGES:**
- **Table serialization schema change**: The `Table` model now includes `name` and `description` fields in serialized output (model_dump). This is a backward-incompatible change for consumers expecting the old schema. The fields are present as `null` when not set.

**New Features:**
- **Enhanced error handling**: `AgentApiClientException` now exposes `status_code` attribute for robust error checking instead of string matching.
- **Improved type safety**: `agent.list_data_frames()` now returns `list[DataFrameInfo]` instead of `list[dict]` for better type hints and IDE support.
- **Table validation improvement**: All rows are now validated for consistency, not just the first 5 rows. This ensures data integrity with negligible performance impact.
- **Table metadata support**: `Table` now accepts optional `name` and `description` fields for better labeling and documentation of table data.
- **New dataframe API functions**: Added `agent.list_data_frames()` and `agent.get_data_frame()` for programmatic access to thread dataframes. Both functions require an action execution context and are client-side only.

## 1.5.0 - 2025-10-08

- Added `SecretSpec` class for tagging secrets with metadata that can be used by external clients for special handling.
  - `SecretSpec` can be used with `Annotated` to mark secrets with well-known tags that signal to external clients
    that a secret requires special treatment (e.g., as a global setting managed centrally).

## 1.4.3 - 2025-09-24

- Add the ability to use a different llm model when generating prompts

## 1.4.2 - 2025-08-21

- CVE fixes

## 1.4.1 - 2025-08-07

- Extend `psutil` dependency to <8.0 to support latest versions

## 1.4.0 - 2025-07-29

- Secrets may now also be passed as environment variables
  or individually as headers (both in dev or production mode).

  This may be the preferred way when dealing with mcp servers or
  some infrastructure that doesn't have support for customizing
  the `X-Action-Context`.

  The environment variable name is by default the same name of the secret
  in uppercase.

  Example:

  Given the code:

  ```python
  @mcp.tool
  def my_action(my_secret: Secret):
      the_secret_is = my_secret.value
  ```

  A secret may also be passed as an environment variable such as:

  ```
  MY_SECRET=<secret-value>
  ```

  or as a header prefixed by `X-` and replacing `_` by `-` in the variable name
  (in this case it's case insensitive). i.e.:

  ```
  X-My-Secret=<secret-value>
  ```

  The `<secret-value>` may be the plain value of the variable or it
  may also be encrypted with the same logic used to encrypt the
  `X-Action-Context` (the only difference being that the secret
  is a string and not a dictionary/object, but it should still
  be json-dumped/encrypted/put in the json envelope/converted to base64).

## 1.3.15 - 2025-07-24

- Fixed issue where an `@action(is_consequential=False)` wasn't being properly linted due to the decorator being a function call.

## 1.3.14 - 2025-07-07

- Added new `sema4ai.actions.agent` module with agent interaction capabilities:
  - `prompt_generate()`: Send prompts to agents and get responses. Supports both Pydantic models and dictionaries for prompts and platform configurations.
  - `get_thread_id()`: Retrieve the current thread ID from action context or request headers.
  - `get_agent_id()`: Retrieve the current agent ID from action context or request headers.
  - Support for multiple AI platforms including OpenAI, Azure OpenAI, Google, Groq, Bedrock, Cortex, and Reducto.
  - Flexible prompt structure supporting text, image, audio, document, tool use, and tool result content types.
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
  - The namespace changed from `robocorp.actions`
