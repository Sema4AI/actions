import os

import pytest

from sema4ai.actions.agent import (
    Agent,
    AgentApiClientException,
    Conversation,
    create_conversation,
    get_agent_by_name,
    get_all_agents,
    get_conversation,
    get_conversation_messages,
    get_conversations,
    send_message,
)


@pytest.fixture
def dummy_server():
    from actions_tests.agent_dummy_server import AgentDummyServer

    server = AgentDummyServer()
    server.start()

    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def sample_agents():
    """Sample agent data for testing."""
    from actions_tests.agent_dummy_server import SAMPLE_AGENTS

    return SAMPLE_AGENTS


@pytest.fixture
def sample_conversations():
    """Sample conversation data for testing."""
    from actions_tests.agent_dummy_server import SAMPLE_CONVERSATIONS

    return SAMPLE_CONVERSATIONS


@pytest.fixture
def sample_messages():
    """Sample message data for testing."""
    from actions_tests.agent_dummy_server import SAMPLE_MESSAGES

    return SAMPLE_MESSAGES


class TestAgent:
    def test_get_agent_by_name_success(self, dummy_server, sample_agents):
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            result = get_agent_by_name("Test Agent 1")

            assert result.name == "Test Agent 1"
            # Check that ID is a UUID
            import uuid

            assert uuid.UUID(result.id)
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]

    def test_get_all_agents_success(self, dummy_server, sample_agents):
        # Set environment variable to point to dummy server
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            result = get_all_agents()

            assert len(result) == 2
            assert isinstance(result[0], Agent)
            assert result[0].name == "Test Agent 1"
            assert result[1].name == "Test Agent 2"
            # Check that IDs are UUIDs
            import uuid

            assert uuid.UUID(result[0].id)
            assert uuid.UUID(result[1].id)
        finally:
            # Clean up environment variable
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]


class TestConversations:
    def test_get_conversations_success(self, dummy_server, sample_conversations):
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            # First get an agent to get its ID
            agents = get_all_agents()
            agent_id = agents[0].id

            result = get_conversations(agent_id)

            assert len(result) == 2
            assert isinstance(result[0], Conversation)
            assert result[0].agent_id == agent_id
            assert result[0].name == "Test Conversation 1"
            assert result[1].name == "Test Conversation 2"
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]

    def test_get_conversation_success(
        self, dummy_server, sample_agents, sample_conversations
    ):
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            result = get_conversation("Test Agent 1", "Test Conversation 1")

            assert result.name == "Test Conversation 1"
            # Check that agent_id is a UUID
            import uuid

            assert uuid.UUID(result.agent_id)
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]

    def test_get_conversation_agent_not_found(self, dummy_server):
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            with pytest.raises(
                AgentApiClientException,
                match="No agent found with name 'Non-existent Agent'",
            ):
                get_conversation("Non-existent Agent", "Test Conversation")
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]

    def test_create_conversation_success(self, dummy_server, sample_conversations):
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            # First get an agent to get its ID
            agents = get_all_agents()
            agent_id = agents[0].id

            result = create_conversation(agent_id, "New Conversation")

            assert isinstance(result, Conversation)
            assert result.name == "New Conversation"
            assert result.agent_id == agent_id
            # Check that ID is a UUID
            import uuid

            assert uuid.UUID(result.id)
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]


class TestMessages:
    def test_get_conversation_messages_success(self, dummy_server, sample_messages):
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            # First get an agent to get its ID
            agents = get_all_agents()
            agent_id = agents[0].id

            # Get conversations to get a conversation ID
            conversations = get_conversations(agent_id)
            conversation_id = conversations[0].id

            result = get_conversation_messages(agent_id, conversation_id)

            assert len(result) == 2
            assert result[0]["role"] == "user"
            assert result[0]["content"][0]["text"] == "What is the hottest day?"
            assert result[1]["role"] == "agent"
            # Check for the actual text content from the shared data
            assert (
                result[1]["content"][1]["text"]
                == 'Could you clarify what location, year, or data you\'re referring to when you ask "What is the hottest day?" For example, are you asking about the hottest day ever recorded on Earth, in a specific city, or for a recent time period?'
            )
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]

    def test_send_message_success(self, dummy_server, sample_messages):
        """Test successful message sending."""
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            # First get an agent to get its ID
            agents = get_all_agents()
            agent_id = agents[0].id

            # Get conversations to get a conversation ID
            conversations = get_conversations(agent_id)
            conversation_id = conversations[0].id

            result = send_message(conversation_id, agent_id, "Hello")

            # Should return the agent's response
            assert result == "Agent reply"
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]

    def test_send_message_with_path_conversation_id(
        self, dummy_server, sample_messages
    ):
        """Test send_message with conversation ID containing path."""
        api_url = f"http://127.0.0.1:{dummy_server.get_port()}"
        os.environ["SEMA4AI_API_V1_URL"] = api_url

        try:
            # First get an agent to get its ID
            agents = get_all_agents()
            agent_id = agents[0].id

            # Get conversations to get a conversation ID
            conversations = get_conversations(agent_id)
            conversation_id = conversations[0].id

            # Test with full path
            full_path = f"agents/{agent_id}/conversations/{conversation_id}"
            result = send_message(full_path, agent_id, "Hello")

            # Should extract conversation ID from path and return agent response
            assert result == "Agent reply"
        finally:
            if "SEMA4AI_API_V1_URL" in os.environ:
                del os.environ["SEMA4AI_API_V1_URL"]
