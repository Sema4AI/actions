from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


def test_server_async_api_requests_while_waiting_for_action_to_complete(
    action_server_process: ActionServerProcess, client: ActionServerClient, datadir
):
    """
    Test that the server can handle requests while waiting for an action to complete.
    """
    from devutils.fixtures import wait_for_non_error_condition

    from sema4ai.action_server.vendored_deps.url_callback_server import (
        start_server_in_thread,
    )

    fut_uri, fut_address = start_server_in_thread(port=0)
    action_server_process.start(
        cwd=datadir,
        actions_sync=True,
        db_file="server.db",
    )

    callback_url = fut_address.result(10)
    assert callback_url

    response = client.post_get_response(
        "api/actions/test-server-async/sleep-action/run",
        {"time_to_sleep": 20},  # Sleep for a long time.
        {
            "x-actions-async-timeout": "0.2",  # Return after 0.2 seconds
            "x-actions-async-callback": callback_url,
            "x-actions-request-id": "123",  # Can be used to cancel the action, get status, get the result, ...
        },
    )
    response.raise_for_status()
    headers = response.headers
    assert headers

    # Check for the message we received saying it's an async compute.
    assert (
        headers.get("x-action-async-completion") == "1"
    ), f"Failed to get x-action-async-completion. Headers: {headers}"

    def run_id_from_request_id_available():
        response = client.get_get_response(
            "api/runs/run-id-from-request-id/123",
            data={},
            # data={"request_id": "123"},
        )
        response.raise_for_status()

    # Get the run id from the request id
    # wait_for_non_error_condition(run_id_from_request_id_available)
    response = client.get_get_response(
        "api/runs/run-id-from-request-id/123",
        data={},
        # data={"request_id": "123"},
    )
    response.raise_for_status()
    run_id = response.json()["run_id"]
    assert run_id

    # Get the status of the action
    response = client.get_get_response(f"api/runs/{run_id}", data={})
    response.raise_for_status()
    status = response.json()
    assert status["status"] == 1  # 1=running

    # Cancel the action
    response = client.post_get_response(f"api/runs/{run_id}/cancel", data={})
    response.raise_for_status()

    assert response.json() is True

    # Get the status of the action
    def check_cancelled_status():
        response = client.get_get_response(f"api/runs/{run_id}", data={})
        response.raise_for_status()
        status = response.json()
        assert status["status"] == 4  # 4=cancelled

    wait_for_non_error_condition(check_cancelled_status)


def test_server_async_api(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
):
    """
    Process for asynchronously calling an action in the action server:

    - Action Server receives a request with something as x-actions-async-timeout: <timeout in seconds> and x-actions-async-callback: url
    - If the action completes before the timeout the regular value is returned
    - If the action takes longer then it'd receive that run_id in the body along with a header such as x-action-async-completion: true.
    - When the action completes that callback would be triggered with the return.

    -- at any point the server could poll for the request or cancel the action given the run id.
    """
    from action_server_tests.fixtures import get_in_resources

    from sema4ai.action_server.vendored_deps.url_callback_server import (
        start_server_in_thread,
    )

    fut_uri, fut_address = start_server_in_thread(port=0)

    pack = get_in_resources("no_conda", "greeter")
    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
    )

    callback_url = fut_address.result(10)
    assert callback_url

    response = client.post_get_response(
        "api/actions/greeter/greet/run",
        {"name": "Foo"},
        {
            "x-actions-async-timeout": "0",  # Return immediately
            "x-actions-async-callback": callback_url,
            "x-actions-request-id": "123",  # Can be used to cancel the action, get status, get the result, ...
        },
    )
    response.raise_for_status()
    found = response.text

    headers = response.headers
    assert headers

    # Check for the message we received saying it's an async compute.
    assert (
        headers.get("x-action-async-completion") == "1"
    ), f"Failed to get x-action-async-completion. Headers: {headers}"
    assert (
        headers.get("x-action-server-run-id") is not None
    ), f"Failed to get x-action-server-run-id. Headers: {headers}"

    assert found == '"async-return"', f"{found} != '\"async-return\"'"

    # Now check for the callback result after it's computed.
    result = fut_uri.result(10)
    assert result["body"] == '"Hello Mr. Foo."'
    headers = result["headers"]
    assert headers
    assert (
        headers.get("x-actions-request-id") == "123"
    ), f"Failed to get x-actions-request-id. Headers: {headers}"

    run_id = headers.get("x-action-server-run-id")
    assert run_id

    response = client.post_get_response(f"api/runs/{run_id}/cancel", data={})
    response.raise_for_status()
    # i.e.: the run was not running (so, it was not canceled)
    assert response.json() is False

    response = client.get_get_response(f"api/runs/{run_id}", data={})
    response.raise_for_status()
    assert response.json()["status"] == 2  # 2=finished
    assert response.json()["result"] == '"Hello Mr. Foo."'
