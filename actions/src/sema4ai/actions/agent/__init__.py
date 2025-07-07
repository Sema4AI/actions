import logging

from pydantic import BaseModel
from sema4ai.actions._response import ActionError
from sema4ai.actions.agent._client import _AgentAPIClient
from sema4ai.actions.agent._models import (
    ConversationHistoryParams,
    ConversationHistorySpecialMessage,
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
) -> dict:
    """Gives a prompt to an agent.

    Args:
        prompt: The prompt to generate.
        platform_config: The platform configuration if method is called without action context (optional).
        thread_id: The thread ID to use for the prompt (optional).
        agent_id: The agent ID to use for the prompt (optional).

    Note:
        Either platform_config, thread_id or agent_id must be provided when calling this method without action context.

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

    response = client.request(
        "prompts/generate",
        method="POST",
        json_data=payload,
        query_params=query_params,
    )
    return response.json()


__all__ = [
    "get_thread_id",
    "get_agent_id",
    "prompt_generate",
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
]
