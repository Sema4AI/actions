import logging
import os
import sys
import threading
import time

log = logging.getLogger(__name__)

_track_pids_to_exit = {}
_watching_thread_global = None
PARENT_PROCESS_WATCH_INTERVAL = 2


def exit_when_pid_exits(pid: str | int, interval=PARENT_PROCESS_WATCH_INTERVAL) -> None:
    """
    Exit the current process when the given pid exists (may be called multiple times and if
    any of the pids we're tracking exit, the current process will exit).

    Args:
        pid: The pid of the process to watch.
        interval: The interval to check if the process is alive.
    """
    pid = int(pid)
    if pid:
        import psutil

        if pid not in _track_pids_to_exit:
            _track_pids_to_exit[pid] = psutil.Process(pid)
        global _watching_thread_global
        if _watching_thread_global is None:

            def watch_parent_process():
                # exit when any of the ids we're tracking exit.
                while True:
                    for p in tuple(_track_pids_to_exit.values()):
                        if not p.is_running():
                            # Note: just exit since the parent process already
                            # exited.
                            log.debug(
                                f"Force-quit process: {os.getpid()} because parent: {p.pid} exited"
                            )
                            _os_exit(0)

                    time.sleep(interval)

            _watching_thread_global = threading.Thread(
                target=watch_parent_process, args=()
            )
            _watching_thread_global.daemon = True
            _watching_thread_global.start()


# Keep old API (which has a typo).
exit_when_pid_exists = exit_when_pid_exits


def _os_exit(retcode: int) -> None:
    """
    Kills subprocesses and exits with the given returncode.
    """
    from sema4ai.common.process import kill_subprocesses

    try:
        kill_subprocesses()
        sys.stdout.flush()
        sys.stderr.flush()
        # Give some time for other threads to run just a little bit more.
        time.sleep(0.2)
    finally:
        os._exit(retcode)
