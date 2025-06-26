<!-- markdownlint-disable -->

# API Overview

## Modules

- [`sema4ai.actions`](./sema4ai.actions.md#module-sema4aiactions): Sema4.ai Actions enables running your AI actions in the Sema4.ai Action Server.
- [`sema4ai.actions.agent`](./sema4ai.actions.agent.md#module-sema4aiactionsagent)
- [`sema4ai.actions.api`](./sema4ai.actions.api.md#module-sema4aiactionsapi): This module contains the public API for the actions.
- [`sema4ai.actions.chat`](./sema4ai.actions.chat.md#module-sema4aiactionschat)
- [`sema4ai.actions.cli`](./sema4ai.actions.cli.md#module-sema4aiactionscli)

## Classes

- [`_response.ActionError`](./sema4ai.actions._response.md#class-actionerror): This is a custom error which actions returning a `Response` are expected
- [`_protocols.IAction`](./sema4ai.actions._protocols.md#class-iaction)
- [`_secret.OAuth2Secret`](./sema4ai.actions._secret.md#class-oauth2secret): This class should be used to specify that OAuth2 secrets should be received.
- [`_request.Request`](./sema4ai.actions._request.md#class-request): Contains the information exposed in a request (such as headers and cookies).
- [`_response.Response`](./sema4ai.actions._response.md#class-response): The response class provides a way for the user to signal that the action
- [`builtins.list`](./builtins.md#class-list): Built-in mutable sequence.
- [`_secret.Secret`](./sema4ai.actions._secret.md#class-secret): This class should be used to receive secrets.
- [`_protocols.Status`](./sema4ai.actions._protocols.md#class-status): Action state
- [`_table.Table`](./sema4ai.actions._table.md#class-table): Table is a simple data structure that represents a table with columns and rows.
- [`agent.Agent`](./sema4ai.actions.agent.md#class-agent)
- [`_client.AgentApiClientException`](./sema4ai.actions.agent._client.md#class-agentapiclientexception): Exception raised when the Agent API client encounters an error.
- [`agent.Conversation`](./sema4ai.actions.agent.md#class-conversation)
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
- [`agent.create_conversation`](./sema4ai.actions.agent.md#function-create_conversation): Creates a new conversation for communication with an agent.
- [`agent.get_agent_by_name`](./sema4ai.actions.agent.md#function-get_agent_by_name): Fetches the agent that matches the name.
- [`agent.get_all_agents`](./sema4ai.actions.agent.md#function-get_all_agents): Fetches a list of all available agents with their IDs and names.
- [`agent.get_conversation`](./sema4ai.actions.agent.md#function-get_conversation): Fetches the conversation with the given name for an agent.
- [`agent.get_conversation_messages`](./sema4ai.actions.agent.md#function-get_conversation_messages): Fetches all messages from a specific conversation.
- [`agent.get_conversations`](./sema4ai.actions.agent.md#function-get_conversations): Fetches all conversations for an agent.
- [`agent.send_message`](./sema4ai.actions.agent.md#function-send_message): Sends a message within a conversation and retrieves the agent's response.
- [`api.collect_lint_errors`](./sema4ai.actions.api.md#function-collect_lint_errors): Provides lint errors from the contents of a file containing the `@action`s.
- [`chat.attach_file`](./sema4ai.actions.chat.md#function-attach_file): Attaches a file to the current chat.
- [`chat.attach_file_content`](./sema4ai.actions.chat.md#function-attach_file_content): Set the content of a file to be used in the current chat.
- [`chat.attach_json`](./sema4ai.actions.chat.md#function-attach_json): Attach a file with JSON content to the current chat.
- [`chat.attach_text`](./sema4ai.actions.chat.md#function-attach_text): Attach a file with text content to the current chat.
- [`chat.get_file`](./sema4ai.actions.chat.md#function-get_file): Get the content of a file in the current action chat, saves it to a temporary file
- [`chat.get_file_content`](./sema4ai.actions.chat.md#function-get_file_content): Get the content of a file in the current action chat.
- [`chat.get_json`](./sema4ai.actions.chat.md#function-get_json): Get the JSON content of a file in the current action chat.
- [`chat.get_text`](./sema4ai.actions.chat.md#function-get_text): Get the text content of a file in the current action chat.
- [`cli.main`](./sema4ai.actions.cli.md#function-main): Entry point for running actions from sema4ai-actions.
