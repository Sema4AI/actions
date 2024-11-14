# Changelog

## Unreleased

- The `options` of an `Action` now have a `kind` (the default being `action`, but other actions kinds can be set, for instance, `sema4ai-data` will contribute `query` and `predict` kinds).
- The type `Annotated[DataSource, DataSourceSpec(...)]` is now handled as a managed argument.
- New `python -m sema4.actions metadata` command is available and will also include the `metadata` from `sema4ai-data` if it's available as well as the metadata (actions list) from the `actions` found.
- The seach glob to identify modules which should be automatically loaded to find definitions is now `"*action*.py|*query*.py|*queries*.py|*predict*.py|*datasource*.py"` (previously it was `"*action*.py"`)
- Supports receiving an `x-data-context` header to initialize datasources in the `sema4ai-data` library.

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
