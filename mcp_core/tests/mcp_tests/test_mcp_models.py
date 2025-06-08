from sema4ai.mcp_core.mcp_models import (
    Annotations,
    BlobResourceContents,
    CallToolRequest,
    CallToolRequestParamsParams,
    CallToolResult,
    EmbeddedResource,
    InitializeRequest,
    InitializeResult,
    ProgressNotification,
    TextContent,
    TextResourceContents,
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
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
    }

    result = CallToolResult.from_dict(result_data)

    # Verify the list items are properly converted
    assert isinstance(result, CallToolResult)
    assert isinstance(result.content, list)
    assert len(result.content) == 2

    # Verify each item is a TextContent with the correct text
    for i, item in enumerate(result.content):
        assert isinstance(
            item, TextContent
        ), f"Item {i} is not a TextContent instance. Item data: {item}"
        assert item.type == "text", f"Item {i} has incorrect type. Item data: {item}"
        assert item.text in [
            "Hello",
            "World",
        ], f"Item {i} has incorrect text. Item data: {item}"


def test_embedded_resource_conversion():
    """Test that EmbeddedResource objects are properly converted from dictionaries."""
    # Test with TextResourceContents
    text_resource_data = {
        "type": "resource",
        "resource": {
            "type": "text",
            "text": "Hello, this is some text content",
            "mimeType": "text/plain",
            "uri": "data:text/plain;base64,SGVsbG8gV29ybGQ=",
        },
    }

    text_resource = EmbeddedResource.from_dict(text_resource_data)

    # Verify the EmbeddedResource is properly converted
    assert isinstance(text_resource, EmbeddedResource)
    assert text_resource.type == "resource"
    assert isinstance(text_resource.resource, TextResourceContents)
    assert text_resource.resource.text == "Hello, this is some text content"
    assert text_resource.resource.mimeType == "text/plain"
    assert text_resource.resource.uri == "data:text/plain;base64,SGVsbG8gV29ybGQ="

    # Test with BlobResourceContents
    blob_resource_data = {
        "type": "resource",
        "resource": {
            "type": "blob",
            "blob": "SGVsbG8gV29ybGQ=",  # Base64 encoded "Hello World"
            "uri": "data:text/plain;base64,SGVsbG8gV29ybGQ=",
            "mimeType": "text/plain",
        },
    }

    blob_resource = EmbeddedResource.from_dict(blob_resource_data)

    # Verify the EmbeddedResource is properly converted
    assert isinstance(blob_resource, EmbeddedResource)
    assert blob_resource.type == "resource"
    assert isinstance(blob_resource.resource, BlobResourceContents)
    assert blob_resource.resource.blob == "SGVsbG8gV29ybGQ="
    assert blob_resource.resource.uri == "data:text/plain;base64,SGVsbG8gV29ybGQ="
    assert blob_resource.resource.mimeType == "text/plain"

    # Test with annotations
    annotated_resource_data = {
        "type": "resource",
        "resource": {
            "type": "text",
            "text": "Annotated text content",
            "mimeType": "text/plain",
            "uri": "data:text/plain;base64,SGVsbG8gV29ybGQ=",
        },
        "annotations": {"audience": ["user", "assistant"], "priority": 0.5},
    }

    annotated_resource = EmbeddedResource.from_dict(annotated_resource_data)

    # Verify the EmbeddedResource with annotations is properly converted
    assert isinstance(annotated_resource, EmbeddedResource)
    assert annotated_resource.type == "resource"
    assert isinstance(annotated_resource.resource, TextResourceContents)
    assert annotated_resource.resource.text == "Annotated text content"
    assert annotated_resource.resource.mimeType == "text/plain"
    assert annotated_resource.resource.uri == "data:text/plain;base64,SGVsbG8gV29ybGQ="
    assert isinstance(annotated_resource.annotations, Annotations)
    assert annotated_resource.annotations.audience == ["user", "assistant"]
    assert annotated_resource.annotations.priority == 0.5
