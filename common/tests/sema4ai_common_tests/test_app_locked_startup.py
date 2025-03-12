def test_obtain_app_mutex(tmpdir):
    import sys
    from pathlib import Path

    from sema4ai.common.app_mutex import obtain_app_mutex
    from sema4ai.common.process import Process
    from sema4ai.common.wait_for import wait_for_expected_func_return

    lock_basename = "test_app_locked_startup.lock"
    mutex = obtain_app_mutex(
        kill_lock_holder=True,
        data_dir=Path(tmpdir),
        lock_basename=lock_basename,
        app_name="Test App",
        timeout=5,
    )

    assert mutex is not None

    mutex2 = obtain_app_mutex(
        kill_lock_holder=False,
        data_dir=Path(tmpdir),
        lock_basename=lock_basename,
        app_name="Test App",
        timeout=0.4,
        mutex_creation_kwargs={"check_reentrant": False},
    )
    assert mutex2 is None

    del mutex
    mutex2 = obtain_app_mutex(
        kill_lock_holder=False,
        data_dir=Path(tmpdir),
        lock_basename=lock_basename,
        app_name="Test App",
        timeout=2,
        mutex_creation_kwargs={"check_reentrant": False},
    )
    assert mutex2 is not None
    del mutex2

    # Now, create a separate process that holds the lock

    code = f"""
from sema4ai.common.app_mutex import obtain_app_mutex
from pathlib import Path
import os
import sys
mutex = obtain_app_mutex(
    kill_lock_holder=False,
    data_dir=Path({str(tmpdir)!r}),
    lock_basename={str(lock_basename)!r},
    app_name="Test App",
    timeout=2,
)

assert mutex is not None, "Mutex should be obtained!"
print(f'Current process PID: ' + str(os.getpid()) + '\\n')
sys.stdout.flush()
import time
time.sleep(100)
"""

    cmdline = [sys.executable, "-c", code]
    process_holding_lock = Process(cmdline)
    try:
        import io

        output = io.StringIO()
        pid_line = None

        def on_output(line):
            nonlocal pid_line
            if line.startswith("Current process PID: "):
                pid_line = line
            output.write(line)

        process_holding_lock.on_stdout.register(on_output)
        process_holding_lock.on_stderr.register(on_output)
        process_holding_lock.start()

        def other_process_has_mutex():
            import os

            if pid_line is None:
                return "Waiting for PID line. Found output:\n" + output.getvalue()

            other_process_pid = int(pid_line.split(":")[1].strip())

            lock_file = Path(tmpdir) / lock_basename
            if not lock_file.exists():
                return f"Lock file does not exist: {lock_file!r}"

            if not process_holding_lock.is_alive():
                return f"The other process should not have exited yet! PID: {other_process_pid}"

            contents = lock_file.read_text()
            if f"PID: {other_process_pid}" in contents:
                return True
            return f"Waiting for PID: {other_process_pid} to be in the lock file contents:\n{contents!r}\nCurrent process PID: {os.getpid()}"

        # Mutex must not be gotten once (so that we know the other process is holding it)
        wait_for_expected_func_return(other_process_has_mutex, True, timeout=10)
        assert process_holding_lock.is_alive()

        mutex = obtain_app_mutex(
            kill_lock_holder=True,
            data_dir=Path(tmpdir),
            lock_basename=lock_basename,
            app_name="Test App",
            timeout=5,
            mutex_creation_kwargs={"check_reentrant": False},
        )
        assert mutex is not None, "Error: did not kill the process with the mutex!"

        assert (
            not process_holding_lock.is_alive()
        ), "Expected the other process to be killed at this point!"
    finally:
        process_holding_lock.stop()
