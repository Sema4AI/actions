import logging
import os
import subprocess
import sys
import threading
import time

log = logging.getLogger(__name__)

_track_pids_to_exit = set()
_watching_thread_global = None
PARENT_PROCESS_WATCH_INTERVAL = 2


if sys.platform == "win32":
    import ctypes

    kernel32 = ctypes.windll.kernel32
    PROCESS_SYNCHRONIZE = 0x00100000
    DWORD = ctypes.c_uint32
    BOOL = ctypes.c_int
    LPVOID = ctypes.c_void_p
    HANDLE = LPVOID

    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [DWORD, BOOL, DWORD]
    OpenProcess.restype = HANDLE

    WaitForSingleObject = kernel32.WaitForSingleObject
    WaitForSingleObject.argtypes = [HANDLE, DWORD]
    WaitForSingleObject.restype = DWORD

    WAIT_TIMEOUT = 0x00000102
    WAIT_ABANDONED = 0x00000080
    WAIT_OBJECT_0 = 0
    WAIT_FAILED = 0xFFFFFFFF

    def is_process_alive(pid):
        """Check whether the process with the given pid is still alive.

        Running `os.kill()` on Windows always exits the process, so it can't be used to
        check for an alive process.
        see: https://docs.python.org/3/library/os.html?highlight=os%20kill#os.kill

        Hence ctypes is used to check for the process directly via windows API avoiding
        any other 3rd-party dependency.

        Args:
            pid (int): process ID

        Returns:
            bool: False if the process is not alive or don't have permission to check,
            True otherwise.
        """
        process = OpenProcess(PROCESS_SYNCHRONIZE, 0, pid)
        if process != 0:
            try:
                wait_result = WaitForSingleObject(process, 0)
                if wait_result == WAIT_TIMEOUT:
                    return True
            finally:
                kernel32.CloseHandle(process)
        return False

else:
    import errno

    def _is_process_alive(pid):
        """Check whether the process with the given pid is still alive.

        Args:
            pid (int): process ID

        Returns:
            bool: False if the process is not alive or don't have permission to check,
            True otherwise.
        """
        if pid < 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError as e:
            if e.errno == errno.ESRCH:
                return False  # No such process.
            elif e.errno == errno.EPERM:
                return True  # permission denied.
            else:
                log.info("Unexpected errno: %s", e.errno)
                return False
        else:
            return True

    def is_process_alive(pid):
        if _is_process_alive(pid):
            # Check if zombie...
            try:
                cmd = ["ps", "-p", str(pid), "-o", "stat"]
                try:
                    process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                except Exception:
                    log.exception("Error calling: %s.", " ".join(cmd))
                else:
                    stdout, _ = process.communicate()
                    stdout = stdout.decode("utf-8", "replace")
                    lines = [line.strip() for line in stdout.splitlines()]
                    if len(lines) > 1:
                        if lines[1].startswith("Z"):
                            return False  # It's a zombie
            except Exception:
                log.exception("Error checking if process is alive.")

            return True
        return False


def exit_when_pid_exists(pid: str | int, interval=PARENT_PROCESS_WATCH_INTERVAL):
    pid = int(pid)
    if pid:
        _track_pids_to_exit.add(pid)
        global _watching_thread_global
        if _watching_thread_global is None:

            def watch_parent_process():
                # exit when any of the ids we're tracking exit.
                while True:
                    for pid in _track_pids_to_exit:
                        if not is_process_alive(pid):
                            # Note: just exit since the parent process already
                            # exited.
                            log.debug(
                                f"Force-quit process: {os.getpid()} because parent: {pid} exited"
                            )
                            _os_exit(0)

                    time.sleep(interval)

            _watching_thread_global = threading.Thread(
                target=watch_parent_process, args=()
            )
            _watching_thread_global.daemon = True
            _watching_thread_global.start()


def _os_exit(retcode: int):
    """
    Kills subprocesses and exits with the given returncode.
    """
    from robocorp import log

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
                psutil.wait_procs(alive, 5)
        except Exception as e:
            log.debug(f"Exception when listing/killing processes: {e}")

        sys.stdout.flush()
        sys.stderr.flush()
        # Give some time for other threads to run just a little bit more.
        time.sleep(0.2)
    finally:
        os._exit(retcode)
