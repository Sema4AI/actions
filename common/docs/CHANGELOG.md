# Changelog

## Unreleased

## 0.2.2 - 2025-12-17

- CVE fixes

## 0.2.1 - 2025-08-21

- CVE fixes

## 0.2.0 - 2025-07-29

- Use the same code (with psutil) in all platforms for `kill_process_and_subprocesses`.

## 0.1.1 - 2025-06-02

- Fix issue when killing subprocesses on MacOS (apparently in MacOS we could
  end in a state where killing subprocesses could end up killing parent processes --
  i.e.: PyCharm was killed when a subprocess was killed using `kill_process_and_subprocesses`
  -- it's not entirely clear why that happened, but the new code using psutil doesn't
  seem to suffer from the issue, and shouldn't be an issue since we already
  rely on psutil anyways in this library).

## 0.1.0 - 2025-04-01

- Update sema4ai-http-helper to 2.0.0 version

## 0.0.10 - 2025-03-29

- Make msgspec dependency less strict.

## 0.0.9 - 2025-03-13

- Fix critical issue in autoexit.

## 0.0.8 - 2025-03-12

- Make it possible to customize the SystemMutex message saved to the file.
- Create `kill_subprocesses` API.
- Fixed typo on `exit_when_pid_exists` -> `exit_when_pid_exits` (kept API with typo for backward compatibility)
- Created `sema4ai.common.app_mutex.obtain_app_mutex` API to help with logic starting up Application.
- Customize `soft_kill_timeout` in `exit_when_pid_exits` and `kill_subprocesses`.

## 0.0.7 - 2025-03-09

Add utility to automatically exit when another pid exits (`exit_when_pid_exists`).

## 0.0.6 - 2025-03-07

Improve `Process.__str__` and `Process.__repr__`.

## 0.0.5 - 2025-03-07

Improve BaseTool to define target paths for windows and linux too (not just mac os).

## 0.0.4 - 2025-03-06

Added utilities previously used with git subtree (vendored_deps) in action server and vscode extension.

## 0.0.3 - 2025-02-04

Add sema4ai.common.uris module for uri <-> path translations.

## 0.0.2 - 2025-01-25

Add py.typed to the sources.

## 0.0.1 - 2025-01-16

- Initial release
- Utilities for:
  - callbacks
  - process management
  - running callbacks in threads
  - system mutex
  - busy waiting
  - downloading tools
  - null object pattern
