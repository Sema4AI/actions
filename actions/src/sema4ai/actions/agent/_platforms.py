from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class OpenAIPlatformParameters(BaseModel):
    """Parameters for the OpenAI platform.

    This class encapsulates all configuration parameters for OpenAI client
    initialization.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["openai"] = Field(
        default="openai",
        description="The kind of platform parameters.",
    )

    openai_api_key: str | None = Field(
        default=None,
        description="The OpenAI API key. If not provided, it will be "
        "attempted to be inferred from the environment.",
    )


class BedrockPlatformParameters(BaseModel):
    """Parameters for the Bedrock platform.

    This class encapsulates all configuration parameters for AWS Bedrock
    client initialization. It supports both direct client parameters and
    advanced configuration via the botocore Config object.

    Direct Parameters:
        region_name: The AWS region to use (e.g., 'us-west-2', 'us-east-1').
            If not specified, boto3 will use the default region from AWS configuration.
        api_version: The API version to use. Generally should be left as
            None to use the latest.
        use_ssl: Whether to use SSL when communicating with AWS (True by default).
        verify: Whether to verify SSL certificates. Can be True/False or path
            to a CA bundle.
        endpoint_url: Alternative endpoint URL (e.g., for VPC endpoints or testing).
            Format: 'https://bedrock.us-east-1.amazonaws.com'
        aws_access_key_id: AWS access key. If not provided, boto3 will use the
            AWS configuration chain (environment, credentials file, IAM role).
        aws_secret_access_key: AWS secret key. Required if aws_access_key_id
            is provided.
        aws_session_token: Temporary session token for STS credentials.

    Advanced Configuration:
        config_params: Used to instantiate a botocore.config.Config object for
        advanced settings. Common options include:
            - retries: Dict controlling retry behavior (e.g., {'max_attempts': 3})
            - connect_timeout: Connection timeout in seconds
            - read_timeout: Read timeout in seconds
            - max_pool_connections: Max connections to keep in connection pool
            - proxies: Dict of proxy servers to use
            - proxies_config: Proxy configuration including CA bundles
            - user_agent: Custom user agent string
            - user_agent_extra: Additional user agent string
            - tcp_keepalive: Whether to use TCP keepalive
            - client_cert: Path to client-side certificate for TLS auth
            - inject_host_prefix: Whether to inject host prefix into endpoint

    Examples:
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
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["bedrock"] = Field(
        default="bedrock",
        description="The kind of platform parameters.",
    )

    # Direct client parameters
    region_name: str | None = Field(
        default=None,
        description="AWS region name (e.g., 'us-west-2'). If not specified, "
        "boto3 will use the default region from AWS configuration chain "
        "(environment variables, config file, or instance metadata).",
        json_schema_extra={"example": "us-east-1"},
    )

    api_version: str | None = Field(
        default=None,
        description="API version to use for the AWS service. Generally should "
        "be left as None to use the latest available version. Only set this if "
        "you need a specific API version for compatibility.",
        json_schema_extra={"example": "2023-04-20"},
    )

    use_ssl: bool | None = Field(
        default=None,
        description="Whether to use SSL/TLS when communicating with AWS "
        "(True by default). Setting this to False is not recommended in "
        "production environments.",
        json_schema_extra={"example": True},
    )

    verify: bool | str | None = Field(
        default=None,
        description="Controls SSL certificate verification. Can be:\n"
        "- True: Verify certificates using system CA store (default)\n"
        "- False: Disable verification (not recommended)\n"
        "- str: Path to custom CA bundle file",
        json_schema_extra={"example": "/path/to/custom/ca-bundle.pem"},
    )

    endpoint_url: str | None = Field(
        default=None,
        description="Alternative endpoint URL for the AWS service. Useful for:\n"
        "- VPC endpoints\n"
        "- Testing with local endpoints\n"
        "- Custom service endpoints\n"
        "Format should be a complete URL including scheme (https://)",
        json_schema_extra={"example": "https://bedrock.us-east-1.amazonaws.com"},
    )

    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID for authentication. If not provided, "
        "boto3 will attempt to find credentials in the following order:\n"
        "1. Environment variables\n"
        "2. Shared credential file (~/.aws/credentials)\n"
        "3. IAM role for EC2 instance or ECS task",
        json_schema_extra={"example": "AKIAIOSFODNN7EXAMPLE"},
    )

    aws_secret_access_key: str | None = Field(
        default=None,
        description="AWS secret access key for authentication. Required if "
        "aws_access_key_id is provided. Should be kept secure and not exposed in "
        "code or logs.",
        json_schema_extra={"example": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    )

    aws_session_token: str | None = Field(
        default=None,
        description="Temporary session token for AWS STS (Security Token "
        "Service) credentials. Only required when using temporary credentials "
        "(e.g., from AssumeRole or federated access).",
        json_schema_extra={
            "example": "AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5TthT+..."
        },
    )

    config_params: dict = Field(
        default_factory=dict,
        description="Advanced configuration parameters for botocore Config object.",
    )


class CortexPlatformParameters(BaseModel):
    """Parameters for the Snowflake Cortex platform.

    This class encapsulates all configuration parameters for Snowflake Cortex
    client initialization.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["cortex"] = Field(
        default="cortex",
        description="The kind of platform parameters.",
    )

    snowflake_username: str | None = Field(
        default=None,
        description="The Snowflake username. Optional, as token-based auth is preferred.",
    )

    snowflake_password: str | None = Field(
        default=None,
        description="The Snowflake password. Optional, as token-based auth is preferred.",
    )

    snowflake_account: str | None = Field(
        default=None,
        description="The Snowflake account. If not provided, it will be"
        "inferred from the environment.",
    )

    snowflake_host: str | None = Field(
        default=None,
        description="The Snowflake host. If not provided, it will be"
        "inferred from the environment (built from account name).",
    )

    snowflake_warehouse: str | None = Field(
        default=None,
        description="The Snowflake warehouse. Optional.",
    )

    snowflake_database: str | None = Field(
        default=None,
        description="The Snowflake database. Optional.",
    )

    snowflake_schema: str | None = Field(
        default=None,
        description="The Snowflake schema. Optional.",
    )

    snowflake_role: str | None = Field(
        default=None,
        description="The Snowflake role. Optional.",
    )


class AzureOpenAIPlatformParameters(BaseModel):
    """Parameters for the Azure OpenAI platform.

    This class encapsulates all configuration parameters for Azure OpenAI client
    initialization.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["azure"] = Field(
        default="azure",
        description="The kind of platform parameters.",
    )

    azure_api_key: str | None = Field(
        default=None,
        description="The Azure OpenAI API key. If not provided, it will be "
        "attempted to be inferred from the environment.",
    )

    azure_endpoint_url: str | None = Field(
        default=None,
        description="The Azure OpenAI endpoint URL. If not provided, "
        "it will beattempted to be inferred from the environment.",
    )

    azure_deployment_name: str | None = Field(
        default=None,
        description="The Azure OpenAI deployment name. If not provided, "
        "it will be attempted to be inferred from the environment.",
    )

    azure_api_version: str | None = Field(
        default="2023-03-15-preview",
        description="The Azure OpenAI API version. If not provided, "
        "it will be attempted to be inferred from the environment.",
    )

    azure_deployment_name_embeddings: str | None = Field(
        default=None,
        description="The Azure OpenAI deployment name for embeddings. If not "
        "provided, it will be attempted to be inferred from the environment.",
    )

    azure_generated_endpoint_url: str = Field(
        default="",
        description="The Azure OpenAI generated endpoint URL "
        "(generated by the combination of the endpoint URL "
        "and the deployment name).",
    )

    azure_generated_endpoint_url_embeddings: str = Field(
        default="",
        description="The Azure OpenAI generated endpoint URL for embeddings "
        "(generated by the combination of the endpoint URL "
        "and the deployment name).",
    )


class GooglePlatformParameters(BaseModel):
    """Parameters for the Google platform.

    This class encapsulates all configuration parameters for Google client
    initialization.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["google"] = Field(
        default="google",
        description="The kind of platform parameters.",
    )

    google_api_key: str | None = Field(
        default=None,
        description="The Google API key. If not provided, it will be "
        "attempted to be inferred from the environment.",
    )


class GroqPlatformParameters(BaseModel):
    """Parameters for the Groq platform.

    This class encapsulates all configuration parameters for Groq client
    initialization.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["groq"] = Field(
        default="groq",
        description="The kind of platform parameters.",
    )

    groq_api_key: str | None = Field(
        default=None,
        description="The Groq API key. If not provided, it will be "
        "attempted to be inferred from the environment.",
    )


class ReductoPlatformParameters(BaseModel):
    """Parameters for the Reducto platform.

    This class encapsulates all configuration parameters for Reducto client
    initialization.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["reducto"] = Field(
        default="reducto",
        description="The kind of platform parameters.",
    )

    reducto_api_url: str = Field(
        default="https://backend.sema4ai.dev/reducto",
        description="The Reducto API URL.",
    )

    reducto_api_key: str | None = Field(
        default=None,
        description="The Reducto API key. If not provided, it will be "
        "attempted to be inferred from the environment.",
    )

    delegate_kind: str | None = Field(
        default=None,
        description="The kind of the delegate platform client.",
    )

    delegate_api_key: str | None = Field(
        default=None,
        description="The API key for the delegate platform client. If not "
        "provided, it will be attempted to be inferred from the environment.",
    )


AnyPlatformParameters = (
    OpenAIPlatformParameters
    | BedrockPlatformParameters
    | CortexPlatformParameters
    | AzureOpenAIPlatformParameters
    | GooglePlatformParameters
    | GroqPlatformParameters
    | ReductoPlatformParameters
)
