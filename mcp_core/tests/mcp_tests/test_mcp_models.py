import pytest

from sema4ai.mcp_core.mcp_models import (
    BaseModel,
    CallToolRequest,
    CallToolRequestParamsParams,
    CallToolResult,
    Implementation,
    InitializeRequest,
    InitializeResult,
    MessageType,
    ProgressNotification,
    ServerCapabilities,
    TextContent,
    create_mcp_model,
)


def test_initialize_request():
    """Test InitializeRequest model."""
    # Test creating from dict
    data = {
        "method": "initialize",
        "params": {
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
            "capabilities": {},
            "protocolVersion": "1.0",
        },
    }
    request = InitializeRequest.from_dict(data)
    # Verify fields
    assert request.method == "initialize"
    assert request.params.clientInfo.name == "test-client"
    assert request.params.clientInfo.version == "1.0.0"
    assert request.params.capabilities.to_dict() == {}
    assert request.params.protocolVersion == "1.0"


def test_progress_notification():
    """Test ProgressNotification model."""
    # Test creating from dict
    data = {
        "method": "progress",
        "params": {"progress": 50, "progressToken": "token123"},
    }
    notification = ProgressNotification.from_dict(data)
    # Verify fields
    assert notification.method == "progress"
    assert notification.params.progress == 50
    assert notification.params.progressToken == "token123"


def test_initialize_result():
    """Test InitializeResult model."""
    # Test creating from dict
    data = {
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
    assert result.capabilities.to_dict() == data["capabilities"]
    assert result.instructions == "Test instructions"
    assert result.protocolVersion == "1.0"
    assert result.serverInfo.name == "test-server"
    assert result.serverInfo.version == "1.0.0"


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
            "capabilities": {},
            "protocolVersion": "1.0",
        },
    }
    init_model = create_mcp_model(init_data)
    assert isinstance(init_model, InitializeRequest)
    assert init_model.method == "initialize"
    assert init_model.params.clientInfo.name == "test-client"


def test_nested_object_conversion():
    """Test that nested objects and lists are properly converted in from_dict."""
    # Create a test dictionary with nested objects and lists
    data = {
        "method": "tools/call",
        "params": {
            "name": "test_tool",
            "arguments": {"param1": "value1", "param2": 42},
        },
    }

    # Create instance from dict
    request = CallToolRequest.from_dict(data)

    # Verify the nested objects are properly converted
    assert isinstance(request, CallToolRequest)
    assert isinstance(request.params, CallToolRequestParamsParams)
    assert request.params.name == "test_tool"
    assert isinstance(request.params.arguments, dict)
    assert request.params.arguments["param1"] == "value1"
    assert request.params.arguments["param2"] == 42

    # Test with a result containing a list of TextContent
    result_data = {
        "content": [
            {"type": "text", "text": "Hello", "kind": "text"},
            {"type": "text", "text": "World", "kind": "text"},
        ]
    }

    result = CallToolResult.from_dict(result_data)

    # Verify the list items are properly converted
    assert isinstance(result, CallToolResult)
    assert isinstance(result.content, list)
    assert len(result.content) == 2
    assert all(isinstance(item, TextContent) for item in result.content)
    assert result.content[0].text == "Hello"
    assert result.content[1].text == "World"
