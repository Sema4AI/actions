import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


@pytest.mark.integration_test
def test_server_post_run(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import os
    import sys
    from pathlib import Path

    from action_server_tests.fixtures import get_in_resources
    from devutils.fixtures import wait_for_non_error_condition

    from sema4ai.action_server._encryption import make_unencrypted_data_envelope

    post_run_script = datadir / "post_run_script.py"
    assert os.path.exists(post_run_script)

    pack = get_in_resources("no_conda", "greeter")

    output_json = Path(datadir / "output.json")
    cmd = f"{Path(sys.executable).as_posix()} {post_run_script.as_posix()} {output_json.as_posix()} $base_artifacts_dir $run_artifacts_dir $run_id $agent_id"

    env = {"SEMA4AI_ACTION_SERVER_POST_RUN_CMD": cmd}
    action_server_process.start(
        cwd=pack, actions_sync=True, db_file="server.db", env=env
    )

    x_action_context = make_unencrypted_data_envelope(
        {
            "invocation_context": {
                "agent_id": "my-agent-id",
                "invoked_on_behalf_of_user_id": "my-user-id",
                "thread_id": "my-thread-id",
                "tenant_id": "my-tenant-id",
            }
        }
    )
    found = client.post_get_str(
        "api/actions/greeter/greet/run",
        {"name": "Foo"},
        headers={"x-action-context": x_action_context, "Authorization": "Bearer Foo"},
    )
    assert found == '"Hello Mr. Foo."', f"{found} != '\"Hello Mr. Foo.\"'"

    def func():
        import json

        found = json.loads(Path(output_json).read_text())
        assert found["run_id"].startswith("run")
        base_artifacts_dir = found["base_artifacts_dir"]
        run_artifacts_dir = found["run_artifacts_dir"]
        agent_id = found["agent_id"]
        thread_id = found["thread_id"]
        action_name = found["action_name"]

        assert agent_id == "my-agent-id"
        assert thread_id == "my-thread-id"
        assert os.path.exists(run_artifacts_dir)
        assert os.path.exists(base_artifacts_dir)
        assert action_name == "greet"

    wait_for_non_error_condition(func)


@pytest.mark.integration_test
def test_server_post_run_on_failure(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import os
    import sys
    from pathlib import Path

    from action_server_tests.fixtures import get_in_resources
    from devutils.fixtures import wait_for_non_error_condition

    from sema4ai.action_server._encryption import make_unencrypted_data_envelope

    post_run_script = datadir / "post_run_script.py"
    assert os.path.exists(post_run_script)

    pack = get_in_resources("no_conda", "calculator")

    output_json = Path(datadir / "output.json")
    cmd = f"{Path(sys.executable).as_posix()} {post_run_script.as_posix()} {output_json.as_posix()} $base_artifacts_dir $run_artifacts_dir $run_id $agent_id"

    env = {"SEMA4AI_ACTION_SERVER_POST_RUN_CMD": cmd}
    action_server_process.start(
        cwd=pack, actions_sync=True, db_file="server.db", env=env
    )

    x_action_context = make_unencrypted_data_envelope(
        {
            "invocation_context": {
                "agent_id": "my-agent-id",
                "invoked_on_behalf_of_user_id": "my-user-id",
                "thread_id": "my-thread-id",
                "tenant_id": "my-tenant-id",
            }
        }
    )
    client.post_error(
        "api/actions/calculator/broken-action/run",
        500,
        headers={"x-action-context": x_action_context, "Authorization": "Bearer Foo"},
    )

    def func():
        import json

        found = json.loads(Path(output_json).read_text())
        assert found["run_id"].startswith("run")
        base_artifacts_dir = found["base_artifacts_dir"]
        run_artifacts_dir = found["run_artifacts_dir"]
        agent_id = found["agent_id"]
        thread_id = found["thread_id"]
        action_name = found["action_name"]

        assert agent_id == "my-agent-id"
        assert thread_id == "my-thread-id"
        assert os.path.exists(run_artifacts_dir)
        assert os.path.exists(base_artifacts_dir)
        assert action_name == "broken_action"

    wait_for_non_error_condition(func)


@pytest.mark.integration_test
def test_server_bad_post_run_command(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import sys
    from pathlib import Path

    from action_server_tests.fixtures import get_in_resources

    from sema4ai.action_server._encryption import make_unencrypted_data_envelope

    post_run_script = datadir / "post_run_script-not-there.py"

    pack = get_in_resources("no_conda", "calculator")

    output_json = Path(datadir / "output.json")
    cmd = f"{Path(sys.executable).as_posix()} {post_run_script.as_posix()} {output_json.as_posix()} $base_artifacts_dir $run_artifacts_dir $run_id $agent_id"

    env = {"SEMA4AI_ACTION_SERVER_POST_RUN_CMD": cmd}
    action_server_process.start(
        cwd=pack, actions_sync=True, db_file="server.db", env=env
    )

    x_action_context = make_unencrypted_data_envelope(
        {
            "invocation_context": {
                "agent_id": "my-agent-id",
                "invoked_on_behalf_of_user_id": "my-user-id",
                "thread_id": "my-thread-id",
                "tenant_id": "my-tenant-id",
            }
        }
    )
    client.post_error(
        "api/actions/calculator/broken-action/run",
        500,
        headers={"x-action-context": x_action_context, "Authorization": "Bearer Foo"},
    )
