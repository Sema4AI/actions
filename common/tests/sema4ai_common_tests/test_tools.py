# import pytest
# pytestmark = pytest.mark.skipif(
#     True,
#     reason="Skipping all tests here for now (we don't want to run them all the time)",
# )
import pytest


def test_action_server_tool(tmpdir):
    import sys

    from sema4ai.common.tools import ActionServerTool

    suffix = ".exe" if sys.platform == "win32" else ""

    target = tmpdir / f"action_server{suffix}"

    # See: https://github.com/Sema4AI/actions/blob/master/action_server/docs/CHANGELOG.md for versions
    tool = ActionServerTool(target, "2.5.1")
    assert not tool.verify()
    tool.download()
    assert tool.verify()

    target = tmpdir / "action_server-in_mac_arm"
    tool = ActionServerTool(target, "2.5.1")
    tool.force_sys_platform = "darwin"
    tool.force_machine = "arm64"
    tool.make_run_check = False
    tool.download()
    assert tool.verify()

    executable = ActionServerTool.get_default_executable(version="2.5.1", download=True)
    assert executable.exists()
    assert executable.is_file()


@pytest.fixture(autouse=True)
def setup_logging():
    import logging

    logger = logging.getLogger("sema4ai.common.tools")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    yield
    logger.removeHandler(handler)


def test_agent_cli_tool(tmpdir):
    import sys

    from sema4ai.common.tools import AgentCliTool

    suffix = ".exe" if sys.platform == "win32" else ""

    target = tmpdir / f"agent-cli{suffix}"

    # See: https://github.com/Sema4AI/agents-spec/blob/master/cli/common/version.go for versions
    tool = AgentCliTool(target, "v1.0.2")
    assert not tool.verify()
    tool.download()
    assert tool.verify()

    executable = AgentCliTool.get_default_executable(version="v1.0.2", download=True)
    assert executable.exists()
    assert executable.is_file()


def test_rcc_tool(tmpdir):
    import sys

    from sema4ai.common.tools import RccTool

    suffix = ".exe" if sys.platform == "win32" else ""

    target = tmpdir / f"rcc{suffix}"

    # Using joshyorko/rcc version (see: https://github.com/joshyorko/rcc/releases)
    tool = RccTool(target, "v18.13.1")
    assert not tool.verify()
    tool.download()
    assert tool.verify()

    target = tmpdir / "rcc-in_mac_arm"
    tool = RccTool(target, "v18.13.1")
    tool.force_sys_platform = "darwin"
    tool.force_machine = "arm64"
    tool.make_run_check = False
    tool.download()
    assert tool.verify()

    executable = RccTool.get_default_executable(version="v18.13.1", download=True)
    assert executable.exists()
    assert executable.is_file()


def test_data_server_tool(tmpdir):
    import sys

    from sema4ai.common.tools import DataServerTool

    suffix = ".exe" if sys.platform == "win32" else ""

    target = tmpdir / f"data-server-cli{suffix}"

    tool = DataServerTool(target, "v1.0.2")
    assert not tool.verify()
    tool.download()
    assert tool.verify()

    target = tmpdir / "data_server-in_mac_arm"
    tool = DataServerTool(target, "v1.0.2")
    tool.force_sys_platform = "darwin"
    tool.force_machine = "arm64"
    tool.make_run_check = False
    tool.download()
    assert tool.verify()

    executable = DataServerTool.get_default_executable(version="v1.0.2", download=True)
    assert executable.exists()
    assert executable.is_file()
