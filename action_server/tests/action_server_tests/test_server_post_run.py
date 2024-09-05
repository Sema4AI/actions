from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


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

    post_run_script = datadir / "post_run_script.py"
    assert os.path.exists(post_run_script)

    pack = get_in_resources("no_conda", "greeter")

    output_json = Path(datadir / "output.json")
    cmd = f"{Path(sys.executable).as_posix()} {post_run_script.as_posix()} {output_json.as_posix()} $base_artifacts_dir $run_artifacts_dir $run_id"

    env = {"S4_ACTION_SERVER_POST_RUN_CMD": cmd}
    action_server_process.start(
        cwd=pack, actions_sync=True, db_file="server.db", env=env
    )

    found = client.post_get_str(
        "api/actions/greeter/greet/run",
        {"name": "Foo"},
        {"Authorization": "Bearer Foo"},
    )
    assert found == '"Hello Mr. Foo."', f"{found} != '\"Hello Mr. Foo.\"'"

    def func():
        import json
        from pathlib import Path

        found = json.loads(Path(output_json).read_text())
        assert found["run_id"].startswith("run")
        base_artifacts_dir = found["base_artifacts_dir"]
        run_artifacts_dir = found["run_artifacts_dir"]
        assert os.path.exists(run_artifacts_dir)
        assert os.path.exists(base_artifacts_dir)

    wait_for_non_error_condition(func)
