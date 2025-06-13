def test_resource_template_matches():
    from sema4ai.action_server.mcp.setup_mcp_server_from_actions import (
        McpServerSetupHelper,
    )

    setup = McpServerSetupHelper()
    assert setup.resource_template_matches("https://example.com/resource/{id}") == {
        "id": "{id}"
    }
    assert setup.resource_template_matches("https://example.com/resource/123") == {}
