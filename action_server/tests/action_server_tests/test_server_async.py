from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


def test_server_async_api_requests_while_waiting_for_action_to_complete(
    action_server_process: ActionServerProcess, client: ActionServerClient, datadir
):
    """
    Test that the server can handle requests while waiting for an action to complete.
    """
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

    # TODO: Check for the APIs to:
    # - Get the run id from the request id.
    # - Get the status of the action.
    # - Cancel the action.


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

    # TODO: Check for the APIs to:
    # - Get the result of the action.
    # - Get the status of the action.
    # - Check that cancelling returns that the action was already finished.
