import json

import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


@pytest.mark.integration_test
def test_serve_https(action_server_process: ActionServerProcess):
    from action_server_tests.fixtures import get_in_resources

    pack = get_in_resources("no_conda", "greeter")
    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        use_https=True,
        additional_args=["--ssl-self-signed"],
    )

    client = ActionServerClient(action_server_process, use_https=True)
    openapi_json = client.get_openapi_json()
    json.loads(openapi_json)  # Just check it can be loaded

    found = client.post_get_str(
        "api/actions/greeter/greet/run",
        {"name": "Foo"},
        {"Authorization": "Bearer Foo"},
    )
    assert found == '"Hello Mr. Foo."', f"{found} != '\"Hello Mr. Foo.\"'"
