from pathlib import Path

import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess
from sema4ai.action_server._settings import (
    HEADER_ACTION_ASYNC_COMPLETION,
    HEADER_ACTION_SERVER_RUN_ID,
    HEADER_ACTIONS_ASYNC_CALLBACK,
    HEADER_ACTIONS_ASYNC_TIMEOUT,
    HEADER_ACTIONS_REQUEST_ID,
)


@pytest.mark.integration_test
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
            HEADER_ACTIONS_ASYNC_TIMEOUT: "0.2",  # Return after 0.2 seconds
            HEADER_ACTIONS_ASYNC_CALLBACK: callback_url,
            HEADER_ACTIONS_REQUEST_ID: "123",  # Can be used to cancel the action, get status, get the result, ...
        },
    )
    response.raise_for_status()
    headers = response.headers
    assert headers
    assert response.json() == "async-return"

    # Check for the message we received saying it's an async compute.
    assert headers.get(HEADER_ACTION_ASYNC_COMPLETION) == "1", (
        f"Failed to get {HEADER_ACTION_ASYNC_COMPLETION}. Headers: {headers}"
    )

    def run_id_from_request_id_available():
        response = client.get_get_response(
            "api/runs/run-id-from-request-id/123",
            data={},
        )
        response.raise_for_status()

    # Get the run id from the request id
    # wait_for_non_error_condition(run_id_from_request_id_available)
    response = client.get_get_response(
        "api/runs/run-id-from-request-id/123",
        data={},
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

    assert response.json() == "cancelled"

    # Get the status of the action
    def check_cancelled_status():
        response = client.get_get_response(f"api/runs/{run_id}", data={})
        response.raise_for_status()
        status = response.json()
        assert status["status"] == 4  # 4=cancelled

    wait_for_non_error_condition(check_cancelled_status)


@pytest.mark.integration_test
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
            HEADER_ACTIONS_ASYNC_TIMEOUT: "0",  # Return immediately
            HEADER_ACTIONS_ASYNC_CALLBACK: callback_url,
            HEADER_ACTIONS_REQUEST_ID: "123",  # Can be used to cancel the action, get status, get the result, ...
        },
    )
    response.raise_for_status()
    found = response.text

    headers = response.headers
    assert headers

    # Check for the message we received saying it's an async compute.
    assert headers.get(HEADER_ACTION_ASYNC_COMPLETION) == "1", (
        f"Failed to get {HEADER_ACTION_ASYNC_COMPLETION}. Headers: {headers}"
    )
    assert headers.get(HEADER_ACTION_SERVER_RUN_ID) is not None, (
        f"Failed to get {HEADER_ACTION_SERVER_RUN_ID}. Headers: {headers}"
    )

    assert found == '"async-return"', f"{found} != '\"async-return\"'"

    # Now check for the callback result after it's computed.
    result = fut_uri.result(10)
    assert result["body"] == '"Hello Mr. Foo."'
    headers = result["headers"]
    assert headers
    assert headers.get(HEADER_ACTIONS_REQUEST_ID) == "123", (
        f"Failed to get {HEADER_ACTIONS_REQUEST_ID}. Headers: {headers}"
    )

    run_id = headers.get(HEADER_ACTION_SERVER_RUN_ID)
    assert run_id

    response = client.post_get_response(f"api/runs/{run_id}/cancel", data={})
    response.raise_for_status()
    # i.e.: the run was not running (so, it was not canceled)
    assert response.json() == "not-running"

    response = client.get_get_response(f"api/runs/{run_id}", data={})
    response.raise_for_status()
    assert response.json()["status"] == 2  # 2=finished
    assert response.json()["result"] == '"Hello Mr. Foo."'


def do_run(
    client: ActionServerClient, time_to_sleep: float, async_run: bool, request_id: str
):
    if async_run:
        headers = {
            HEADER_ACTIONS_ASYNC_TIMEOUT: "0",  # Return immediately
            HEADER_ACTIONS_REQUEST_ID: request_id,  # Can be used to cancel the action, get status, get the result, ...
        }
    else:
        headers = {}
    response = client.post_get_response(
        "api/actions/test-server-async/sleep-action/run",
        {"time_to_sleep": time_to_sleep},  # Sleep for a long time.
        headers,
    )
    response.raise_for_status()

    if async_run:
        found = response.text
        assert found == '"async-return"', f"{found} != '\"async-return\"'"

    headers = response.headers
    assert headers
    run_id = headers.get(HEADER_ACTION_SERVER_RUN_ID)
    assert run_id
    return run_id


@pytest.mark.integration_test
def test_server_async_process_poll_with_cancel(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir: Path,
):
    from devutils.fixtures import wait_for_non_error_condition

    action_server_process.start(
        cwd=datadir,
        actions_sync=True,
        db_file="server.db",
        max_processes=1,
    )

    def get_run_status(run_id: str):
        response = client.get_get_response(
            f"api/runs/{run_id}/fields", data={"fields": ["status"]}
        )
        response.raise_for_status()
        return response.json()["status"]

    run_id1 = do_run(client, 20, async_run=True, request_id="123")
    run_id2 = do_run(client, 20, async_run=True, request_id="456")

    # Cancel the second run (should still be in not-running state)
    response = client.post_get_response(f"api/runs/{run_id2}/cancel", data={})
    response.raise_for_status()
    assert response.json() == "cancelled"

    def check_cancelled_run2():
        status = get_run_status(run_id2)
        if status != 4:
            raise RuntimeError(f"Run {run_id2} is not cancelled. Status: {status}")

    def check_cancelled_run1():
        status = get_run_status(run_id1)
        if status != 4:
            raise RuntimeError(f"Run {run_id1} is not cancelled. Status: {status}")

    wait_for_non_error_condition(check_cancelled_run2, timeout=10)

    response = client.post_get_response(f"api/runs/{run_id1}/cancel", data={})
    response.raise_for_status()
    assert response.json() == "cancelled"

    # Check that first is also cancelled.

    wait_for_non_error_condition(check_cancelled_run1, timeout=10)

    # Ok, just cancelled both runs, now, let's check that a new run works properly.
    run_id3 = do_run(client, 0.01, async_run=False, request_id="789")

    def check_run_id3_completed():
        status = get_run_status(run_id3)
        if status != 2:
            raise RuntimeError(f"Run {run_id3} is not completed. Status: {status}")

    wait_for_non_error_condition(check_run_id3_completed, timeout=10)


@pytest.mark.integration_test
def test_cancel_existing_runs_on_restart(action_server_datadir, datadir):
    action_server_process = ActionServerProcess(action_server_datadir)
    try:
        action_server_process.start(
            cwd=datadir,
            actions_sync=True,
            db_file="server.db",
            max_processes=1,
        )
        client = ActionServerClient(action_server_process)
        run_id = do_run(client, 20, async_run=True, request_id="123")
    finally:
        action_server_process.stop()

    action_server_process = ActionServerProcess(action_server_datadir)
    try:
        # Ok, now, start a new action server and check that the run is cancelled.
        action_server_process.start(
            cwd=datadir,
            actions_sync=True,
            db_file="server.db",
            max_processes=1,
        )
        client = ActionServerClient(action_server_process)
        response = client.get_get_response(
            f"api/runs/{run_id}/fields", data={"fields": ["status"]}
        )
        response.raise_for_status()
        assert response.json()["status"] == 4  # 4=cancelled
    finally:
        action_server_process.stop()
