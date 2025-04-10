import json

import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


@pytest.mark.integration_test
def test_server_custom_model_argument(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    data_regression,
) -> None:
    from action_server_tests.fixtures import fix_openapi_json, get_in_resources

    pack = get_in_resources("no_conda", "custom_model")
    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
    )

    openapi_json = client.get_openapi_json()
    spec = json.loads(openapi_json)
    # print(json.dumps(spec, indent=4))

    data_regression.check(fix_openapi_json(spec))

    found = client.post_get_str(
        "api/actions/custom-model/my-action/run",
        {
            "x": "Foo",
            "data": {
                "name": "data-name",
                "price": 22,
                "is-offer": None,
                "depends_on": {"city": "Foo"},
            },
        },
    )
    assert json.loads(found) == {"accepted": True, "depends_on": {"city": "Foo"}}

    # Bad arguments
    client.post_error(
        "api/actions/custom-model/my-action/run",
        422,
        {"x": "Foo", "data": {"name": "data-name"}},  # Missing fields
    )
