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
    assert (
        "create_ticket status: PASS" in output
    ), f"Did not find 'create_ticket status: PASS' in output: {output}"


def test_mcp_prompt_run(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        [
            "run",
            "-a",
            "generate_ticket_summary",
            "--console-colors=plain",
            "--",
            "--ticket_id",
            "123",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    output = result.stdout.decode("utf-8")
    assert (
        "generate_ticket_summary status: PASS" in output
    ), f"Did not find 'generate_ticket_summary status: PASS' in output: {output}"


def test_mcp_resource_run(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        [
            "run",
            "-a",
            "get_ticket_details",
            "--console-colors=plain",
            "--",
            "--ticket_id",
            "123",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    output = result.stdout.decode("utf-8")
    assert (
        "get_ticket_details status: PASS" in output
    ), f"Did not find 'get_ticket_details status: PASS' in output: {output}"


def test_collect_metadata(datadir, data_regression):
    import json

    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        [
            "metadata",
            "--skip-lint",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    output = result.stdout.decode("utf-8")
    metadata = json.loads(output)

    use_file_basename(metadata)
    data_regression.check(metadata)


def use_file_basename(obj):
    import os.path

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "file" and isinstance(value, str):
                obj[key] = os.path.basename(value)
            else:
                use_file_basename(value)
    elif isinstance(obj, list):
        for item in obj:
            use_file_basename(item)
