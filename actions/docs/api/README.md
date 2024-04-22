<!-- markdownlint-disable -->

# API Overview

## Modules

- [`sema4ai.actions`](./sema4ai.actions.md#module-sema4aiactions): Sema4AI Actions enables running your AI actions in the Sema4AI Action Server.
- [`sema4ai.actions.cli`](./sema4ai.actions.cli.md#module-sema4aiactionscli)

## Classes

- [`_protocols.IAction`](./sema4ai.actions._protocols.md#class-iaction)
- [`_request.Request`](./sema4ai.actions._request.md#class-request): Contains the information exposed in a request (such as headers and cookies).
- [`_secret.Secret`](./sema4ai.actions._secret.md#class-secret): This class should be used to receive secrets.
- [`_protocols.Status`](./sema4ai.actions._protocols.md#class-status): Action state

## Functions

- [`actions.action`](./sema4ai.actions.md#function-action): Decorator for actions (entry points) which can be executed by `sema4ai.actions`.
- [`actions.action_cache`](./sema4ai.actions.md#function-action_cache): Provides decorator which caches return and clears it automatically when the
- [`actions.get_current_action`](./sema4ai.actions.md#function-get_current_action): Provides the action which is being currently run or None if not currently
- [`actions.get_output_dir`](./sema4ai.actions.md#function-get_output_dir): Provide the output directory being used for the run or None if there's no
- [`actions.session_cache`](./sema4ai.actions.md#function-session_cache): Provides decorator which caches return and clears automatically when all
- [`_fixtures.setup`](./sema4ai.actions._fixtures.md#function-setup): Run code before any actions start, or before each separate action.
- [`_fixtures.teardown`](./sema4ai.actions._fixtures.md#function-teardown): Run code after actions have been run, or after each separate action.
- [`cli.main`](./sema4ai.actions.cli.md#function-main): Entry point for running actions from sema4ai-actions.
