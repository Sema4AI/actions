import pytest

from sema4ai.mcp_core.mcp_models import (
    BaseModel,
    Implementation,
    InitializeRequest,
    InitializeResult,
    MessageType,
    ProgressNotification,
    ServerCapabilities,
    create_mcp_model,
)


def test_initialize_request():
    """Test InitializeRequest model."""
    # Test creating from dict
    data = {
        "method": "initialize",
        "params": {
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
            "clientId": "test-client-id",
        },
    }
    request = InitializeRequest.from_dict(data)

    # Verify fields
    assert request.method == "initialize"
    assert request.params["clientInfo"]["name"] == "test-client"
    assert request.params["clientInfo"]["version"] == "1.0.0"
    assert request.params["clientId"] == "test-client-id"

    # Test converting back to dict
    result_dict = request.to_dict()
    assert result_dict == data

    # Test message type
    assert request.get_message_type() == MessageType.REQUEST


def test_progress_notification():
    """Test ProgressNotification model."""
    # Test creating from dict
    data = {
        "method": "progress",
        "params": {
            "token": "test-token",
            "value": {
                "kind": "begin",
                "message": "Starting operation",
                "percentage": 0,
            },
        },
    }
    notification = ProgressNotification.from_dict(data)

    # Verify fields
    assert notification.method == "progress"
    assert notification.params["token"] == "test-token"
    assert notification.params["value"]["kind"] == "begin"
    assert notification.params["value"]["message"] == "Starting operation"
    assert notification.params["value"]["percentage"] == 0

    # Test converting back to dict
    result_dict = notification.to_dict()
    assert result_dict == data

    # Test message type
    assert notification.get_message_type() == MessageType.NOTIFICATION


def test_initialize_result():
    """Test InitializeResult model."""
    # Test creating from dict
    data = {
        "_meta": {"requestId": "123"},
        "capabilities": {
            "completions": {},
            "experimental": {},
            "logging": {},
            "prompts": {},
            "resources": {},
            "tools": {},
        },
        "instructions": "Test instructions",
        "protocolVersion": "1.0",
        "serverInfo": {"name": "test-server", "version": "1.0.0"},
    }
    result = InitializeResult.from_dict(data)

    # Verify fields
    assert result._meta["requestId"] == "123"
    assert result.capabilities == data["capabilities"]
    assert result.instructions == "Test instructions"
    assert result.protocolVersion == "1.0"
    assert result.serverInfo == data["serverInfo"]

    # Test converting back to dict
    result_dict = result.to_dict()
    assert result_dict == data

    # Test message type
    assert result.get_message_type() == MessageType.RESPONSE


def test_base_model():
    """Test BaseModel functionality."""
    # Test that BaseModel methods are available on subclasses
    request = InitializeRequest(
        method="initialize",
        params={
            "clientInfo": {"name": "test", "version": "1.0"},
            "clientId": "test-id",
        },
    )
    assert hasattr(request, "from_dict")
    assert hasattr(request, "to_dict")
    assert hasattr(request, "get_message_type")


def test_create_mcp_model():
    """Test the create_mcp_model factory function."""
    # Test creating an InitializeRequest
    init_data = {
        "method": "initialize",
        "params": {
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
            "clientId": "test-client-id",
        },
    }
    init_model = create_mcp_model(init_data)
    assert isinstance(init_model, InitializeRequest)
    assert init_model.method == "initialize"
    assert init_model.params["clientInfo"]["name"] == "test-client"
    assert init_model.get_message_type() == MessageType.REQUEST

    # Test creating a ProgressNotification
    progress_data = {
        "method": "notifications/progress",
        "params": {
            "token": "test-token",
            "value": {
                "kind": "begin",
                "message": "Starting operation",
                "percentage": 0,
            },
        },
    }
    progress_model = create_mcp_model(progress_data)
    assert isinstance(progress_model, ProgressNotification)
    assert progress_model.method == "notifications/progress"
    assert progress_model.params["token"] == "test-token"
    assert progress_model.get_message_type() == MessageType.NOTIFICATION

    # Test error cases
    with pytest.raises(
        ValueError, match="Input dictionary must contain a 'method' field"
    ):
        create_mcp_model({})

    with pytest.raises(
        ValueError, match="No MCP model class found for method: invalid_method"
    ):
        create_mcp_model({"method": "invalid_method"})
