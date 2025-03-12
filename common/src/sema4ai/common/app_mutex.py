import logging
import typing
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from sema4ai.common.system_mutex import SystemMutex


def obtain_app_mutex(
    *,
    kill_lock_holder: bool = False,
    data_dir: Path,
    lock_basename: str,
    app_name: str,
    timeout: int = 10,
    mutex_creation_kwargs: dict[str, Any] | None = None,
) -> "SystemMutex | None":
    """
    This function is used to obtain a mutex for the application.

    If the mutex is already acquired by another process, the current process will wait for the mutex to be released
    and if not available after the timeout, the function will return None.
        - If kill_lock_holder is True, the process holding the lock will be killed so that the new process can acquire the lock.

    If able to acquire the lock, the function will return a SystemMutex object (that must be kept alive until the process exits
    for the lock to be kept alive).

    Args:
        kill_lock_holder: If True, the process holding the lock will be killed so that the new process can acquire the lock.
        data_dir: The directory to store the lock file.
        lock_basename: The basename of the lock file. i.e.: "agent-server.lock"
        app_name: The name of the application (for logging purposes). i.e.: "Agent Server"
        timeout: The timeout to wait for the lock to be released.

    Returns:
        The SystemMutex object if the lock was acquired, None otherwise.
        Note: the SystemMutex object must be kept alive until the process exits (if it's released before
        the lock will be lost and a new process would be able to acquire it while this process is running).

    Usage:

        mutex = obtain_app_mutex(
            kill_lock_holder=True,
            data_dir=Path("."),
            lock_basename="agent-server.lock",
            app_name="Agent Server",
        )
        if mutex is None:
            sys.exit(1)

        ... # proceed to startup the app
    """
    import re
    import time

    from sema4ai.common.process import is_process_alive, kill_process_and_subprocesses
    from sema4ai.common.system_mutex import SystemMutex

    shown_first_message = False
    timeout_at = time.monotonic() + timeout

    while True:
        mutex = SystemMutex(
            lock_basename, base_dir=str(data_dir), **(mutex_creation_kwargs or {})
        )
        acquired = mutex.get_mutex_aquired()
        if acquired:
            if shown_first_message:
                log.info(
                    f"Process holding lock exited. Proceeding with {app_name} startup."
                )
            return mutex

        msg = mutex.mutex_creation_info or ""
        i = msg.find("--- Stack ---")
        if i > 0:
            msg = msg[:i]
        msg = msg.strip()

        # msg is something like:
        # f"PID: {os.getpid()}"

        if kill_lock_holder:
            # Extract the PID from the message using regex
            try:
                matched = re.search(r"PID: (\d+)", msg.splitlines()[0])
                if matched:
                    found = matched.group(1)
                    pid = int(found)
                else:
                    raise RuntimeError("PID not found in the lock file")
            except Exception:
                if not shown_first_message:
                    log.info(
                        f"PID not found in the lock file (unable to kill process holding lock). Lock file contents: {msg}"
                    )
            else:
                if is_process_alive(pid):
                    log.info(f"Killing process {pid} holding the lock file.")

                    kill_process_and_subprocesses(pid)

        if not shown_first_message:
            shown_first_message = True
            log.info(
                f"An {app_name} is already started in this datadir ({data_dir}).\n"
                f"\nInformation on mutex holder:\n"
                f"{msg}",
            )

        log.info("Waiting for it to exit...")
        time.sleep(0.3)

        timed_out = time.monotonic() > timeout_at
        if timed_out:
            log.critical(
                f"\n{app_name} not started (timed out waiting for mutex to be released).",
            )
            return None
