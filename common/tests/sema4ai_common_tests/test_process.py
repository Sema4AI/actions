import pytest


def test_process_is_process_alive():
    import os

    from sema4ai.common.process import is_process_alive

    assert is_process_alive(os.getpid())


def test_process_start():
    import sys

    from sema4ai.common.process import Process
    from sema4ai.common.wait_for import wait_for_condition

    p = Process([sys.executable, "-c", "import time; time.sleep(20);print(20)"])
    p.start()
    assert p.is_alive()
    assert p.returncode is None
    p.stop()
    wait_for_condition(lambda: not p.is_alive(), timeout=2)
    assert p.returncode is not None


@pytest.mark.parametrize(
    "scenario",
    [
        "monitor",
        "future",
        "timeout",
    ],
)
def test_launch_and_return_future(scenario):
    import sys
    from concurrent.futures import CancelledError, TimeoutError

    from sema4ai.common.monitor import Monitor
    from sema4ai.common.process import ProcessResultStatus, launch_and_return_future
    from sema4ai.common.wait_for import wait_for_condition

    code = """
import time
while True:
    time.sleep(1)
"""
    monitor = Monitor()
    future = launch_and_return_future(
        [sys.executable, "-c", code],
        environ={},
        cwd=".",
        monitor=monitor,
        timeout=1 if scenario == "timeout" else 30,
    )

    with pytest.raises(TimeoutError):
        future.result(0.1 if scenario == "timeout" else 1)

    if scenario == "monitor":
        monitor.cancel()
        result = future.result(1)
        assert result.returncode is not None
        assert result.status == ProcessResultStatus.CANCELLED
    elif scenario == "future":
        future.cancel()
        with pytest.raises(CancelledError):
            future.result(1)
    elif scenario == "timeout":
        result = future.result()
        assert result.returncode is not None
        assert result.status == ProcessResultStatus.TIMED_OUT
    else:
        raise ValueError(f"Invalid scenario: {scenario}")

    process = future._process_weak_ref()
    wait_for_condition(lambda: process.poll() is not None)
