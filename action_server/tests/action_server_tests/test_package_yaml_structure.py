from sema4ai.action_server._selftest import ActionServerProcess


def test_package_yaml_structure_too_new(
    action_server_process: ActionServerProcess, datadir
):
    import pytest

    from sema4ai.action_server._selftest import ActionServerExitedError

    with pytest.raises(ActionServerExitedError):
        action_server_process.start(cwd=datadir / "pack_too_new", actions_sync=True)

    stderr = action_server_process.get_stderr()
    assert (
        "This version of the Action Server only supports `spec-version` `v1` or `v2`."
        in stderr
    )


def test_package_yaml_structure_warn_spec_version(
    action_server_process: ActionServerProcess, datadir
):
    action_server_process.start(cwd=datadir / "pack1", actions_sync=True, timeout=300)
    stderr = action_server_process.get_stderr()
    assert (
        "The `pythonpath` entries in `package.yaml` are only supported in `spec-version: v2`"
        in stderr
    )
