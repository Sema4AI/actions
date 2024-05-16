# Changelog

## Unreleased

- The default datadirs will now be created in `~/.sema4ai/action-server`
  or `LOCALAPPDATA/sema4ai/action-server` instead of `~/robocorp/.action_server`
  or `LOCALAPPDATA/robocorp/action_server`.
  Note that this is a _backward incompatible_ change. Users can move the contents
  of the old dir to the new dir to keep existing information (a warning is shown
  from the action server notifying users about it if the old directory exists).
- The `SEMA4AI_HOME` environment variable can now be used to set a different home
  folder to store the `action-server` directory information.
- OAuth2 Secrets can now be passed to the action server (see the secrets guide for more information).

## 0.8.1 - 2024-05-09

- Action package names are now properly validated when setting secrets through `/api/secrets`.

## 0.8.0 - 2024-05-08

- Secret information (with `sema4ai-actions 0.5.0`) is now available in the package metadata.
  - Note: this is a backward-incompatible change in `sema4ai-actions 0.5.0` as secrets are now required to be documented.
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
- It's possible to `--expose` the server on the public web using a 'robocorp.link'.
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
