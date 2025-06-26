<!-- markdownlint-disable -->

# module `sema4ai.actions.agent`

# Functions

______________________________________________________________________

## `create_conversation`

Creates a new conversation for communication with an agent.

**Args:**

- <b>`agent_id`</b>: The id of the agent to create conversation with
- <b>`conversation_name`</b>: The name of the conversation to be created
- <b>`sema4_api_key`</b>: The API key for the Sema4 API if running in cloud. Use LOCAL if in Studio or SDK!

**Returns:**
The created conversation.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L173)

```python
create_conversation(
    agent_id: str,
    conversation_name: str,
    sema4_api_key: str | None = None
) → Conversation
```

______________________________________________________________________

## `get_all_agents`

Fetches a list of all available agents with their IDs and names.

**Args:**

- <b>`sema4_api_key`</b>: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

**Returns:**
The list of all agents.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L64)

```python
get_all_agents(sema4_api_key: str | None = None) → list[Agent]
```

______________________________________________________________________

## `get_agent_by_name`

Fetches the agent that matches the name.

**Args:**

- <b>`name`</b>: The name of the agent
- <b>`sema4_api_key`</b>: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

**Returns:**
The agent that matches the given name.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L79)

```python
get_agent_by_name(name: str, sema4_api_key: str | None = None) → Agent | None
```

______________________________________________________________________

## `get_conversations`

Fetches all conversations for an agent.

**Args:**

- <b>`agent_id`</b>: The ID of the agent
- <b>`sema4_api_key`</b>: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

**Returns:**
The list of conversations for the agent.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L97)

```python
get_conversations(
    agent_id: str,
    sema4_api_key: str | None = None
) → list[Conversation]
```

______________________________________________________________________

## `get_conversation`

Fetches the conversation with the given name for an agent.

**Args:**

- <b>`agent_name`</b>: The name of the agent
- <b>`conversation_name`</b>: The name of the conversation
- <b>`sema4_api_key`</b>: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

**Returns:**
The conversation with the given name.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L118)

```python
get_conversation(
    agent_name: str,
    conversation_name: str,
    sema4_api_key: str | None = None
) → Conversation | None
```

______________________________________________________________________

## `get_conversation_messages`

Fetches all messages from a specific conversation.

**Args:**

- <b>`agent_id`</b>: The ID of the agent
- <b>`conversation_id`</b>: The ID of the conversation
- <b>`sema4_api_key`</b>: The API key for the Sema4 API if running in cloud. Use LOCAL if in Studio or SDK!

**Returns:**
The list of messages in the conversation.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L151)

```python
get_conversation_messages(
    agent_id: str,
    conversation_id: str,
    sema4_api_key: str | None = None
) → list[dict]
```

______________________________________________________________________

## `send_message`

Sends a message within a conversation and retrieves the agent's response.

**Args:**

- <b>`conversation_id`</b>: The ID of the conversation
- <b>`agent_id`</b>: The ID of the agent to send message to
- <b>`message`</b>: The message content to send
- <b>`sema4_api_key`</b>: The API key for the Sema4 API if running in cloud. Use LOCAL if in Studio or SDK!

**Returns:**
Response containing either the agent's response or an error message

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L202)

```python
send_message(
    conversation_id: str,
    agent_id: str,
    message: str,
    sema4_api_key: str | None = None
) → str
```

______________________________________________________________________

# Class `Agent`

## Properties

- `model_extra`

Get extra fields set during validation.

**Returns:**
A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`.

- `model_fields_set`

Returns the set of fields that have been explicitly set on this model instance.

**Returns:**
A set of strings representing the fields that have been set, i.e. that were not filled from defaults.

______________________________________________________________________

# Class `Conversation`

## Properties

- `model_extra`

Get extra fields set during validation.

**Returns:**
A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`.

- `model_fields_set`

Returns the set of fields that have been explicitly set on this model instance.

**Returns:**
A set of strings representing the fields that have been set, i.e. that were not filled from defaults.

# Exceptions

______________________________________________________________________

## `AgentApiClientException`

Exception raised when the Agent API client encounters an error.
