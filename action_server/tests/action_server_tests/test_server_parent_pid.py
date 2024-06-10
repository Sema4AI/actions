from devutils.fixtures import wait_for_condition

from sema4ai.action_server._robo_utils.process import Process
from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


def test_action_server_parent_pid(
    action_server_process: ActionServerProcess, data_regression
):
    from action_server_tests.fixtures import get_in_resources

    from sema4ai.action_server._robo_utils.process import kill_process_and_subprocesses

    process = Process(["python", "-c", "import time;time.sleep(1000000)"])
    process.start()
    pid = process.pid

    pack = get_in_resources("no_conda", "greeter")
    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        reuse_processes=True,
        min_processes=1,
        additional_args=[f"--parent-pid={pid}"],
    )

    client = ActionServerClient(action_server_process)

    found = client.post_get_str(
        "api/actions/greeter/greet/run",
        {"name": "Foo"},
        {"Authorization": "Bearer Foo"},
    )
    assert found == '"Hello Mr. Foo."', f"{found} != '\"Hello Mr. Foo.\"'"

    assert action_server_process.process.is_alive()

    kill_process_and_subprocesses(pid)

    wait_for_condition(lambda: not action_server_process.process.is_alive())
