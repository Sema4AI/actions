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
- [`_secret.SecretSpec`](./sema4ai.actions._secret.md#class-secretspec): Metadata for secrets that specifies a tag for identification by external clients.
- [`_protocols.Status`](./sema4ai.actions._protocols.md#class-status): Action state
- [`_table.Table`](./sema4ai.actions._table.md#class-table): Table is a simple data structure that represents a table with columns and rows.
- [`_platforms.AzureOpenAIPlatformParameters`](./sema4ai.actions.agent._platforms.md#class-azureopenaiplatformparameters): Parameters for the Azure OpenAI platform.
- [`_platforms.BedrockPlatformParameters`](./sema4ai.actions.agent._platforms.md#class-bedrockplatformparameters): Parameters for the Bedrock platform.
- [`_models.ConversationHistoryParams`](./sema4ai.actions.agent._models.md#class-conversationhistoryparams): Parameters for the conversation history special message.
- [`_models.ConversationHistorySpecialMessage`](./sema4ai.actions.agent._models.md#class-conversationhistoryspecialmessage): Special message for including the conversation history in a prompt.
- [`_platforms.CortexPlatformParameters`](./sema4ai.actions.agent._platforms.md#class-cortexplatformparameters): Parameters for the Snowflake Cortex platform.
- [`_models.DocumentsParams`](./sema4ai.actions.agent._models.md#class-documentsparams): Parameters for the documents special message.
- [`_models.DocumentsSpecialMessage`](./sema4ai.actions.agent._models.md#class-documentsspecialmessage): Special message for including the documents in a prompt.
- [`_platforms.GooglePlatformParameters`](./sema4ai.actions.agent._platforms.md#class-googleplatformparameters): Parameters for the Google platform.
- [`_platforms.GroqPlatformParameters`](./sema4ai.actions.agent._platforms.md#class-groqplatformparameters): Parameters for the Groq platform.
- [`_models.MemoriesParams`](./sema4ai.actions.agent._models.md#class-memoriesparams): Parameters for the memories special message.
- [`_models.MemoriesSpecialMessage`](./sema4ai.actions.agent._models.md#class-memoriesspecialmessage): Special message for including the memories in a prompt.
- [`_platforms.OpenAIPlatformParameters`](./sema4ai.actions.agent._platforms.md#class-openaiplatformparameters): Parameters for the OpenAI platform.
- [`_models.Prompt`](./sema4ai.actions.agent._models.md#class-prompt): Represents a complete prompt for an AI model interaction.
- [`_models.PromptAgentMessage`](./sema4ai.actions.agent._models.md#class-promptagentmessage): Represents an agent message in the prompt.
- [`_models.PromptAudioContent`](./sema4ai.actions.agent._models.md#class-promptaudiocontent): Represents an audio message in the agent system.
- [`_models.PromptDocumentContent`](./sema4ai.actions.agent._models.md#class-promptdocumentcontent): Represents a document message in the agent system.
- [`_models.PromptImageContent`](./sema4ai.actions.agent._models.md#class-promptimagecontent): Represents an image message in the agent system.
- [`_models.PromptTextContent`](./sema4ai.actions.agent._models.md#class-prompttextcontent): Represents a text message in the agent system.
- [`_models.PromptToolResultContent`](./sema4ai.actions.agent._models.md#class-prompttoolresultcontent): Represents the result of a tool execution in the agent system.
- [`_models.PromptToolUseContent`](./sema4ai.actions.agent._models.md#class-prompttoolusecontent): Represents a message containing a tool use request from an AI agent.
- [`_models.PromptUserMessage`](./sema4ai.actions.agent._models.md#class-promptusermessage): Represents a user message in the prompt.
- [`_platforms.ReductoPlatformParameters`](./sema4ai.actions.agent._platforms.md#class-reductoplatformparameters): Parameters for the Reducto platform.
- [`_response.ResponseAudioContent`](./sema4ai.actions.agent._response.md#class-responseaudiocontent): Represents audio content generated or referenced in a model's response.
- [`_response.ResponseDocumentContent`](./sema4ai.actions.agent._response.md#class-responsedocumentcontent): Represents a document generated or referenced in a model's response.
- [`_response.ResponseImageContent`](./sema4ai.actions.agent._response.md#class-responseimagecontent): Represents an image generated or referenced in a model's response.
- [`_response.ResponseMessage`](./sema4ai.actions.agent._response.md#class-responsemessage): A response message from a language model hosted on a platform.
- [`_response.ResponseTextContent`](./sema4ai.actions.agent._response.md#class-responsetextcontent): Represents a text segment in a model's response.
- [`_response.ResponseToolUseContent`](./sema4ai.actions.agent._response.md#class-responsetoolusecontent): Represents a tool use request generated by the model.
- [`_response.TokenUsage`](./sema4ai.actions.agent._response.md#class-tokenusage): Represents token usage statistics from a model's response.
- [`_models.ToolDefinition`](./sema4ai.actions.agent._models.md#class-tooldefinition): Represents the definition of a tool.
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
- [`agent.get_agent_id`](./sema4ai.actions.agent.md#function-get_agent_id): Get the agent ID from the action context or the request headers.
- [`agent.get_thread_id`](./sema4ai.actions.agent.md#function-get_thread_id): Get the thread ID from the action context or the request headers.
- [`agent.prompt_generate`](./sema4ai.actions.agent.md#function-prompt_generate): Gives a prompt to an agent.
- [`api.collect_lint_errors`](./sema4ai.actions.api.md#function-collect_lint_errors): Provides lint errors from the contents of a file containing the `@action`s.
- [`chat.attach_file`](./sema4ai.actions.chat.md#function-attach_file): Attaches a file to the current chat.
- [`chat.attach_file_content`](./sema4ai.actions.chat.md#function-attach_file_content): Set the content of a file to be used in the current chat.
- [`chat.attach_json`](./sema4ai.actions.chat.md#function-attach_json): Attach a file with JSON content to the current chat.
- [`chat.attach_text`](./sema4ai.actions.chat.md#function-attach_text): Attach a file with text content to the current chat.
- [`chat.get_file`](./sema4ai.actions.chat.md#function-get_file): Get the content of a file in the current action chat, saves it to a temporary file
- [`chat.get_file_content`](./sema4ai.actions.chat.md#function-get_file_content): Get the content of a file in the current action chat.
- [`chat.get_json`](./sema4ai.actions.chat.md#function-get_json): Get the JSON content of a file in the current action chat.
- [`chat.get_text`](./sema4ai.actions.chat.md#function-get_text): Get the text content of a file in the current action chat.
- [`chat.list_files`](./sema4ai.actions.chat.md#function-list_files): Lists all files in the current chat thread.
- [`cli.main`](./sema4ai.actions.cli.md#function-main): Entry point for running actions from sema4ai-actions.
