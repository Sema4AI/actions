# Changelog

## Unreleased

## 2.14.0 - 2025-07-29

- Headers are now properly forwarded for requests using the `mcp` protocol (so, it's possible
  to receive `Secrets` as headers in the request -- also requires `sema4ai.actions` version `1.4.0`).
- Showing `/mcp` endpoint in the output.
- Upgraded to `sema4ai.common` `0.2.0` (to fix issue where `process.kill` would raise an exception on windows).

## 2.13.1 - 2025-07-15

- Fixed issue where `action-server new --force` was not actually accepting the `--force` flag.

## 2.13.0 - 2025-07-11

- `--expose` is working properly again (it broke in `2.11.0`).
- `action-server new` command changes:
  - New flag: `--force` to force the creation of a new project even if the directory already exists and is not empty.
  - The directory is now considered not empty only if it has files that don't match the default exclusion patterns (so, it can be created without the `--force` flag even if directories such as `.git` or `.vscode` exists inside it).

## 2.12.1 - 2025-06-19

- Properly marking `mcp` as a dependency of the Action Server (the PyPi version was failing to start due to the missing dependency).

## 2.12.0 - 2025-06-18

- Changed so that the MCP tools from actions are now called with just the name of the action (instead of `<action-package-name>/<action-name>`).
  - This is a backward incompatible change (but as MCP in 2.11.0 was still provisional, a major version bump won't be done).
- Packages using `sema4ai-mcp` can now be deployed in the Action Server using the MCP protocol (using `@tool`, `@resource` and `@prompt`
  from `sema4ai-mcp`).

## 2.11.0 - 2025-06-05

- The Action Server now supports the MCP protocol (note: current support is provisional and may still change without major version bumps).
  - Registered actions are now available as tools.
    - The tool name is `<action-package-name>/<action-name>`.
  - Both `/mcp` and `/sse` endpoints are available.
    - So, if the Action Server is started at `http://localhost:8000`, the MCP endpoints are available at `http://localhost:8000/mcp` and `http://localhost:8000/sse`.
  - If an `--api-key` is specified, users must a `Bearer <api-key>` Authorization header to access with it.
  - Note: when the `--reload` flag is used, the MCP tools are also properly reloaded.
  - Note: support for tool cancellation with MCP is not there yet.

## 2.10.0 - 2025-05-05

- No longer logging the full action input/output in the `log.debug` logs in the Action Server.
- Added command: `action-server datadir clear-actions` to clear (disable) the actions from the datadir.
- Updated Action Server frontend dependencies versions (to fix CVEs).
- Support opening the url `/runs/<run_id>` to open the run directly in the Action Server UI.
- No longer doing an update check when the `Action Server` is launched.

## 2.9.1 - 2025-05-02

- Update `rcc` to `20.1.1`

## 2.9.0 - 2025-04-09

- Replaced `requests` with `sema4ai-http-helper` for HTTP operations
- Updated all dependencies to their latest versions

## 2.8.3 - 2025-03-28

- Use uv to setup python environment (to get around issue where the python version was built with an old version of sqlite in ubuntu 20.04).
- Using `ubuntu-22.04` as the default ubuntu version in the CI workflows.

## 2.8.2 - 2025-03-26

- Fixed issue downloading RCC on Mac OS on built executable.
- Always use `sqlite_master` instead of `sqlite_schema` (fix issue in Linux where `sqlite_schema` was not available).

## 2.8.1 - 2025-03-25

- PoC: Fixes in sema4ai_http to be able to download on Mac OS with a signed binary (not merged with master, just binary published, no wheels).

## 2.8.0 - 2025-03-24

- Only update assets if the version is a local version (released versions are not overridden).
- Added `--kill-lock-holder` argument to the `action-server start/migrate/import` commands.

## 2.7.0 - 2025-03-23

- Note: incomplete release (had errors in the build pipeline making the release to github actions).
- `Action Server` now requires Python 3.12 or Python 3.13.
  - Updated some dependencies (`jsonschema-specifications`, `aihttp`, `fastapi-slim`, `sema4ai-actions`, `uvicorn`)
- The `go-wrapper` executable now uses a lock before extracting the assets (to avoid issues when running multiple instances in parallel).
- PyInstaller is used instead of PyOxidizer now to build the Python distribution (PyOxidizer is now unsupported and didn't support Python 3.12).
- When the `Action Server` is launched, a `lastLaunchTouch` file is touched (so, it's possible to check the time of the last `Action Server` usage).
- All integration tests are now run against the binary distribution (previously only a smoke test was run).
- Wheels are now available in pypi for mac os arm64 (and mac os x86_64 is now no longer available).

## 2.6.0 - 2025-02-26

- Support `external-endpoints` in `package.yaml` (to allow configuring firewall settings for egress rules).
  - The information in the `package.yaml` is added to the metadata given by the Action Server.
  - The Action Server will now check that the `external-endpoints` are properly configured for the deployed environment.
  - See: [17-external-endpoints.md](./guides/17-external-endpoints.md) for more information.
  - Note: the metadata version is now `4` and includes the `external-endpoints` information.

## 2.5.3 - 2025-02-24

- Improved logging on post run command failure.

## 2.5.2 - 2025-02-10

- Action Server Go Wrapper:
  - Now embeds the assets as a zip file in the binary.
  - The proper download url is shown for mac os arm64 if the current version is not the latest.
  - Updated Go to 1.23.6 (CVE fixes)
- Updated RCC to 19.0.2 (go v1.23.6 CVE fixes)

## 2.5.1 - 2025-01-07

- Action Server is now available in MacOS ARM 64.
- RCC updated to v19.0.1

## 2.5.0 - 2025-01-03

- It's now possible to cancel a run that is still in the `not_run` state (waiting for a process from the process pool).
- Add `cancel` buttons to the UI (in the run history and in the run itself).
- When the Action Server is started, if there were any runs in the `not_run` state or in the `running` state, they'll be marked as cancelled.
- Fixed a deadlock that could happen in a racing condition when creating/releasing a process from the process pool.
- Created API: `/api/runs/{run_id}/fields` which can be used to get just a few specified fields from a run (instead of the whole run model with `/api/runs/{run_id}/`).

## 2.4.0 - 2024-12-30

- Added support for running actions asynchronously.
  - The Run model now has a `request_id` (optional) field which is the id of the request that created this run.
  - It's possible to get the run id from the request id using the `/api/runs/run-id-from-request-id/<request_id>` endpoint.
  - To call an action asynchronously, set the `x-actions-async-timeout` header to the desired timeout (in seconds).
    - When the timeout is reached a response saying that the action will complete asynchronously is returned.
    - The client can later use the run id to query the run status, cancel the run, etc.
  - The client can also set the `x-actions-async-callback` header to the URL to call when the action is finished.
    - The callback URL will receive the result of the action as a json in the body.
    - A header `x-action-server-run-id` will be sent with the ID of the action run.
    - A header `x-actions-request-id` will be sent with the ID of the request.
- Fixed usages of `time.time()` to `time.monotonic()` to measure time when elapsed time is needed
  (to avoid issues with time going backwards).
- Added support for cancelling actions (url: `/api/runs/<run_id>/cancel`).
  - There's a new "status" in the run model (4=cancelled).
  - Existing statuses are now:
    - 0=not run
    - 1=running
    - 2=passed
    - 3=failed
    - 4=cancelled

## 2.3.1 - 2024-12-18

- Error messages produced by the `Action Server` are now properly shown in the `Actions Run History`.
  - i.e.: structure validation failures are now properly shown in the UI.

## 2.3.0 - 2024-11-21

- The `x-action-context` and `x-data-context` information is now expected to be in the body of the request when the `x-action-invocation-context` header is present.

  - This allows passing more information in these contexts as they may become bigger (to avoid hitting the headers size limit).
  - The body format expected in this case is:

    ```json
    {
      "x-action-context": "data-envelope",
      "x-data-context": "data-envelope",
      "body": {
        "input-value": "value"
      }
    }
    ```

    - The `x-action-invocation-context` header is expected to be a data envelope too.
    - Note: The data envelope format is the same used for secrets (either a `base64(encrypted_data(JSON.stringify(content)))` or a `base64(JSON.stringify(content))`).

## 2.2.0 - 2024-11-20

- Add `x-operation-kind` to the OpenAPI schema.

## 2.1.0 - 2024-11-19

- The `action-server metadata` command now provides a `data` field in the metadata containing the `datasources` collected
  from data packages.

## 2.0.0 - 2024-10-24

- `RCC` is now updated to `v18.3.0`.
- Changes in `package.yaml`:
  - `dev-dependencies` can now be used to install dependencies in a development environment.
  - `dev-tasks` can be used to run tasks in the development environment.
  - `pythonpath` can now be used to specify the directories which should be added to the pythonpath.
    - Note: this is a **backward incompatible** change as old versions of the action server will not
      be able to understand the new `pythonpath` field, thus, action packages making use of it
      will not work with older versions of the `Action Server`.

See: https://github.com/Sema4AI/actions/blob/master/action_server/docs/guides/14-dev-tasks.md for more information on how to use dev-tasks.

## 1.1.2 - 2024-10-17

- Fix the high security issues in backend and frontend

## 1.1.1 - 2024-10-07

- Make sure that temporary session data acquired for OAuth2 authentication is deleted after use.
- When json output is written, utf-8 is used (regular prints still use the default
  Python heuristic, which can use `PYTHONIOENCODING` to override the locale encoding if needed).

## 1.1.0 - 2024-10-02

- Now it's possible to use any variable from the `invocation_context` in the post run command (they'll also be available as environment variables in the format `SEMA4AI_ACTION_SERVER_POST_RUN_<VARIABLE_NAME>`).

## 1.0.1 - 2024-09-26

- Add more debug logging related to post run commands.
- Fixed issue where running an action would fail when passing an action context (just reproducible when using the binary build).

## 1.0.0 - 2024-09-25

- The command specified in `SEMA4AI_ACTION_SERVER_POST_RUN_CMD` can now use the following variables:

  - `$action_name`
  - `$workroom_base_url` (optional)
  - `$agent_id` (optional)
  - `$invoked_on_behalf_of_user_id` (optional)
  - `$thread_id` (optional)
  - `$tenant_id` (optional)

- The variables are now also available as environment variables in the command executed in the format of `SEMA4AI_ACTION_SERVER_POST_RUN_<VARIABLE_NAME>`.

- Marking as `1.0.0` as the `Action Server` is now considered stable and ready for production use.

## 0.23.2 - 2024-09-08

- Fixed issue where OAuth2 token was being renewed when no `refresh_token` was available.

## 0.23.1 - 2024-09-08

- Fixed issue on auto-shutdown when specified `--parent-pid` dies (did not work if `robocorp.log` was not in the environment and it was not release dependency).

## 0.23.0 - 2024-09-06

- Add support for authenticating OAuth2 flow with pkce (without clientSecret).
- Using new format for OAuth2.
  - File path being used changed from `oauth2-settings.yaml` to `oauth2_config.yaml`.
  - The structure of the file changed (there's now support for )

## 0.22.0 - 2024-09-05

- Rename constant to be `SEMA4AI_ACTION_SERVER_POST_RUN_CMD`.

## 0.21.0 - 2024-09-05

- In the `Action Server`, it's possible to customize a command to be invoked right after
  an action is run by setting the `S4_ACTION_SERVER_POST_RUN_CMD` environment variable.
  See [13-post-run-script.md](./guides/13-post-run-script.md) for details.

## 0.20.0 - 2024-08-30

- RCC is now used to calculate hash from `package.yaml` (which is used as the space name)
  - Uses: `rcc ht hash package.yaml --silent --no-temp-management --warranty-voided --bundled`
- If the `SEMA4AI_OPTIMIZE_FOR_CONTAINER=1` environment variable is set:
  - `--liveonly` is passed as a flag to `rcc` when building the environment.
- `SEMA4AI_OPTIMIZE_FOR_CONTAINER=1` or `SEMA4AI_SKIP_UPDATE_CHECK=1` may be used for the go wrapper to skip its version check.
- Removed support for (long deprecated) actions with a `conda.yaml` or `action-server.yaml`.

## 0.19.0 - 2024-08-28

- Add top level command: `oauth2`, providing OAuth2 related utilities
- Add `sema4ai-config` subcommand for `oauth2`
  - Returns OAuth2 configuration for Sema4.ai provided OAuth2 applications
- Add `user-config-path` subcommand for `oauth2`
  - Returns the path to user's local OAuth config file (note: it changed from `oauth2-settings.yaml` to `oauth2_config.yaml`)
  - `--json` argument can be provided to get the result in JSON format

## 0.18.0 - 2024-08-27

- Add to the package metadata an `action_package_version` field and rename `version` to `metadata_version`.

## 0.17.0 - 2024-08-14

- New `--auto-reload` parameter available in `action-server start`.
  - When passed, whenever a file with a `.py`, `.pyx` or `.yaml` extension under an Action
    Package directory is changed, the Action Server will automatically reload the actions
    loaded.
- The Action Server UI will now detect when:
  - The Action Server backend becomes unreachable (i.e.: UI indication that the network is down or it was stopped).
  - The Action Server is restarted with a different `--expose` flag (i.e.: the proper state is now shown).
  - The Actions available in the Action Server change (i.e.: shows the new contents of the action after a reload).
  - The connected Action Server version changes (i.e.: requires a browser page reload).
- Action Server will now use `%LOCALAPPDATA%/sema4ai` (Windows) and `~/.sema4ai` (Linux/Mac) as default directories for RCC data and settings.

## 0.16.1 - 2024-07-11

- Upgrade to MacOS runner 13 as 11 is now deprecated in GitHub actions.

## 0.16.0 - 2024-07-10

- OAuth2 is now defined in the server side and not in the client side.
  - The OAuth2 settings are now defined in a `.yaml`.
    - On Windows it's default location is `%LOCALAPPDATA%/sema4ai/action-server/oauth2-settings.yaml`.
    - On Linux/Mac it's default location is `~/.sema4ai/action-server/oauth2-settings.yaml`.
- Note: this was a partial release because Mac OS 11 is deprecated in GitHub actions.

## 0.15.2 - 2024-06-25

- Fixed issue where metadata was not created in package zip when `--input-dir` was provided.
- Now signed as `Sema4.ai`.

## 0.15.1 - 2024-06-21

- Fixed issue where OAuth2 settings would not be loaded properly from the Action Server UI.

## 0.15.0 - 2024-06-21

- The `cwd` is now always reset whenever an action is run (so, changes to the `cwd`
  will not affect a new action run).
- Use RCC network profile when doing requests
- If the python executable for an environment is no longer available, the environment
  is properly recreated when the action server is started.
- `OAuth2` authentication is now available in the action server UI.
  - Note: if a given provider only accepts `https` as a redirect uri (such as `Slack`), then the action server must be started with `--https`.
- `--https` can now be used when starting the `Action Server` to serve using `ssl`, either using a self-signed certificate or a custom certificate.
- To use a self-signed certificate, `--https --ssl-self-signed` is required (it'll generate a self-signed certificate and use it).
  - Note: when using a self-signed certificate you may need to manually add an exception in the browser or import the self-signed certificate into the system.
- To use a custom certificate `--https --ssl-keyfile <path> --ssl-certfile <path>` needs to be used.

## 0.14.0 - 2024-06-11

- Add package build argument `--input-dir` to choose the action package source directory
- Package build command to print package path to stdout in json format if `--json` argument is provided
- Encrypt-at-rest sensitive storage data to the file system instead of using keyring to store it

## 0.13.0 - 2024-06-10

- A new argument: `--parent-pid` can be passed to the action server. When passed,
  the action server will automatically exit when the given parent pid is no longer
  alive (it's meant to be used when the action server is embedded into another app).
- Standardized the lock file to always start with `PID: {os.getpid()}\n`.
- Accept `datetime.datetime` objects in pydantic models:
  - `mode="json"` used in `model_dump`
  - Using `jsonschema` to validate schema instead of `fastjsonschema` (because it didn't deal with dates properly).

## 0.12.1 - 2024-05-31

- Fix issue where keyring backend was not loaded properly with Windows and MacOS

## 0.12.0 - 2024-05-29

- Add new command: cloud
  - Subcommand: login
    - Save the Control Room login information to keyring, the access credentials and the hostname
  - Subcommand: verify-login
    - Verify if the user credentials have been saved to the keyring
  - Subcommand: list-organizations
    - List all available organization with given access credentials
- Add new package subcommand
  - publish, publish action package to Control Room
    - Intended for human user to handle the whole publish pipeline
  - Subcommands intended for CI users that handles the publish pipeline without interaction:
    - push, upload the action package to Control Room
    - status, query the action package publish status
    - set-changelog, update the action package changelog to Control Room
- `sema4ai.link` is now used on `--expose`

## 0.11.0 - 2024-05-23

- Improved support for exceptions raised in `@action`s from `sema4ai-actions`.
- Note: `sema4ai-actions 0.8.0` added `ActionError` and `Response` classes
  to the public API for improved handling of error conditions.
- See: [Structuring actions guide](./guides/09-structuring-actions.md) for more information.
- `list-templates` subcommand is now available for the `new` command, allowing to get the list of available Action templates
  - subcommand can be used with `--json` flag, which will format the output as JSON
- In the builtin view, added a link to see logs from a run where the run is done.

## 0.10.0 - 2024-05-20

- A `version` is now available in the metadata to signal the current version of the metadata format.
- `openapi.json` (also provided in the metadata): now has an `info/version` field with the version of the `Action Server` (previously it was always `0.1.0`).
- The `action-server package metadata` now has an `--output-file` parameter which allows writing to a file.
- In the `action-server package build`, a file named `__action_server_metadata__.json` is added to the root of the `.zip` with the metadata contents.
- `new` command allows to choose a template from a predefined list now. Command will list available templates,
  and prompt user to choose one.
  - `--template` argument has been added, allowing to specify a concrete template when running the command (when specified,
    user won't be prompted to choose a template from the list).
  - Note: this is a **backward incompatible** change (clients using `action-server new --name <name>` must upgrade
    to pass a template name, otherwise the command will appear to be stuck and will not create anything while waiting for
    an input).

## 0.9.1 - 2024-05-17

- Accept passing `OAuth2 secrets` (as a dict with the required keys) in the `/api/secrets`.

## 0.9.0 - 2024-05-16

- The default datadirs will now be created in `~/.sema4ai/action-server`
  or `LOCALAPPDATA/sema4ai/action-server` instead of `~/robocorp/.action_server`
  or `LOCALAPPDATA/robocorp/action_server`.
  Note that this is a **backward incompatible** change. Users can move the contents
  of the old dir to the new dir to keep existing information (a warning is shown
  from the action server notifying users about it if the old directory exists).
- The `SEMA4AI_HOME` environment variable can now be used to set a different home
  folder to store the `action-server` information (default datadirs).
- OAuth2 Secrets can now be passed to the action server

  - **Important**: Requires `sema4ai-actions 0.6.0` onwards to work.
  - Secrets are received as parameters in an `@action`.
  - The metadata generated by `action-server package metadata` now includes information on OAuth2 secrets required.
  - OAuth2 secrets can be sent the same way that regular secrets are sent, with the only difference
    that instead of having a payload where the value is a string, the payload is a dict with the following
    keys: `"provider", "scopes", "access_token", "metadata"`.
  - Example showing an `@action` requiring an OAuth2 secret:

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

  - See the secrets guide for more information.

## 0.8.1 - 2024-05-09

- Action package names are now properly validated when setting secrets through `/api/secrets`.

## 0.8.0 - 2024-05-08

- Secret information is now available in the package metadata.
  - **Important**: requires `sema4ai-actions 0.5.0`
  - Note: this is a **backward-incompatible** change in `sema4ai-actions 0.5.0` as secrets are now required to be documented.
- Fixed brew reference to `sema4ai/tools/action-server` in conda wrapper.
- The internal database (which keeps information on the runs, etc) is now auto-migrated, so, the
  separate `migrate` command does not need to be manually called.
  - Note: The action server will now check the internal database version and if it's newer than
    the current expected version it'll notify the user and abort the startup.

## 0.7.0 - 2024-05-06

- A new API (`/api/secrets`) is now available to set secrets in memory which will later
  be passed on to actions when they're run (those are later passed using the `x-action-context`
  -- it's meant to be used in cases where a process is managing the action server but is
  not intercepting requests to set the `x-action-context` as would be needed to set the secrets).
  - Note: a new call for a given action package will override previous secrets given for the
    same action package.

## 0.6.0 - 2024-05-02

- It's possible to use `@action(display_name="<Action name>")` to specify a different
  summary in the openapi.json (the default is using the action signature name
  replacing '\_' by spaces and making it a title).
  - Note: require `sema4ai-actions 0.4.0`.
- Error message is properly shown when trying to bind the action server to a port
  which is already being used.
- Actions from action packages that are no longer available are disabled when actions
  are synchronized.
- The `ROBOCORP_HOME` is no longer set to be inside of the datadir (users can set
  the home using the environment variable when needed).
- Passing `--no-retry-build` to RCC when building the environment.
- RCC updated to `v17.28.4`.
- Created command: `action-server env clean-tools-caches`.
- `.pyc` files are now written (passing `--no-pyc-management` to RCC).
- The environment is built only once and is no longer checked/made pristine
  whenever the action server is started.

## 0.5.3 - 2024-04-24

- Properly work with `uv` (to use add `uv=<version>` in the `conda-forge` section).

## 0.5.2 - 2024-04-24

- The `version` field in the `package.yaml` is no longer required nor used
  (when uploading an action package a version will be automatically given).

## 0.5.1 - 2024-04-24

- Fixed issue in Windows binary build signing.

## 0.5.0 - 2024-04-23

- Branding change: `Robocorp Action Server` is now `Sema4.ai Action Server`.
- `robocorp-actions` is now deprecated and `sema4ai.actions` should
  be used instead (temporarily `robocorp-actions` is still accepted, but
  it'll be deprecated soon).
- `auth-tag` is now properly used in the `X-Action-Context`, but
  `sema4ai-actions=0.3.1` is required in the environment.

## 0.4.1 - 2024-04-17

- `auth-tag` can be passed/used in the `X-Action-Context` header when encoding using `aes256-gcm` encryption.
  - Note: requires `robocorp-actions=0.2.1`
  - Note: actually has an issue (auth-tag still not properly supported).

## 0.4.0 - 2024-04-16

- Using `Ctrl+C` to stop action server should no longer show a traceback.
- Return package name in package metadata.
- Return package description in package metadata.
- RCC updated to `v17.23.2`.
- RCC `--bundled` flag now passed when called from the action server.
- When the help is shown the action server version is shown in the description.
- (Backward-Incompatibility) The label referencing the encryption algorithm for the context is now properly specified as `aes256-gcm`.
- Note: New migration required with data related to required secrets (`action-server migrate` needs to be manually called).
- Action Server Builtin UI:
  - Fix issue where the label for some entry would not be shown in the run. [#370](https://github.com/robocorp/robocorp/issues/370)
  - Show ` (item)` when editing an item from a list.
  - Required secrets are now properly shown in the UI (so, it's possible to pass secrets from the Builtin UI).

## 0.3.2 - 2024-04-12

- Fixed issue where auto-update message could break commands which wrote to stdout (such as version or package metadata).

## 0.3.1 - 2024-04-11

- Fixes in the builtin UI:
  - There's a JSON toggle so that the data can be sent as JSON.
  - Objects can now be properly edited.
  - Entering a float or int now works properly.

## 0.3.0 - 2024-04-10

- `action-server package metadata` now includes information on the secrets required
  for each action.
- Passing secrets now works (requires `robocorp-actions=0.2.0`)
  - Note: the builtin UI still has no support for passing secrets.

## 0.2.1 - 2024-04-04

- `action-server package build` no longer includes the `.zip` being created in the
  `.zip` itself if it's created in the current directory.
- `action-server package extract` uses the current dir by default as a target for
  extraction.
- A traceback is no longer shown if the user does `Ctrl+C` when waiting for the
  user input on whether to override or not files in the related
  `action-server package` commands.
- Fixed issue where items could be overridden in the `action-server package` commands
  even if the user answered `n` to the prompt.

## 0.2.0 - 2024-04-03

- Update package's main README.
- Improved handling of websockets when used from the builtin UI (not the `--expose` one).
  - Fixed issue where the number of runs shown in the UI would not match the
    actual number of runs (i.e.: updated data was not collected on websocket
    reconnection).
- Fixed issue where `"sqlite3.OperationalError: database is locked"` could be raised
  when executing multiple actions in parallel.
- In `action-server start --expose`, if an action run starts and the connection
  is broken and a new websocket connection is created to the tunnel, the results
  of the action run are sent to the new websocket.
- Added support for `action-server package build` to create a .zip file with the
  package contents (excluding contents based on the `package.yaml` `packaging/exclude`
  session).
- Added support for `action-server package extract` to extract the contents of the
  package created with `action-server package build`.
- Added support for `action-server package metadata` to extract metadata from the
  action package (in the current directory). Currently outputs to stdout
  a json containing a map from `openapi.json` to its contents.
- Backward-incompatibility: `action-server package update` needs to be used
  instead of `action-server package --update`.
- Add support parsing Array type in Action Server UI action run view

## 0.1.4 - 2024-03-20

- Fixed issue in action-server binary build.

## 0.1.3 - 2024-03-20

- Fixed issue in action-server binary build.

## 0.1.2 - 2024-03-20

- `action-server start --expose` now accepts concurrent requests.
- `x-openai-isConsequential: false` is now properly set again for `@action(is_consequential=False)`.

## 0.1.1 - 2024-03-15

- Fixed issue running `action-server start --expose`.

## 0.1.0 - 2024-03-15

- Support parsing Custom Types in Action Server UI action run view
- Add Console output to Action Server UI action run view
- Add Public URL link to Action Server UI if Action Server is started with `--expose`
- When used with `robocorp-actions 0.1.0`, the `headers` can now be gotten in the `request`.
- Action server's public URL no longer changes on reconnection (with `--expose`).

## 0.0.28 - 2024-03-11

- `pydantic` models are accepted as the input and output of `@action`s.

- The action package name is now gotten from the `package.yaml` and not from the directory name
  (it's still gotten from the directory name when `conda.yaml` is used for backward compatibility).
- The action package name and action name are slugified to be ascii only and replace
  unwanted chars for `-` in the urls.
- A `--whitelist` argument is accepted in the command line for `start` and `import` and
  it allows whitelisting action package names as well as action names.

## 0.0.27 - 2024-03-04

- Same as 0.0.26, but had issues publishing the actual binary.

## 0.0.26 - 2024-03-01

- Worked around bug in which `import numpy` halts if `sys.stdin` is being read when it's imported.

## 0.0.25 - 2024-02-29

- `action-server package --update` properly adds the 'name' to the package.yaml

## 0.0.24 - 2024-02-23

- Properly use all lines from docstring description to feed to the `openapi.json`.
- When creating project from template, skip the root directory in the .zip.

## 0.0.23 - 2024-02-23

- Support for Action Packages with `package.yaml`.
  - `conda.yaml` or `action-server.yaml` support is deprecated (but still supported).
  - `action-server package --update` may be used to migrate an existing package.
- When starting up, if a running server is detected the newly spawned server will wait a bit
  for the old one to exit before finishing with an error.

# 0.0.22 - 2024-02-23

- Same as 0.0.23, but had issues publishing the actual binary.

# 0.0.21 - 2024-02-23

- Same as 0.0.23, but had issues publishing the actual binary.

## 0.0.20 - 2024-01-31

- When importing actions, lint them by default (`--skip-lint` may be used
  to disable linting).
  - `robocorp-actions 0.0.7` is now required.

## 0.0.19 - 2024-01-24

- Instead of defining a `conda.yaml` it's expected that an `action-server.yaml` is defined
  (at this point it's expected that it has the same contents as the `conda.yaml`).

## 0.0.18 - 2024-01-19

- The response from a run now includes an `"X-Action-Server-Run-Id"` header containing the run id.
  - This makes it possible to query more information from `api/runs/{run_id}` after the run finishes.
- Fixed issue where `@action` code would not have logging in place.

## 0.0.17 - 2024-01-19

- By default the minimum number of processes is now 2.
- Console/log output improved.
- Full traceback no longer shown if `robocorp-actions` version does not match the one expected.
- Verify that the `robocorp-actions` version found is 0.0.6 or higher.
  - Required for fixes running `@action` multiple times in the same process.

## 0.0.16 - 2024-01-18

- If a process crashes while in the process pool idle processes it's not reused in a new run.
- When reusing processes, `@setup(scope="session")` is only called once and `@teardown(scope="session")` is no longer called.
  - Requires `robocorp-actions 0.0.6`.
  - Also fixes issue where files containing `@action` would be reimported on each new run when process is reused.

## 0.0.15 - 2024-01-16

- The `--api-key` is now checked in any calls, not just on the connection relative to the `--expose`.
- The Run UI now has a field to specify the `--api-key` to be used in a run.
- Console startup message showing url for action server UI is improved.

## 0.0.14 - 2024-01-16

- It's now possible to specify the server url using the `--server-url` command line parameter.
- A process pool is now available in the action server. The following new arguments are available:
  `--min-processes=<n-processes>`
  `--max-processes=<n-processes>`
  `--reuse-process`
- If the return of an `@action` does not conform to the proper return type a better error message is given.
- Improved keepalive/reconnection on the `--expose` tunnel (ping-pong messages).

## 0.0.13 - 2024-01-14

- Fix main README and update docs.

## 0.0.12 - 2024-01-12

- Auto-trigger brew pipeline after build.

## 0.0.11 - 2024-01-10

- Fixed issue where the actions wouldn't be shown in the UI if the `@action` didn't have any required arguments.

## 0.0.10 - 2024-01-09

- Arguments are passed to the `@action` using `--json-input` command line argument (requires `robocorp-actions 0.0.4`).
  Fixes issue where having long arguments could make the action invocation fail.

## 0.0.9 - 2024-01-08

- Fixed build issue (`rcc` should not be bundled in source release).

## 0.0.8 - 2024-01-08

- Properly depend on node 20.x when doing build.
- Trying to fix build issue (`rcc` should not be bundled in source release).

## 0.0.7 - 2024-01-08

- Make sure that `rcc` is not bundled when doing the source dist (otherwise the linux binary could be wrongly used in mac).
- UI revamp for the action server.
- When an action has default values it can be properly run without passing those as arguments.
- Updated template to start action server project.

## 0.0.6 - 2024-01-05

- `rcc` is now bundled in the action server wheel.
- When the action server is stopped, any subprocess is also killed.
- Pass `@action(is_consequential=True)` to add `x-openai-isConsequential` option to action openapi spec.
- Can be started with `--expose-allow-reuse` to reuse the previously exposed url.

## 0.0.5 - 2023-12-14

- Fixed issues in deployment:
  - `requests` is now a required dep (for --expose to work).
  - \_static_contents now properly added by poetry (because it was in .gitignore it was not added to the distribution).
  - "new" command properly checks that RCC is downloaded.
- Running an action with multiple `_` now works from the UI.

## 0.0.4 - 2023-12-13

- `action-server` is not defined as an entry point (so, after installing it,
  an `action-server` executable will be available to execute it instead of having
  to use `python -m robocorp-action-server`).
- Instead of just a text showing the trace header a hyperlink to the trace is also available.
- It's possible to bootstrap a project with `action-server new`.
- Improvements when exposing a server with `--expose`:
  - It's now possible to reuse a previously exposed session with `--expose-session`
  - An API key may be used with `--api-key` for authentication (`--api-key=None` can
    be used to disable authentication).
- By default, when the action server is started with `action-server start`, the
  current directory will be searched for actions and only those actions will be
  served (metadata will be stored in a datadir linked to the current folder).
- For more advanced cases, it's still possible to import actions specifying a
  custom datadir and then start the action server with `--actions-sync=false`
  specifying the proper datadir).

i.e.:

```
action-server import --dir=c:/temp=action-package1 --datadir=c:/temp/datadir
action-server import --dir=c:/temp=action-package2 --datadir=c:/temp/datadir
action-server start --actions-sync=false --datadir=c:/temp/datadir
```

## 0.0.3 - 2023-12-08

- UI now uses websockets to provide updates on runs in real-time.
- The static assets are bundled into the application so that the distributed version has access to it.
- It's possible to `--expose` the server on the public web using a 'sema4ai.link'.
- A text showing the trace header is now available in the logs.
- Other UI improvements.

## 0.0.2 - 2023-12-05

- Still pre-alpha.
- Internal DB migration available.
- Initial UI available.
  - Allows running from the UI.
  - Shows action packages, actions and runs.
  - The console and log.html can be seen.
  - API to expose the server to the web.
  - Known issue: requests for runs and actions are cached and a full page request is needed to get new information.

## 0.0.1 - 2023-11-29

- First release (pre-alpha).
- Can import actions in the backend and run using API
