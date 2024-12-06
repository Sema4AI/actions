from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


def test_server_async_api(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
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

    found = client.post_get_str(
        "api/actions/greeter/greet/run",
        {"name": "Foo"},
        {
            "Authorization": "Bearer Foo",
            "x-actions-async-timeout": "0",
            "x-actions-async-callback": callback_url,
        },
    )

    # TODO: Finish this to do things async!
    assert found == '"Hello Mr. Foo."', f"{found} != '\"Hello Mr. Foo.\"'"

    # request_info = fut_uri.result(60 * 5)
    # print(request_info)
