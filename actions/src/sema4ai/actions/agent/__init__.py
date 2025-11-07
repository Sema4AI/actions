import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel

from sema4ai.actions._response import ActionError
from sema4ai.actions.agent._client import _AgentAPIClient
from sema4ai.actions.agent._models import (
    ConversationHistoryParams,
    ConversationHistorySpecialMessage,
    DataFrameInfo,
    DocumentsParams,
    DocumentsSpecialMessage,
    MemoriesParams,
    MemoriesSpecialMessage,
    Prompt,
    PromptAgentMessage,
    PromptAudioContent,
    PromptDocumentContent,
    PromptImageContent,
    PromptTextContent,
    PromptToolResultContent,
    PromptToolUseContent,
    PromptUserMessage,
    ToolDefinition,
)
from sema4ai.actions.agent._platforms import (
    AnyPlatformParameters,
    AzureOpenAIPlatformParameters,
    BedrockPlatformParameters,
    CortexPlatformParameters,
    GooglePlatformParameters,
    GroqPlatformParameters,
    OpenAIPlatformParameters,
    ReductoPlatformParameters,
)
from sema4ai.actions.agent._response import (
    ResponseAudioContent,
    ResponseDocumentContent,
    ResponseImageContent,
    ResponseMessage,
    ResponseTextContent,
    ResponseToolUseContent,
    TokenUsage,
)

if TYPE_CHECKING:
    from sema4ai.actions import Table


# Cache PyArrow availability to avoid repeated imports
_pyarrow_available = None


def _is_pyarrow_available() -> bool:
    """Check if PyArrow is available, caching the result."""
    global _pyarrow_available
    if _pyarrow_available is None:
        try:
            import pyarrow  # noqa: F401
            import pyarrow.parquet  # noqa: F401

            _pyarrow_available = True
        except ImportError:
            _pyarrow_available = False
    return _pyarrow_available


def _parse_dataframe_response_from_parquet(response) -> dict:
    """Parse dataframe response from Parquet format.

    Args:
        response: HTTP response object with Parquet data

    Returns:
        dict: Parsed dataframe data with columns, rows, name, description
    """
    from io import BytesIO

    import pyarrow as pa  # noqa: F401
    import pyarrow.parquet as pq

    # Read Parquet data (use .data for urllib3 HTTPResponse)
    parquet_data = BytesIO(response.data)
    table = pq.read_table(parquet_data)

    # Convert to our format
    columns = table.column_names
    rows = []
    for i in range(len(table)):
        row = []
        for col in columns:
            value = table[col][i].as_py()
            row.append(value)
        rows.append(row)

    return {
        "columns": columns,
        "rows": rows,
        "name": None,  # Parquet doesn't include metadata
        "description": None,
    }


log = logging.getLogger(__name__)


def _get_id_from_action_context(action_context, id_key: str) -> str:
    value = action_context.value
    if not isinstance(value, dict):
        raise ActionError(
            "Internal Error: Unable to get the Action Context because it's not a dictionary"
        )

    invocation_context = value.get("invocation_context")
    if not invocation_context:
        raise ActionError(
            "Internal Error: No invocation context found in the action context!"
        )
    if not isinstance(invocation_context, dict):
        raise ActionError(
            "Internal Error: Unable to get the invocation context because it's not a dictionary"
        )

    id_value = invocation_context.get(id_key)
    if not id_value:
        raise ActionError(
            f"Internal Error: No {id_key} found in the invocation_context!"
        )
    if not isinstance(id_value, str):
        raise ActionError(
            f"Internal Error: {id_key} is not a string (found: {id_value} ({type(id_value)}))!"
        )
    return id_value


def _get_id_from_invocation_context(
    invocation_context_object, id_key: str
) -> str | None:
    invocation_context = invocation_context_object.value
    if not invocation_context:
        return None
    if not isinstance(invocation_context, dict):
        raise ActionError(
            "Internal Error: Unable to get the invocation context because it's not a dictionary"
        )

    # If we have an invocation context, we should always have the id!
    id_value = invocation_context.get(id_key)

    if not id_value:
        raise ActionError(
            f"Internal Error: No {id_key} found in the invocation_context!"
        )

    if not isinstance(id_value, str):
        raise ActionError(
            f"Internal Error: {id_key} is not a string (found: {id_value} ({type(id_value)}))!"
        )
    return id_value


def _get_id_generic(id_key: str, header_key: str) -> str:
    from sema4ai.actions._action import get_current_requests_contexts

    id_value = None
    request_contexts = get_current_requests_contexts()
    if request_contexts is None:
        raise ActionError(
            f"Internal Error: Unable to get the {id_key} (no context available)"
        )

    # Prefer invocation context.
    if request_contexts.invocation_context:
        id_value = _get_id_from_invocation_context(
            request_contexts.invocation_context, id_key
        )

    if id_value is None:
        # Alternative use case when coupled directly with the
        # agent server without a router to make the invocation/action context
        # available.
        request = request_contexts._request
        if request:
            id_value = request.headers.get(header_key)

    if id_value is None:
        action_context = request_contexts.action_context
        if action_context:
            # Old use case (without separate id in the action context)
            id_value = _get_id_from_action_context(action_context, id_key)

    if id_value is None:
        # Ok, unable to get the id through any of the heuristics,
        # let's raise an error.
        raise ActionError(
            f"Internal Error: Unable to get the {id_key} from the action context or the request headers"
        )

    return id_value


def get_thread_id() -> str:
    """Get the thread ID from the action context or the request headers.

    Note:
        This will raise an ActionError if the thread ID cannot be found. This is expected when calling this
        function directly from VSCode unless the `x-invoked_for_thread_id` header is set in the request in configured
        inputs.
    """
    return _get_id_generic("thread_id", "x-invoked_for_thread_id")


def get_agent_id() -> str:
    """Get the agent ID from the action context or the request headers.

    Note:
        This will raise an ActionError if the agent ID cannot be found. This is expected when calling this
        function directly from VSCode unless the `x-invoked_by_assistant_id` header is set in the request in configured
        inputs.
    """
    return _get_id_generic("agent_id", "x-invoked_by_assistant_id")


def prompt_generate(
    prompt: Prompt | dict,
    platform_config: AnyPlatformParameters | dict | None = None,
    thread_id: str | None = None,
    agent_id: str | None = None,
    model_name: str | None = None,
) -> ResponseMessage:
    """Gives a prompt to an agent.

    Args:
        prompt: The prompt to generate.
        platform_config: The platform configuration if method is called without action context (optional).
        thread_id: The thread ID to use for the prompt (optional).
        agent_id: The agent ID to use for the prompt (optional).
        model_name: The model name to use for the prompt (optional).

    Note:
        Either platform_config, thread_id or agent_id must be provided when calling this method without action context.
        The platform_config will be automatically obtained from the agent which is related to the thread_id or agent_id.

    Returns:
        JSON representation of the response from the agent.
    """
    if not (platform_config or thread_id or agent_id):
        # If none of the arguments are provided, we need to get the thread_id and agent_id from the action context.
        # If it doesn't exist, then we raise an error as we can't generate a prompt without a thread_id.
        thread_id = get_thread_id()

    client = _AgentAPIClient()

    # Skip validation when passing dicts to have an escape hatch if the agent-server api changes
    if isinstance(prompt, Prompt):
        prompt = prompt.model_dump()

    if isinstance(platform_config, BaseModel):
        platform_config = platform_config.model_dump()

    payload = {"prompt": prompt, "platform_config_raw": platform_config}
    query_params = {}
    if thread_id:
        query_params["thread_id"] = thread_id
    if agent_id:
        query_params["agent_id"] = agent_id
    if model_name:
        query_params["model_name"] = model_name

    response = client.request(
        "prompts/generate",
        method="POST",
        json_data=payload,
        query_params=query_params,
    )
    return response.json()


def list_data_frames() -> list[DataFrameInfo]:
    """List all data frames available in the current thread.

    Returns:
        List of DataFrameInfo objects containing:
        - name: str - Name of the dataframe
        - description: str | None - Description of the dataframe
        - num_rows: int - Number of rows
        - num_columns: int - Number of columns
        - column_headers: list[str] - List of column names

    Raises:
        ActionError: If called outside of an action context or if unable to fetch dataframes.

    Note:
        This function requires the agent-server to support the dataframes API endpoint.
        If the endpoint is not available, this will raise an ActionError.
    """
    from sema4ai.actions.agent._client import AgentApiClientException

    thread_id = get_thread_id()
    client = _AgentAPIClient()

    try:
        response = client.request(
            f"threads/{thread_id}/data-frames",
            method="GET",
        )
        return response.json()
    except AgentApiClientException as e:
        raise ActionError(
            f"Failed to list dataframes from thread {thread_id}: {e}"
        ) from e


def get_data_frame(
    name: str,
    limit: int = 1000,
    offset: int = 0,
    column_names: list[str] | None = None,
    order_by: str | None = None,
) -> "Table":
    """Get a data frame by name from the current thread.

    Args:
        name: Name of the data frame to retrieve
        limit: Maximum number of rows to fetch (default: 1000).
            For very large dataframes, consider using SQL to filter data before fetching.
        offset: Number of rows to skip from the beginning (default: 0).
            Useful for pagination when combined with limit.
        column_names: List of specific column names to retrieve. If not provided, all columns are returned.
        order_by: Column name to sort by.

    Returns:
        Table object with the data frame contents, including:
        - columns: list[str]
        - rows: list[list]
        - name: str | None
        - description: str | None

    Raises:
        ActionError: If called outside of an action context or if unable to fetch data frame.

    Note:
        This function requires the agent-server to support the dataframes API endpoint.
        If the endpoint is not available, this will raise an ActionError.
    """
    from sema4ai.actions import Table
    from sema4ai.actions.agent._client import AgentApiClientException

    thread_id = get_thread_id()
    client = _AgentAPIClient()

    try:
        query_params: dict[str, int | str] = {"limit": limit, "offset": offset}

        if column_names:
            query_params["column_names"] = ",".join(column_names)
        if order_by:
            query_params["order_by"] = order_by

        # Request Parquet format if PyArrow is available, otherwise JSON
        requested_format = "parquet" if _is_pyarrow_available() else "json"
        query_params["output_format"] = requested_format

        response = client.request(
            f"threads/{thread_id}/data-frames/{name}",
            method="GET",
            query_params=query_params,
        )

        if requested_format == "parquet":
            data = _parse_dataframe_response_from_parquet(response)
        else:
            data = response.json()

        return Table(
            columns=data["columns"],
            rows=data["rows"],
            name=data.get("name"),
            description=data.get("description"),
        )
    except AgentApiClientException as e:
        # Convert 404 to ActionError for better UX
        if e.status_code == 404:
            raise ActionError(
                f"Data frame '{name}' not found in thread {thread_id}"
            ) from e
        # Wrap other errors in ActionError
        raise ActionError(
            f"Failed to fetch dataframe '{name}' from thread {thread_id}: {e}"
        ) from e


__all__ = [
    "get_thread_id",
    "get_agent_id",
    "prompt_generate",
    "list_data_frames",
    "get_data_frame",
    "Prompt",
    "PromptTextContent",
    "PromptImageContent",
    "PromptAudioContent",
    "PromptDocumentContent",
    "PromptToolResultContent",
    "PromptToolUseContent",
    "PromptAgentMessage",
    "PromptUserMessage",
    "ConversationHistoryParams",
    "ConversationHistorySpecialMessage",
    "DocumentsParams",
    "DocumentsSpecialMessage",
    "MemoriesParams",
    "MemoriesSpecialMessage",
    "ToolDefinition",
    "AnyPlatformParameters",
    "BedrockPlatformParameters",
    "CortexPlatformParameters",
    "OpenAIPlatformParameters",
    "AzureOpenAIPlatformParameters",
    "GooglePlatformParameters",
    "GroqPlatformParameters",
    "ReductoPlatformParameters",
    "ResponseAudioContent",
    "ResponseDocumentContent",
    "ResponseImageContent",
    "ResponseMessage",
    "ResponseTextContent",
    "ResponseToolUseContent",
    "TokenUsage",
]
