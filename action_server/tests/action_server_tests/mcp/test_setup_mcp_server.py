def test_resource_template_matches():
    from sema4ai.action_server.mcp.setup_mcp_server_from_actions import (
        McpServerSetupHelper,
    )

    setup = McpServerSetupHelper()
    assert setup._resource_template_matches(
        "https://example.com/resource/{id}", "https://example.com/resource/123"
    ) == {"id": "123"}

    assert setup._resource_template_matches(
        "https://example.com/resource/{id}", "https://example.com/resource/123"
    ) == {"id": "123"}

    assert (
        setup._resource_template_matches(
            "https://example.com/resource/{id}", "https://example.com/resource/123/foo"
        )
        is None
    )

    assert setup._resource_template_matches("https://{k}:{v}", "https://key:value") == {
        "k": "key",
        "v": "value",
    }


def test_collect_and_call_resource():
    import json

    from action_server_tests.fixtures import run_async_in_new_thread
    from pydantic.networks import AnyUrl

    from sema4ai.action_server._models import Action
    from sema4ai.action_server.mcp.setup_mcp_server_from_actions import (
        McpServerSetupHelper,
    )

    action = Action(
        id="123",
        action_package_id="456",
        name="test",
        docs="test",
        file="test.py",
        lineno=1,
        input_schema=json.dumps({}),
        output_schema=json.dumps({}),
        enabled=True,
        is_consequential=None,
        managed_params_schema=None,
        options=json.dumps(
            {
                "kind": "resource",
                "uri": "https://example.com/resource/{a}",
            }
        ),
    )

    setup = McpServerSetupHelper()

    def run(*args, **kwargs):
        pass

    setup.register_action(
        func=run,
        action_package=None,
        action=action,
        display_name=None,
        doc_desc=None,
    )

    assert len(setup._resource_templates) == 1

    async def call():
        from mcp.types import ReadResourceRequest, ReadResourceRequestParams

        handler = setup.server.request_handlers[ReadResourceRequest]
        return await handler(
            ReadResourceRequest(
                method="resources/read",
                params=ReadResourceRequestParams(
                    uri=AnyUrl("https://example.com/resource/123")
                ),
            )
        )

    result = run_async_in_new_thread(call)
    print(result)
