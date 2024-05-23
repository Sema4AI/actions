<!-- markdownlint-disable -->

# API Overview

## Modules

- [`sema4ai.actions`](./sema4ai.actions.md#module-sema4aiactions): Sema4.ai Actions enables running your AI actions in the Sema4.ai Action Server.
- [`sema4ai.actions.api`](./sema4ai.actions.api.md#module-sema4aiactionsapi): This module contains the public API for the actions.
- [`sema4ai.actions.cli`](./sema4ai.actions.cli.md#module-sema4aiactionscli)

## Classes

- [`_response.ActionError`](./sema4ai.actions._response.md#class-actionerror): This is a custom error which actions returning a `Response` are expected
- [`_protocols.IAction`](./sema4ai.actions._protocols.md#class-iaction)
- [`_secret.OAuth2Secret`](./sema4ai.actions._secret.md#class-oauth2secret): This class should be used to specify that OAuth2 secrets should be received.
- [`_request.Request`](./sema4ai.actions._request.md#class-request): Contains the information exposed in a request (such as headers and cookies).
- [`_response.Response`](./sema4ai.actions._response.md#class-response): The response class provides a way for the user to signal that the action
- [`_secret.Secret`](./sema4ai.actions._secret.md#class-secret): This class should be used to receive secrets.
- [`_protocols.Status`](./sema4ai.actions._protocols.md#class-status): Action state
- [`api.DiagnosticsTypedDict`](./sema4ai.actions.api.md#class-diagnosticstypeddict)
- [`api.PositionTypedDict`](./sema4ai.actions.api.md#class-positiontypeddict)
- [`api.RangeTypedDict`](./sema4ai.actions.api.md#class-rangetypeddict)

## Functions

- [`actions.action`](./sema4ai.actions.md#function-action): Decorator for actions (entry points) which can be executed by `sema4ai.actions`.
- [`actions.action_cache`](./sema4ai.actions.md#function-action_cache): Provides decorator which caches return and clears it automatically when the
- [`actions.get_current_action`](./sema4ai.actions.md#function-get_current_action): Provides the action which is being currently run or None if not currently
- [`actions.get_output_dir`](./sema4ai.actions.md#function-get_output_dir): Provide the output directory being used for the run or None if there's no
- [`actions.session_cache`](./sema4ai.actions.md#function-session_cache): Provides decorator which caches return and clears automatically when all
- [`_fixtures.setup`](./sema4ai.actions._fixtures.md#function-setup): Run code before any actions start, or before each separate action.
- [`_fixtures.teardown`](./sema4ai.actions._fixtures.md#function-teardown): Run code after actions have been run, or after each separate action.
- [`api.collect_lint_errors`](./sema4ai.actions.api.md#function-collect_lint_errors): Provides lint errors from the contents of a file containing the `@action`s.
- [`cli.main`](./sema4ai.actions.cli.md#function-main): Entry point for running actions from sema4ai-actions.
