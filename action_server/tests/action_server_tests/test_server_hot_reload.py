import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


@pytest.mark.integration_test
def test_server_hot_reload(
    action_server_process: ActionServerProcess, client: ActionServerClient, tmpdir
) -> None:
    from pathlib import Path

    from action_server_tests.fixtures import run_async_in_new_thread
    from devutils.fixtures import wait_for_non_error_condition

    calculator = Path(tmpdir) / "calculator" / "action_calculator.py"
    calculator.parent.mkdir(parents=True, exist_ok=True)
    calculator.write_text(
        """
from sema4ai.actions import action

@action
def calculator_sum(v1: float, v2: float) -> float:
    return v1 + v2
"""
    )

    action_server_process.start(
        actions_sync=True,
        cwd=Path(tmpdir / "calculator"),
        db_file="server.db",
        additional_args=["--auto-reload"],
    )
    found = client.post_get_str(
        "api/actions/calculator/calculator-sum/run", {"v1": 1.0, "v2": 2.0}
    )
    assert float(found) == 1.0 + 2.0

    async def check_mcp_tools():
        async with action_server_process.mcp_client("mcp") as mcp_session:
            tools_result = await mcp_session.list_tools()
            tools_list = tools_result.tools
            assert len(tools_list) == 1
            assert tools_list[0].name == "calculator_sum", (
                "Expected calculator_sum. Found: " + str(tools_list[0].name)
            )

    run_async_in_new_thread(check_mcp_tools)

    # Change file.
    calculator.write_text(
        """
from sema4ai.actions import action


@action
def calculator_subtract(v1: float, v2: float) -> float:
    return v1 - v2
"""
    )

    def check_reloaded():
        found = client.post_get_str(
            "api/actions/calculator/calculator-subtract/run", {"v1": 1.0, "v2": 2.0}
        )
        assert float(found) == 1.0 - 2.0

    wait_for_non_error_condition(check_reloaded)

    async def check_mcp_tools_after_reload():
        async with action_server_process.mcp_client("mcp") as mcp_session:
            tools_result = await mcp_session.list_tools()
            tools_list = tools_result.tools
            assert len(tools_list) == 1, "Expected 1 tool. Found: " + str(tools_list)
            assert tools_list[0].name == "calculator_subtract", (
                "Expected calculator_subtract. Found: " + str(tools_list[0].name)
            )

    run_async_in_new_thread(check_mcp_tools_after_reload)
