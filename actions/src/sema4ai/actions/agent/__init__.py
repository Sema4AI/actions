import json
import logging
from urllib.parse import urljoin

from pydantic import BaseModel

from sema4ai.actions.agent._client import AgentApiClientException, _AgentAPIClient

log = logging.getLogger(__name__)


class Agent(BaseModel):
    id: str
    name: str
    description: str | None = None
    mode: str | None = None


class Conversation(BaseModel):
    id: str
    name: str
    agent_id: str


def _get_all_pages(client: _AgentAPIClient, endpoint: str) -> list:
    all_data = []
    next_token = None

    while True:
        paginated_endpoint = endpoint
        if next_token:
            paginated_endpoint = f"{endpoint}?next={next_token}"

        response = client.request(paginated_endpoint)
        response_json = response.json()

        all_data.extend(response_json.get("data", response_json.get("messages", [])))
        if not response_json.get("next"):
            break

        next_token = response_json.get("next")

    return all_data


def _get_conversations(client: _AgentAPIClient, endpoint: str) -> list[Conversation]:
    full_url = urljoin(client.api_url, endpoint)
    log.info(f"Agent Server API Call URL: {full_url}")

    return [
        Conversation.model_validate(conversation)
        for conversation in _get_all_pages(client, endpoint)
    ]


def _get_agents(client: _AgentAPIClient, endpoint: str) -> list[Agent]:
    full_url = urljoin(client.api_url, endpoint)
    log.info(f"Agent Server API Call URL: {full_url}")

    all_agents = _get_all_pages(client, endpoint)
    return [Agent.model_validate(agent) for agent in all_agents]


def get_all_agents() -> list[Agent]:
    """Fetches a list of all available agents with their IDs and names.

    Returns:
        The list of all agents.
    """
    client = _AgentAPIClient()

    return _get_agents(client, "agents")


def get_agent_by_name(name: str) -> Agent | None:
    """Fetches the agent that matches the name.

    Args:
        name: The name of the agent

    Returns:
        The agent that matches the given name.
    """
    client = _AgentAPIClient()
    agents = _get_agents(client, "agents")

    return next((agent for agent in agents if agent.name == name), None)


def get_conversations(agent_id: str) -> list[Conversation]:
    """Fetches all conversations for an agent.

    Args:
        agent_id: The ID of the agent

    Returns:
        The list of conversations for the agent.
    """
    client = _AgentAPIClient()

    endpoint = f"agents/{agent_id}/conversations"
    full_url = urljoin(client.api_url, endpoint)
    log.info(f"Agent Server API Call URL: {full_url}")

    return _get_conversations(client, endpoint)


def get_conversation(agent_name: str, conversation_name: str) -> Conversation | None:
    """Fetches the conversation with the given name for an agent.

    Args:
        agent_name: The name of the agent
        conversation_name: The name of the conversation

    Returns:
        The conversation with the given name.
    """
    client = _AgentAPIClient()

    agent_result = get_agent_by_name(agent_name)
    if not agent_result:
        raise AgentApiClientException(f"No agent found with name '{agent_name}'")

    agent_id = agent_result.id
    endpoint = f"agents/{agent_id}/conversations"
    conversations = _get_conversations(client, endpoint)

    return next(
        (
            conversation
            for conversation in conversations
            if conversation_name == conversation.name
        ),
        None,
    )


def get_conversation_messages(agent_id: str, conversation_id: str) -> list[dict]:
    """Fetches all messages from a specific conversation.

    Args:
        agent_id: The ID of the agent
        conversation_id: The ID of the conversation

    Returns:
        The list of messages in the conversation.
    """
    client = _AgentAPIClient()

    endpoint = f"agents/{agent_id}/conversations/{conversation_id}/messages"
    full_url = urljoin(client.api_url, endpoint)
    log.info(f"Agent Server API Call URL: {full_url}")

    return _get_all_pages(client, endpoint)


def create_conversation(agent_id: str, conversation_name: str) -> Conversation:
    """Creates a new conversation for communication with an agent.

    Args:
        agent_id: The id of the agent to create conversation with
        conversation_name: The name of the conversation to be created

    Returns:
        The created conversation object.
    """
    client = _AgentAPIClient()

    endpoint = f"agents/{agent_id}/conversations"
    full_url = urljoin(client.api_url, endpoint)
    log.info(f"Agent Server API Call URL: {full_url}")

    response = client.request(
        endpoint,
        method="POST",
        json_data={"name": conversation_name},
    )

    return Conversation.model_validate(response.json())


def send_message(conversation_id: str, agent_id: str, message: str) -> str:
    """Sends a message within a conversation and retrieves the agent's response.

    Args:
        conversation_id: The ID of the conversation
        agent_id: The ID of the agent to send message to
        message: The message content to send

    Returns:
        Response containing either the agent's response or an error message
    """
    client = _AgentAPIClient()

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

    full_url = urljoin(client.api_url, endpoint)
    log.info(f"Agent Server API Call URL: {full_url}")
    response = client.request(
        endpoint,
        method="POST",
        json_data={"content": message},
    )

    response_json = response.json()
    log.info(f"Response from send_message: {response_json}")

    # Handle different response formats:
    # 1. Wrapped in 'data' field: {"data": [...messages...]}
    # 2. Direct list of messages: [...messages...]
    # 3. Single message response: {"id": "...", "content": "..."}
    # 4. Full conversation object: {"id": "...", "messages": [...messages...]}
    messages = []
    if isinstance(response_json, dict):
        if "data" in response_json:
            messages = response_json["data"]
        elif "messages" in response_json:
            # This is a full conversation object with messages
            messages = response_json["messages"]
        elif "content" in response_json:
            # Single message response
            return response_json.get("content", "")
    elif isinstance(response_json, list):
        messages = response_json

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
    "Agent",
    "AgentApiClientException",
    "Conversation",
    "create_conversation",
    "get_all_agents",
    "get_agent_by_name",
    "get_conversations",
    "get_conversation",
    "get_conversation_messages",
    "send_message",
]
