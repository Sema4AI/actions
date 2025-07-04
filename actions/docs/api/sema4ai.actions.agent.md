<!-- markdownlint-disable -->

# module `sema4ai.actions.agent`

# Variables

- **AnyPlatformParameters**

# Functions

______________________________________________________________________

## `get_thread_id`

Get the thread ID from the action context or the request headers.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L117)

```python
get_thread_id() → str
```

______________________________________________________________________

## `get_agent_id`

Get the agent ID from the action context or the request headers.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L122)

```python
get_agent_id() → str
```

______________________________________________________________________

## `prompt_generate`

Gives a prompt to an agent.

**Args:**

- <b>`prompt`</b>: The prompt to generate.
- <b>`platform_config`</b>: The platform configuration if method is called without action context (optional).
- <b>`thread_id`</b>: The thread ID to use for the prompt (optional).
- <b>`agent_id`</b>: The agent ID to use for the prompt (optional).

**Note:**

> Either platform_config, thread_id or agent_id must be provided when calling this method without action context.

**Returns:**
JSON representation of the response from the agent.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/sema4ai/actions/agent/prompt_generate#L127)

```python
prompt_generate(
    prompt: Prompt,
    platform_config: Optional[Annotated[Union[BedrockPlatformParameters, CortexPlatformParameters, OpenAIPlatformParameters, AzureOpenAIPlatformParameters, GooglePlatformParameters, GroqPlatformParameters, ReductoPlatformParameters], FieldInfo(annotation=NoneType, required=True, discriminator='kind')]] = None,
    thread_id: str | None = None,
    agent_id: str | None = None
)
```

______________________________________________________________________

# Class `AzureOpenAIPlatformParameters`

Parameters for the Azure OpenAI platform.

This class encapsulates all configuration parameters for Azure OpenAI client initialization.

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

# Class `BedrockPlatformParameters`

Parameters for the Bedrock platform.

This class encapsulates all configuration parameters for AWS Bedrock client initialization. It supports both direct client parameters and advanced configuration via the botocore Config object.

Direct Parameters: region_name: The AWS region to use (e.g., 'us-west-2', 'us-east-1').If not specified, boto3 will use the default region from AWS configuration.api_version: The API version to use. Generally should be left asNone to use the latest.use_ssl: Whether to use SSL when communicating with AWS (True by default).verify: Whether to verify SSL certificates. Can be True/False or pathto a CA bundle.endpoint_url: Alternative endpoint URL (e.g., for VPC endpoints or testing).Format: 'https://bedrock.us-east-1.amazonaws.com'aws_access_key_id: AWS access key. If not provided, boto3 will use theAWS configuration chain (environment, credentials file, IAM role).aws_secret_access_key: AWS secret key. Required if aws_access_key_idis provided.aws_session_token: Temporary session token for STS credentials.

Advanced Configuration: config_params: Used to instantiate a botocore.config.Config object foradvanced settings. Common options include:
\- retries: Dict controlling retry behavior (e.g., {'max_attempts': 3})
\- connect_timeout: Connection timeout in seconds
\- read_timeout: Read timeout in seconds
\- max_pool_connections: Max connections to keep in connection pool
\- proxies: Dict of proxy servers to use
\- proxies_config: Proxy configuration including CA bundles
\- user_agent: Custom user agent string
\- user_agent_extra: Additional user agent string
\- tcp_keepalive: Whether to use TCP keepalive
\- client_cert: Path to client-side certificate for TLS auth
\- inject_host_prefix: Whether to inject host prefix into endpoint

**Examples:**
Basic usage with region:

```python
params = BedrockPlatformParameters(region_name='us-east-1')
```

Using custom endpoint and credentials:

```python
params = BedrockPlatformParameters(
    endpoint_url='https://bedrock.custom.endpoint',
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET'
)
```

Advanced configuration with retries and timeouts:

```python
params = BedrockPlatformParameters(
    region_name='us-east-1',
    retries={'max_attempts': 3},
    config_params={'connect_timeout': 5, 'read_timeout': 60}
)
```

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

# Class `ConversationHistoryParams`

Parameters for the conversation history special message.

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

# Class `ConversationHistorySpecialMessage`

Special message for including the conversation history in a prompt.

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

# Class `CortexPlatformParameters`

Parameters for the Snowflake Cortex platform.

This class encapsulates all configuration parameters for Snowflake Cortex client initialization.

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

# Class `DocumentsParams`

Parameters for the documents special message.

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

# Class `DocumentsSpecialMessage`

Special message for including the documents in a prompt.

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

# Class `GooglePlatformParameters`

Parameters for the Google platform.

This class encapsulates all configuration parameters for Google client initialization.

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

# Class `GroqPlatformParameters`

Parameters for the Groq platform.

This class encapsulates all configuration parameters for Groq client initialization.

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

# Class `MemoriesParams`

Parameters for the memories special message.

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

# Class `MemoriesSpecialMessage`

Special message for including the memories in a prompt.

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

# Class `OpenAIPlatformParameters`

Parameters for the OpenAI platform.

This class encapsulates all configuration parameters for OpenAI client initialization.

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

# Class `Prompt`

Represents a complete prompt for an AI model interaction.

This class encapsulates all components needed for an AI interaction, including the system instruction, temperature setting, and the conversation history. The conversation history must follow a strict user-agent interleaving pattern (starting with a user message, then alternating between groups of user and agent messages).

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

# Class `PromptAgentMessage`

Represents an agent message in the prompt.

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

# Class `PromptAudioContent`

Represents an audio message in the agent system.

This class handles audio content in base64 format, supporting common audio formats like WAV and MP3.

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

# Class `PromptDocumentContent`

Represents a document message in the agent system.

This class handles document content in either URL or base64 format, with support for different resolutions and image formats.

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

# Class `PromptImageContent`

Represents an image message in the agent system.

This class handles image content in either URL or base64 format, with support for different resolutions and image formats.

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

# Class `PromptTextContent`

Represents a text message in the agent system.

This class handles plain text content, ensuring that the text is non-empty and properly typed.

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

# Class `PromptToolResultContent`

Represents the result of a tool execution in the agent system.

This class encapsulates the output from a tool execution, which can include text and image content, along with status information about the execution.

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

# Class `PromptToolUseContent`

Represents a message containing a tool use request from an AI agent.

This class handles tool usage requests from different LLM providers (OpenAI, Claude), normalizing their different input formats into a consistent structure.

**Raises:**
json.JSONDecodeError: If tool_input_raw is a string and cannot be parsed as valid JSON.

- <b>`AssertionError`</b>: If type field doesn't match the literal "tool_use".

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

# Class `PromptUserMessage`

Represents a user message in the prompt.

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

# Class `ReductoPlatformParameters`

Parameters for the Reducto platform.

This class encapsulates all configuration parameters for Reducto client initialization.

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

# Class `ToolDefinition`

Represents the definition of a tool.

## Properties

- `model_extra`

Get extra fields set during validation.

**Returns:**
A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`.

- `model_fields_set`

Returns the set of fields that have been explicitly set on this model instance.

**Returns:**
A set of strings representing the fields that have been set, i.e. that were not filled from defaults.
