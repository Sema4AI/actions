import logging
import os
import sys
import threading
import time

log = logging.getLogger(__name__)

_track_pids_to_exit = {}
_watching_thread_global = None
PARENT_PROCESS_WATCH_INTERVAL = 2


def exit_when_pid_exists(
    pid: str | int, interval=PARENT_PROCESS_WATCH_INTERVAL
) -> None:
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


def _os_exit(retcode: int) -> None:
    """
    Kills subprocesses and exits with the given returncode.
    """
    try:
        import psutil

        curr_process = psutil.Process()
        try:
            try:
                children_processes = list(curr_process.children(recursive=True))
            except Exception:
                # Retry once
                children_processes = list(curr_process.children(recursive=True))

            try:
                names = ",".join(f"{x.name()} (x.pid)" for x in children_processes)
            except Exception as e:
                log.debug(f"Exception when collecting process names: {e}")
                names = "<unable to get>"

            log.info(f"sema4ai-action-server killing processes after run: {names}")
            for p in children_processes:
                try:
                    p.kill()
                except Exception as e:
                    log.debug(f"Exception when terminating process: {p.pid}: {e}")

            # Give processes 2 seconds to exit cleanly and force-kill afterwards
            _gone, alive = psutil.wait_procs(children_processes, 2)
            for p in alive:
                try:
                    p.terminate()
                except Exception as e:
                    # Expected: process no longer exists.
                    log.debug(f"Exception when killing process: {p.pid}: {e}")
            # Wait a bit more after terminate.
            psutil.wait_procs(alive, 2)
        except Exception as e:
            log.debug(f"Exception when listing/killing processes: {e}")

        sys.stdout.flush()
        sys.stderr.flush()
        # Give some time for other threads to run just a little bit more.
        time.sleep(0.2)
    finally:
        os._exit(retcode)
