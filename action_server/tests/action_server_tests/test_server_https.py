import json

import pytest
from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess
from sema4ai.action_server._settings import get_user_sema4_path


@pytest.mark.integration_test
def test_serve_https(action_server_process: ActionServerProcess):
    from action_server_tests.fixtures import get_in_resources

    pack = get_in_resources("no_conda", "greeter")
    import os

    os.environ["SSL_CERT_FILE"] = str(
        get_user_sema4_path() / "action-server-public-certfile.pem"
    )
    os.environ["PYTHONTRUSTSTORE"] = "ssl"
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
