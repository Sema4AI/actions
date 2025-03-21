import pytest

from sema4ai.action_server._selftest import ActionServerProcess


@pytest.mark.integration_test
def test_package_yaml_structure_too_new(
    action_server_process: ActionServerProcess, datadir
):
    from sema4ai.action_server._selftest import ActionServerExitedError

    with pytest.raises(ActionServerExitedError):
        action_server_process.start(cwd=datadir / "pack_too_new", actions_sync=True)

    stderr = action_server_process.get_stderr()
    assert (
        "This version of the Action Server only supports `spec-version` `v1` or `v2`."
        in stderr
    )


@pytest.mark.integration_test
def test_package_yaml_structure_warn_spec_version(
    action_server_process: ActionServerProcess, datadir
):
    from action_server_tests.fixtures import BUILD_ENV_IN_TESTS_TIMEOUT

    action_server_process.start(
        cwd=datadir / "pack1", actions_sync=True, timeout=BUILD_ENV_IN_TESTS_TIMEOUT
    )
    stderr = action_server_process.get_stderr()
    assert (
        "The `pythonpath` entries in `package.yaml` are only supported in `spec-version: v2`"
        in stderr
    )
