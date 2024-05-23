def test_tasks_mutable(datadir) -> None:
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["run", "--console-colors=plain", "-a", "division_error"],
        returncode=0,
        cwd=str(datadir),
    )

    stdout = result.stdout.decode("utf-8")
    assert "division by zero" in stdout

    result = sema4ai_actions_run(
        ["run", "--console-colors=plain", "-a", "raises_error"],
        returncode=0,
        cwd=str(datadir),
    )

    stdout = result.stdout.decode("utf-8")
    assert "Something went wrong" in stdout
