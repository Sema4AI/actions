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


def test_error_collecting_resources_with_missing_uri_params():
    import json

    import pytest
    from sema4ai.actions._action import Action

    from sema4ai.action_server.mcp.setup_mcp_server_from_actions import (
        McpServerSetupHelper,
    )

    def func(a: int, b: int):
        pass

    action = Action(
        pm=None,
        module_name="test",
        module_file="test.py",
        method=func,
        options=json.dumps(
            {
                "kind": "resource",
                "uri": "https://example.com/resource/{a}",  # missing {b}
            }
        ),
    )

    setup = McpServerSetupHelper()
    with pytest.raises(ValueError) as e:
        setup.register_action(
            func=func,
            action_package=None,
            action=action,
            display_name=None,
            doc_desc=None,
        )

    assert (
        "When collecting @resources, the parameters in the URI (found: ['a']) and the function parameters (found: ['a', 'b']) must match."
        in str(e.value)
    )


def test_error_collecting_resources_param_not_basic_type():
    import json

    import pytest
    from sema4ai.actions._action import Action

    from sema4ai.action_server.mcp.setup_mcp_server_from_actions import (
        McpServerSetupHelper,
    )

    class Foo:
        pass

    def func(a: Foo):  # We can only accept str, int, float, bool in this case
        pass

    action = Action(
        pm=None,
        module_name="test",
        module_file="test.py",
        method=func,
        options=json.dumps(
            {
                "kind": "resource",
                "uri": "https://example.com/resource/{a}",
            }
        ),
    )

    setup = McpServerSetupHelper()
    with pytest.raises(ValueError) as e:
        setup.register_action(
            func=func,
            action_package=None,
            action=action,
            display_name=None,
            doc_desc=None,
        )

    assert (
        "When collecting @resources, parameter 'a' has type 'Foo' but only basic types (str, int, float, bool) are supported."
        in str(e.value)
    )


def test_resources_work_with_unmanaged_params():
    import json

    from sema4ai.actions._action import Action
    from sema4ai.actions._secret import Secret

    from sema4ai.action_server.mcp.setup_mcp_server_from_actions import (
        McpServerSetupHelper,
    )

    # Managed parameters (such as secrets) must be supported (without the user passing it in the URI).
    def func(secret: Secret):
        pass

    action = Action(
        pm=None,
        module_name="test",
        module_file="test.py",
        method=func,
        options=json.dumps(
            {
                "kind": "resource",
                "uri": "https://example.com/resource",
            }
        ),
    )

    setup = McpServerSetupHelper()
    setup.register_action(
        func=func,
        action_package=None,
        action=action,
        display_name=None,
        doc_desc=None,
    )
