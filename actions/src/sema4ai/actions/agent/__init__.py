import json
import logging

from pydantic import BaseModel
from sema4ai.actions.agent._client import _AgentAPIClient

log = logging.getLogger(__name__)


class AgentApiClientException(Exception):
    """Exception raised when the Agent API client encounters an error."""

    pass


class Agent(BaseModel):
    id: str
    name: str
    description: str | None = None
    mode: str | None = None


class Conversation(BaseModel):
    id: str
    name: str
    agent_id: str


class _PaginatedResponse(BaseModel):
    data: list
    next: str | None = None
    has_more: bool = False


def _get_all_pages(client: _AgentAPIClient, endpoint: str) -> list:
    all_data = []
    next_token = None

    while True:
        paginated_endpoint = endpoint
        if next_token:
            paginated_endpoint = f"{endpoint}&next={next_token}"

        response = client.request(paginated_endpoint)
        response_json = response.json()

        paginated_response = _PaginatedResponse.model_validate(response_json)

        all_data.extend(paginated_response.data)
        if not paginated_response.next or not paginated_response.has_more:
            break

        next_token = paginated_response.next

    return all_data


def _get_conversations(client: _AgentAPIClient, endpoint: str) -> list[Conversation]:
    full_url = f"{client.api_url}/{endpoint}"
    log.info(f"Agent Server API Call URL: {full_url}")

    return [
        Conversation.model_validate(conversation)
        for conversation in _get_all_pages(client, endpoint)
    ]


def _get_agents(client: _AgentAPIClient, endpoint: str) -> list[Agent]:
    full_url = f"{client.api_url}/{endpoint}"
    log.info(f"Agent Server API Call URL: {full_url}")

    all_agents = _get_all_pages(client, endpoint)
    return [Agent.model_validate(agent) for agent in all_agents]


def get_all_agents(sema4_api_key: str | None = None) -> list[Agent]:
    """Fetches a list of all available agents with their IDs and names.

    Args:
        sema4_api_key: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

    Returns:
        The list of all agents.
    """
    # Initialize client with API key if provided
    client = _AgentAPIClient(api_key=sema4_api_key)

    return _get_agents(client, "agents")


def get_agent_by_name(name: str, sema4_api_key: str | None = None) -> list[Agent]:
    """Fetches agents by name.

    Args:
        name: The name of the agent
        sema4_api_key: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

    Returns:
        The list of agents that matches the given name.
    """
    # Initialize client with API key if provided
    client = _AgentAPIClient(api_key=sema4_api_key)

    return _get_agents(client, f"agents/?name={name}")


def get_conversations(
    agent_id: str, sema4_api_key: str | None = None
) -> list[Conversation]:
    """Fetches all conversations for an agent.

    Args:
        agent_id: The ID of the agent
        sema4_api_key: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

    Returns:
        The list of conversations for the agent.
    """
    client = _AgentAPIClient(api_key=sema4_api_key)

    endpoint = f"agents/{agent_id}/conversations"
    log.info(f"Agent Server API Call URL: {endpoint}")

    return _get_conversations(client, endpoint)


def get_conversation(
    agent_name: str, conversation_name: str, sema4_api_key: str | None = None
) -> list[Conversation]:
    """Fetches the conversation with the given name for an agent.

    Args:
        agent_name: The name of the agent
        conversation_name: The name of the conversation
        sema4_api_key: The API key for the Sema4 API if running in cloud. Leave empty if in Studio or SDK!

    Returns:
        The list of conversations with the given name.
    """
    client = _AgentAPIClient(api_key=sema4_api_key)

    agent_result = get_agent_by_name(agent_name, sema4_api_key)
    if not agent_result:
        raise AgentApiClientException(f"No agent found with name '{agent_name}'")

    if len(agent_result) > 1:
        raise AgentApiClientException(
            f"Multiple agents found with name '{agent_name}': {','.join([agent.name for agent in agent_result])}"
        )

    agent_id = agent_result[0].id
    endpoint = f"agents/{agent_id}/conversations?name={conversation_name}"
    conversations = _get_conversations(client, endpoint)

    return conversations


def get_conversation_messages(
    agent_id: str, conversation_id: str, sema4_api_key: str | None = None
) -> list[dict]:
    """Fetches all messages from a specific conversation.

    Args:
        agent_id: The ID of the agent
        conversation_id: The ID of the conversation
        sema4_api_key: The API key for the Sema4 API if running in cloud. Use LOCAL if in Studio or SDK!

    Returns:
        The list of messages in the conversation.
    """
    client = _AgentAPIClient(api_key=sema4_api_key)

    endpoint = f"agents/{agent_id}/conversations/{conversation_id}/messages"
    full_url = f"{client.api_url}/{endpoint}"
    log.info(f"Agent Server API Call URL: {full_url}")

    response = client.request(endpoint)
    response_json = response.json()

    return response_json.get("messages", [])


def create_conversation(
    agent_id: str, conversation_name: str, sema4_api_key: str | None = None
) -> Conversation:
    """Creates a new conversation for communication with an agent.

    Args:
        agent_id: The id of the agent to create conversation with
        conversation_name: The name of the conversation to be created
        sema4_api_key: The API key for the Sema4 API if running in cloud. Use LOCAL if in Studio or SDK!

    Returns:
        The created conversation.
    """
    client = _AgentAPIClient(api_key=sema4_api_key)

    endpoint = f"agents/{agent_id}/conversations"
    full_url = f"{client.api_url}/{endpoint}"
    log.info(f"Agent Server API Call URL: {full_url}")

    response = client.request(
        endpoint,
        method="POST",
        json_data={"name": conversation_name},
    )

    response_json = response.json()
    return Conversation.model_validate(response_json)


def send_message(
    conversation_id: str, agent_id: str, message: str, sema4_api_key: str | None = None
) -> str:
    """Sends a message within a conversation and retrieves the agent's response.

    Args:
        conversation_id: The ID of the conversation
        agent_id: The ID of the agent to send message to
        message: The message content to send
        sema4_api_key: The API key for the Sema4 API if running in cloud. Use LOCAL if in Studio or SDK!

    Returns:
        Response containing either the agent's response or an error message
    """
    client = _AgentAPIClient(api_key=sema4_api_key)

    # Handle case where conversation_id contains full path information
    conversation_id_only = conversation_id
    if "/" in conversation_id:
        parts = conversation_id.split("/")
        # Check if this is in the format agents/{agent_id}/conversations/{conversation_id}
        if len(parts) >= 4 and "conversations" in parts:
            conv_index = parts.index("conversations") + 1
            if conv_index < len(parts):
                conversation_id_only = parts[conv_index]
                log.info(f"Extracted conversation_id: {conversation_id_only} from path")
            else:
                # Invalid path format
                raise AgentApiClientException(
                    f"Invalid path format in conversation ID: {conversation_id}"
                )
        else:
            # Simple format like "abc/def"
            conversation_id_only = parts[-1]  # Just take the last part
            log.info(
                f"Using last path segment as conversation_id: {conversation_id_only}"
            )

    # Construct the endpoint with the provided agent_id and extracted conversation_id
    endpoint = f"agents/{agent_id}/conversations/{conversation_id_only}/messages"

    full_url = f"{client.api_url}/{endpoint}"
    log.info(f"Agent Server API Call URL: {full_url}")

    response = client.request(
        endpoint,
        method="POST",
        json_data={"content": message},
    )

    response_json = response.json()
    log.info(f"Response from send_message: {response_json}")

    messages = response_json.get("messages", [])
    if messages:
        for msg in reversed(messages):
            if msg.get("role") == "agent":
                agent_response = msg.get("content", "")
                log.info(f"Found agent response: {agent_response}")
                return agent_response

        # If no agent message found, return the last message content
        if isinstance(messages[-1], dict) and "content" in messages[-1]:
            last_message = messages[-1]["content"]
            log.info(f"No agent response found, returning last message: {last_message}")
            return last_message

        raise AgentApiClientException(
            "No agent response found in conversation messages"
        )

    return json.dumps(response_json)


__all__ = [
    "get_all_agents",
    "get_agent_by_name",
    "get_conversations",
    "get_conversation",
    "get_conversation_messages",
    "create_conversation",
    "send_message",
    "Agent",
    "Conversation",
    "AgentApiClientException",
]
