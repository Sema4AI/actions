import pytest
import requests

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess
from sema4ai.action_server._settings import get_user_sema4_path


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
    requests.get(
        client.build_full_url("openapi.json"),
        verify=str(get_user_sema4_path() / "action-server-public-certfile.pem"),
    ).json()  # check that it loads the json

    found = requests.post(
        client.build_full_url("api/actions/greeter/greet/run"),
        json={"name": "Foo"},
        headers={"Authorization": "Bearer Foo"},
        verify=str(get_user_sema4_path() / "action-server-public-certfile.pem"),
    ).text
    assert found == '"Hello Mr. Foo."', f"{found} != '\"Hello Mr. Foo.\"'"
