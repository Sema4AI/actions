def test_mcp_tool_run(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        [
            "run",
            "-a",
            "create_ticket",
            "--console-colors=plain",
            "--",
            "--title",
            "my ticket title",
            "--description",
            "my ticket description",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    output = result.stdout.decode("utf-8")
    assert "create_ticket status: PASS" in output
