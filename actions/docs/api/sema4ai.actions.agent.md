<!-- markdownlint-disable -->

# module `sema4ai.actions.agent`

# Variables

- **AnyPlatformParameters**

# Functions

______________________________________________________________________

## `get_thread_id`

Get the thread ID from the action context or the request headers.

**Note:**

> This will raise an ActionError if the thread ID cannot be found. This is expected when calling this function directly from VSCode unless the `x-invoked_for_thread_id` header is set in the request in configured inputs.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L202)

```python
get_thread_id() → str
```

______________________________________________________________________

## `get_agent_id`

Get the agent ID from the action context or the request headers.

**Note:**

> This will raise an ActionError if the agent ID cannot be found. This is expected when calling this function directly from VSCode unless the `x-invoked_by_assistant_id` header is set in the request in configured inputs.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L213)

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
- <b>`model_name`</b>: The model name to use for the prompt (optional).

**Note:**

> Either platform_config, thread_id or agent_id must be provided when calling this method without action context. The platform_config will be automatically obtained from the agent which is related to the thread_id or agent_id.

**Returns:**
JSON representation of the response from the agent.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L224)

```python
prompt_generate(
    prompt: Prompt | dict,
    platform_config: OpenAIPlatformParameters | BedrockPlatformParameters | CortexPlatformParameters | AzureOpenAIPlatformParameters | GooglePlatformParameters | GroqPlatformParameters | ReductoPlatformParameters | dict | None = None,
    thread_id: str | None = None,
    agent_id: str | None = None,
    model_name: str | None = None
) → ResponseMessage
```

______________________________________________________________________

## `list_data_frames`

List all data frames available in the current thread.

**Returns:**
List of DataFrameInfo objects containing:
\- name: str - Name of the dataframe
\- description: str | None - Description of the dataframe
\- num_rows: int - Number of rows
\- num_columns: int - Number of columns
\- column_headers: list[str] - List of column names

**Raises:**

- <b>`ActionError`</b>: If called outside of an action context or if unable to fetch dataframes.

**Note:**

> This function requires the agent-server to support the dataframes API endpoint. If the endpoint is not available, this will raise an ActionError.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L279)

```python
list_data_frames() → list[DataFrameInfo]
```

______________________________________________________________________

## `get_data_frame`

Get a data frame by name from the current thread.

**Args:**

- <b>`name`</b>: Name of the data frame to retrieve
- <b>`limit`</b>: Maximum number of rows to fetch (default: 1000). For very large dataframes, consider using SQL to filter data before fetching.
- <b>`offset`</b>: Number of rows to skip from the beginning (default: 0). Useful for pagination when combined with limit.
- <b>`column_names`</b>: List of specific column names to retrieve. If not provided, all columns are returned.
- <b>`order_by`</b>: Column name to sort by.

**Returns:**
Table object with the data frame contents, including:
\- columns: list[str]
\- rows: list[list]
\- name: str | None
\- description: str | None

**Raises:**

- <b>`ActionError`</b>: If called outside of an action context or if unable to fetch data frame.

**Note:**

> This function requires the agent-server to support the dataframes API endpoint. If the endpoint is not available, this will raise an ActionError.

[**Link to source**](https://github.com/sema4ai/actions/tree/master/actions/src/sema4ai/actions/agent/__init__.py#L314)

```python
get_data_frame(
    name: str,
    limit: int = 1000,
    offset: int = 0,
    column_names: list[str] | None = None,
    order_by: str | None = None
) → Table
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

# Class `ResponseAudioContent`

Represents audio content generated or referenced in a model's response.

This class handles audio content in various formats (URL, base64), supporting common audio formats like WAV and MP3. It provides validation for the audio data and ensures proper format handling.

______________________________________________________________________

# Class `ResponseDocumentContent`

Represents a document generated or referenced in a model's response.

This class handles document content in various formats (URL, base64, raw bytes), supporting a wide range of document types including PDFs, text files, spreadsheets, and word processing documents. It provides validation and format handling for document data.

______________________________________________________________________

# Class `ResponseImageContent`

Represents an image generated or referenced in a model's response.

This class handles image content in various formats (URL, base64, raw bytes), with support for different resolutions and image formats. It provides validation and conversion utilities for working with image data.

______________________________________________________________________

# Class `ResponseMessage`

A response message from a language model hosted on a platform.

This class represents a response message from a language model, providing a structured format for both content and metadata. It supports multi-modal content (text, images, audio, documents) and includes standardized fields for model metrics and usage data.

______________________________________________________________________

# Class `ResponseTextContent`

Represents a text segment in a model's response.

This class handles plain text content from the model's response, ensuring that the text is non-empty and properly typed.

______________________________________________________________________

# Class `ResponseToolUseContent`

Represents a tool use request generated by the model.

This class handles tool usage requests from the model, normalizing input formats from different LLM providers (e.g., OpenAI, Claude) into a consistent structure. It provides validation and parsing of tool inputs while maintaining provider-specific compatibility.

**Raises:**
json.JSONDecodeError: If tool_input_raw is a string and cannot be parsed as valid JSON.

- <b>`AssertionError`</b>: If kind field doesn't match the literal "tool_use".

______________________________________________________________________

# Class `TokenUsage`

Represents token usage statistics from a model's response.

This class provides a structured format for tracking token consumption, including input, output, and total tokens used in a model interaction.

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
