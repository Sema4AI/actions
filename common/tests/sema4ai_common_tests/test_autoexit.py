def test_exit_when_pid_exists():
    import sys
    import time

    from sema4ai.common.process import Process
    from sema4ai.common.wait_for import wait_for_condition

    # Create the first process that will run indefinitely
    target_process = Process(["python", "-c", "import time; time.sleep(100000)"])
    target_process.start()
    wait_for_condition(lambda: target_process.is_alive())

    # Create the second process that will watch the first one
    args = [
        sys.executable,
        "-c",
        f"from sema4ai.common.autoexit import exit_when_pid_exits; exit_when_pid_exits({target_process.pid}); import time; time.sleep(100000)",
    ]
    watcher_process = Process(args=args)
    import io

    stream = io.StringIO()
    watcher_process.stream_to(stream)
    watcher_process.start()
    try:
        wait_for_condition(
            lambda: watcher_process.is_alive(),
            timeout=15,
            msg=lambda: f"Watcher process was not created in time. Output:\n{stream.getvalue()}",
        )

        # Just wait a bit to make sure that we don't kill before the pid to track is killed.
        time.sleep(0.2)
        assert target_process.is_alive()
        assert watcher_process.is_alive()

        # Kill the target process
        target_process.stop()

        wait_for_condition(lambda: not watcher_process.is_alive(), timeout=15)

        # Verify the watcher process has exited
        assert not watcher_process.is_alive()

    except Exception as e:
        raise RuntimeError("Test failed. Output:\n" + stream.getvalue()) from e

    finally:
        # Cleanup processes if they're still running
        for p in [target_process, watcher_process]:
            if p.is_alive():
                p.stop()
