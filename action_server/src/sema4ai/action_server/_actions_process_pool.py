import itertools
import json
import logging
import socket as socket_module
import subprocess
import sys
import threading
from collections import namedtuple
from contextlib import contextmanager
from pathlib import Path
from queue import Queue
from typing import Dict, Generator, Iterator, List, Optional, Set

from sema4ai.actions._action_context import ActionContext
from termcolor import colored

from sema4ai.action_server._models import Action, ActionPackage, Run
from sema4ai.action_server._protocols import JSONValue

from ._settings import Settings, is_frozen

log = logging.getLogger(__name__)

AF_INET, SOCK_STREAM, SHUT_WR, SOL_SOCKET, SO_REUSEADDR, IPPROTO_TCP, socket = (
    socket_module.AF_INET,
    socket_module.SOCK_STREAM,
    socket_module.SHUT_WR,
    socket_module.SOL_SOCKET,
    socket_module.SO_REUSEADDR,
    socket_module.IPPROTO_TCP,
    socket_module.socket,
)

if sys.platform == "win32":
    SO_EXCLUSIVEADDRUSE = socket_module.SO_EXCLUSIVEADDRUSE  # noqa

_Key = namedtuple("_Key", "action_package_id, env, cwd")


def _create_server_socket(host: str, port: int):
    try:
        server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        if sys.platform == "win32":
            server.setsockopt(SOL_SOCKET, SO_EXCLUSIVEADDRUSE, 1)
        else:
            server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        server.bind((host, port))
        server.settimeout(None)
    except Exception:
        server.close()
        raise

    return server


def _connect_to_socket(host, port):
    """connects to a host/port"""

    s = socket(AF_INET, SOCK_STREAM)

    #  Set TCP keepalive on an open socket.
    #  It activates after 1 second (TCP_KEEPIDLE,) of idleness,
    #  then sends a keepalive ping once every 3 seconds (TCP_KEEPINTVL),
    #  and closes the connection after 5 failed ping (TCP_KEEPCNT), or 15 seconds
    try:
        s.setsockopt(SOL_SOCKET, socket_module.SO_KEEPALIVE, 1)
    except (AttributeError, OSError):
        pass  # May not be available everywhere.
    try:
        s.setsockopt(socket_module.IPPROTO_TCP, socket_module.TCP_KEEPIDLE, 1)  # noqa
    except (AttributeError, OSError):
        pass  # May not be available everywhere.
    try:
        s.setsockopt(socket_module.IPPROTO_TCP, socket_module.TCP_KEEPINTVL, 3)
    except (AttributeError, OSError):
        pass  # May not be available everywhere.
    try:
        s.setsockopt(socket_module.IPPROTO_TCP, socket_module.TCP_KEEPCNT, 5)
    except (AttributeError, OSError):
        pass  # May not be available everywhere.

    timeout = 20
    s.settimeout(timeout)
    s.connect((host, port))
    s.settimeout(None)  # no timeout after connected
    return s


class ProcessHandle:
    def __init__(
        self,
        settings: Settings,
        action_package: ActionPackage,
        post_run_args: Optional[tuple[str, ...]],
    ):
        from sema4ai.action_server._preload_actions.preload_actions_streams import (
            JsonRpcStreamWriter,
        )
        from sema4ai.action_server._robo_utils.callback import Callback
        from sema4ai.action_server._robo_utils.run_in_thread import run_in_thread

        from ._actions_run_helpers import (
            _add_preload_actions_dir_to_env_pythonpath,
            get_action_package_cwd,
        )
        from ._preload_actions.preload_actions_streams import JsonRpcStreamReaderThread
        from ._robo_utils.process import build_python_launch_env

        self._post_run_args = post_run_args

        # If kill was internally called, we'll just check it instead of waiting for
        # the process to exit when is_alive() is called.
        self._kill_called = False

        self.key = _get_process_handle_key(settings, action_package)

        # The can_reuse flag is used to notify whether this process can be reused
        # (upon reloading all running processes are marked as non-reusable).
        self.can_reuse = True

        env = json.loads(action_package.env_json)
        _add_preload_actions_dir_to_env_pythonpath(env)
        env = build_python_launch_env(env)
        # Shouldn't be there, but just making sure... if it is it can
        # affect how the logs are generated and if wrong the logs would
        # also be wrong.
        env.pop("ROBOT_ROOT", None)

        if settings.reuse_processes:
            # When reusing processes we don't want to dump threads if
            # the process doesn't exit!
            env["RC_DUMP_THREADS_AFTER_RUN"] = "0"

        if "PYTHON_EXE" in env:
            python_exe = env["PYTHON_EXE"]
        else:
            if is_frozen():
                log.critical(
                    f"Unable to create process for action package: {action_package} "
                    "(environment does not contain PYTHON_EXE)."
                )
                return

            python_exe = sys.executable

        # stdin/stdout is no longer an option because numpy gets halted
        # if stdin is being read while importing numpy.
        # https://github.com/numpy/numpy/issues/24290
        # https://github.com/robocorp/robocorp/issues/271
        use_tcp = True

        cwd = get_action_package_cwd(settings, action_package)
        subprocess_kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        self._cwd: str = str(cwd)

        def _process_stream_reader(stderr_or_stdout):
            while True:
                line_bytes = stderr_or_stdout.readline()
                if not line_bytes:
                    break
                line_as_str = line_bytes.decode("utf-8", "replace")
                print(
                    colored(f"output (pid: {pid}): ", attrs=["dark"])
                    + f"{line_as_str.strip()}\n",
                    end="",
                )
                self._on_output(line_bytes)

        self._read_queue: "Queue[dict]" = Queue()

        if use_tcp:
            server_socket = _create_server_socket("127.0.0.1", 0)
            host, port = server_socket.getsockname()
            cmdline = [
                python_exe,
                "-m",
                "preload_actions_server_main",
                "--tcp",
                f"--host={host}",
                f"--port={port}",
            ]

            def accept_connection():
                server_socket.listen(1)
                sock, _addr = server_socket.accept()
                return sock

            connection_future = run_in_thread(accept_connection)

            self._process = subprocess.Popen(cmdline, **subprocess_kwargs)
            self._on_output = Callback()

            pid = self._process.pid

            stderr = self._process.stderr
            stdout = self._process.stdout

            t = threading.Thread(
                target=_process_stream_reader, args=(stderr,), daemon=True
            )
            t.name = f"Stderr reader (pid: {pid})"
            t.start()

            t = threading.Thread(
                target=_process_stream_reader, args=(stdout,), daemon=True
            )
            t.name = f"Stdout reader (pid: {pid})"
            t.start()

            try:
                s = connection_future.result(10)
            except Exception:
                log.exception(
                    "Process that runs action did not connect back in the available timeout."
                )
                raise
            read_from = s.makefile("rb")
            write_to = s.makefile("wb")

            self._writer = JsonRpcStreamWriter(write_to, sort_keys=True)
            self._reader = JsonRpcStreamReaderThread(
                read_from, self._read_queue, lambda *args, **kwargs: None
            )
        else:
            # Will start things using the stdin/stdout for communicating.
            cmdline = [
                python_exe,
                "-m",
                "preload_actions_server_main",
            ]
            subprocess_kwargs["stdin"] = subprocess.PIPE

            self._process = subprocess.Popen(cmdline, **subprocess_kwargs)
            self._on_output = Callback()

            pid = self._process.pid

            stderr = self._process.stderr
            t = threading.Thread(target=_process_stream_reader, args=(stderr,))
            t.name = f"Stderr reader (pid: {pid})"
            t.start()

            write_to = self._process.stdin
            read_from = self._process.stdout
            self._writer = JsonRpcStreamWriter(write_to, sort_keys=True)
            self._reader = JsonRpcStreamReaderThread(
                read_from, self._read_queue, lambda *args, **kwargs: None
            )
        self._reader.start()

    @property
    def pid(self):
        return self._process.pid

    @property
    def cwd(self) -> str:
        return self._cwd

    def is_alive(self) -> bool:
        if self._kill_called:
            return False

        from ._robo_utils.process import is_process_alive

        if self._process.poll() is not None:
            return False

        return is_process_alive(self._process.pid)

    def kill(self) -> None:
        from ._robo_utils.process import kill_process_and_subprocesses

        if not self.is_alive():
            return

        self._kill_called = True

        log.debug("Subprocess kill [pid=%s]", self._process.pid)
        kill_process_and_subprocesses(self._process.pid)

    def _do_run_action(
        self,
        run: Run,
        action_package: ActionPackage,
        action: Action,
        input_json: Path,
        run_artifacts_dir: Path,
        result_json: Path,
        headers: dict,
        cookies: dict,
        reuse_process: bool,
    ) -> int:
        from sema4ai.action_server._api_oauth2 import (
            get_resolved_provider_settings,
            refresh_tokens,
        )
        from sema4ai.action_server._api_secrets import IN_MEMORY_SECRETS
        from sema4ai.action_server._encryption import (
            decrypt_simple,
            get_encryption_keys,
            make_encrypted_data_envelope,
            make_unencrypted_data_envelope,
        )
        from sema4ai.action_server._models import OAuth2UserData, get_db
        from sema4ai.action_server._user_session import (
            COOKIE_SESSION_ID,
            get_user_session_from_id,
        )

        headers = IN_MEMORY_SECRETS.update_headers(action_package, action, headers)

        x_action_context_key = "x-action-context"
        x_action_context = headers.get(x_action_context_key)

        initial_action_context_value: Optional[JSONValue] = None
        if x_action_context:
            action_context = ActionContext(x_action_context)
            initial_action_context_value = action_context.value

        session_id = cookies.get(COOKIE_SESSION_ID)
        if session_id:
            db = get_db()
            with db.connect():
                user_session = get_user_session_from_id(session_id, db)
                if user_session:
                    # Verify whether we need to add OAuth2 secrets from the current
                    # user session.
                    where, values = db.where_from_dict({"user_session_id": session_id})

                    required_providers = set()

                    param_name_to_provider: dict[str, str] = {}
                    managed_params_schema = action.managed_params_schema
                    if managed_params_schema:
                        loaded = json.loads(managed_params_schema)
                        for param_name, param_info in loaded.items():
                            if param_info.get("type") == "OAuth2Secret":
                                provider = param_info.get("provider")
                                if provider:
                                    param_name_to_provider[param_name] = provider
                                    required_providers.add(provider)

                    # Note: if it's not there it's not a blocker (it may've
                    # been passed in the x-action-context header or in the
                    # input json).
                    provider_to_access_data: dict[str, OAuth2UserData] = {}
                    for user_data in db.all(OAuth2UserData, where=where, values=values):
                        if user_data.provider in required_providers:
                            provider_to_access_data[user_data.provider] = user_data

                    # Now that we have the information needed, refresh it.
                    if provider_to_access_data:
                        new_oauth2_data = refresh_tokens(
                            session_id, provider_to_access_data.values()
                        )
                        provider_to_access_data = dict(
                            (d.provider, d) for d in new_oauth2_data
                        )

                        data = {}

                        if initial_action_context_value and isinstance(
                            initial_action_context_value, dict
                        ):
                            data.update(initial_action_context_value)

                        for param_name, provider in param_name_to_provider.items():
                            access_data = provider_to_access_data.get(provider)
                            if access_data and access_data.access_token:
                                try:
                                    access_token = decrypt_simple(
                                        access_data.access_token
                                    )
                                except Exception:
                                    log.critical(
                                        "It was not possible to decrypt the access token, secrets won't be sent"
                                        "(the storage key has probably changed, so, a new login will be needed)."
                                    )
                                else:
                                    settings = get_resolved_provider_settings(provider)
                                    # i.e.: if it's not there, don't add it, let the
                                    # action itself fail and provide the needed info.
                                    metadata: dict[str, JSONValue] = {}
                                    if settings.server:
                                        # Always pass the server if it's available.
                                        metadata["server"] = settings.server
                                    ctx = data.setdefault("secrets", {})

                                    if not isinstance(ctx, dict):
                                        log.critical(
                                            "The value for 'secrets' is not a dictionary, overwriting!"
                                        )
                                        ctx = data["secrets"] = {}

                                    ctx[param_name] = {
                                        "provider": provider,
                                        "access_token": access_token,
                                        "metadata": metadata,
                                    }

                        # No context passed: create one now
                        keys = get_encryption_keys()
                        if keys:
                            # Data must be filled as:
                            # "my_oauth2_secret": {
                            #   "provider": "google",
                            #   "scopes": ["scope1", "scope2"],
                            #   "access_token": "<this-is-the-access-token>",
                            #   "metadata": { "any": "additional info" }
                            # }
                            header_value = make_encrypted_data_envelope(keys[0], data)
                        else:
                            header_value = make_unencrypted_data_envelope(data)

                        headers[x_action_context_key] = header_value

        msg = {
            "command": "run_action",
            "action_name": action.name,
            "action_file": f"{action.file}",
            "input_json": f"{input_json}",
            "robot_artifacts": f"{run_artifacts_dir}",
            "result_json": f"{result_json}",
            "headers": headers,
            "cookies": cookies,
            "reuse_process": reuse_process,
            "cwd": self._cwd,
        }
        self._writer.write(msg)

        queue = self._read_queue

        result_msg = queue.get(block=True)
        if result_msg is None:
            # This means that the process was actually killed (or crashed).
            result_msg = {"returncode": 77}

        if self._post_run_args:
            log.debug("Calling post run command.")
            try:
                self._call_post_run_script(
                    self._post_run_args,
                    initial_action_context_value,
                    msg,
                    run,
                )
            except Exception:
                log.exception("Error runnnig post run command.")
        else:
            log.debug("Not running post run command.")
        return result_msg["returncode"]

    def _call_post_run_script(
        self,
        post_run_args: tuple[str, ...],
        initial_action_context_value: Optional[JSONValue],
        msg: dict,
        run: Run,
    ) -> None:
        import shlex
        from string import Template

        from sema4ai.action_server._robo_utils import process, run_in_thread
        from sema4ai.action_server._robo_utils.process import build_python_launch_env
        from sema4ai.action_server._settings import get_settings

        settings = get_settings()

        mapping = {
            "base_artifacts_dir": settings.artifacts_dir,
            "run_id": run.id,
            "run_artifacts_dir": msg["robot_artifacts"],
            "action_name": msg["action_name"],
        }
        if isinstance(initial_action_context_value, dict):
            invocation_context = initial_action_context_value.get("invocation_context")
            if isinstance(invocation_context, dict):
                for key, value in invocation_context.items():
                    if isinstance(value, str):
                        mapping[key] = value

        use_args = []
        for arg in post_run_args:
            try:
                use_args.append(Template(arg).substitute(mapping))
            except Exception:
                error_msg = f"Error substituting {arg!r} in post run command."
                log.exception(error_msg)
                raise RuntimeError(error_msg)  # We can't proceed!

        # Run but don't wait for it!
        try:
            cwd = None
            mapping_as_env_vars = {
                f"SEMA4AI_ACTION_SERVER_POST_RUN_{k.upper()}": f"{v}"
                for k, v in mapping.items()
            }
            env = build_python_launch_env(mapping_as_env_vars)

            def run_post_run_command_in_thread():
                try:
                    # Note: should log when starting automatically.
                    p = process.Process(use_args, cwd=cwd, env=env)
                    p.start()
                    p.join()
                    if p.returncode != 0:
                        log.error(
                            "Post run command return code is: %s (full command: %s)",
                            p.returncode,
                            shlex.join(use_args),
                        )
                    else:
                        log.debug("Post run command finished successfuly.")
                except Exception:
                    log.exception("Error in post run command.")

            run_in_thread.run_in_thread(run_post_run_command_in_thread)

        except Exception:
            log.exception(f"Error running: {use_args!r}")

    def run_action(
        self,
        run: Run,
        action_package: ActionPackage,
        action: Action,
        input_json: Path,
        run_artifacts_dir: Path,
        output_file: Path,
        result_json: Path,
        headers: dict,
        cookies: dict,
        reuse_process: bool,
    ) -> int:
        """
        Runs the action and returns the returncode from running the action.

        (returncode=0 means everything is Ok).
        """
        with output_file.open("wb") as stream:

            def on_output(line_bytes: bytes):
                stream.write(line_bytes)

            with self._on_output.register(on_output):
                # stdout is now used for communicating, so, don't hear on it.
                returncode = self._do_run_action(
                    run,
                    action_package,
                    action,
                    input_json,
                    run_artifacts_dir,
                    result_json,
                    headers,
                    cookies,
                    reuse_process,
                )
                return returncode


def _get_process_handle_key(settings: Settings, action_package: ActionPackage) -> _Key:
    """
    Given an action provides a key where the key identifies whether a
    given action can be run at a given ProcessHandle.
    """
    from ._actions_run_helpers import get_action_package_cwd

    env = tuple(sorted(json.loads(action_package.env_json).items()))
    cwd = get_action_package_cwd(settings, action_package)
    return _Key(action_package.id, env, cwd)


class ActionsProcessPool:
    def __init__(
        self,
        settings: Settings,
        action_package_id_to_action_package: Dict[str, ActionPackage],
        actions: List[Action],
    ):
        import os
        import shlex

        self._settings = settings
        self.action_package_id_to_action_package = action_package_id_to_action_package

        post_run_cmd = os.environ.get("SEMA4AI_ACTION_SERVER_POST_RUN_CMD")
        if not post_run_cmd:
            log.debug(
                "SEMA4AI_ACTION_SERVER_POST_RUN_CMD not set (post run will be skipped)."
            )
            self._post_run_cmd_args = None
        else:
            log.debug("SEMA4AI_ACTION_SERVER_POST_RUN_CMD set to: '%s'", post_run_cmd)
            try:
                post_run_cmd_args = shlex.split(post_run_cmd)
            except Exception:
                error_msg = f"Error. Unable to parse SEMA4AI_ACTION_SERVER_POST_RUN_CMD: '{post_run_cmd}' with shlex."
                log.exception(error_msg)
                raise RuntimeError(error_msg)

            self._post_run_cmd_args = tuple(post_run_cmd_args)

        # We just want the actions which are enabled.
        self.actions = [action for action in actions if action.enabled]

        # An iterator which keeps cycling over the actions.
        self._cycle_actions_iterator = itertools.cycle(self.actions)

        self._lock = threading.Lock()
        self._running_processes: Dict[_Key, Set[ProcessHandle]] = {}
        self._idle_processes: Dict[_Key, Set[ProcessHandle]] = {}

        # Semaphore used to track running processes.
        self._processes_running_semaphore = threading.Semaphore(self.max_processes)

        self._warmup_processes()

    def on_reload(
        self,
        action_package_id_to_action_package: Dict[str, ActionPackage],
        actions: List[Action],
    ):
        """
        On a reload, we need to kill all the related, idle processes and mark
        any running process as non-reusable.
        """
        with self._lock:
            for key, idle_processes in tuple(self._idle_processes.items()):
                for process in idle_processes:
                    process.kill()
                self._idle_processes.pop(key)

            for key, running_processes in tuple(self._running_processes.items()):
                for process in running_processes:
                    process.can_reuse = False

            self.action_package_id_to_action_package = (
                action_package_id_to_action_package
            )

            # We just want the actions which are enabled.
            self.actions = [action for action in actions if action.enabled]

            # An iterator which keeps cycling over the actions.
            self._cycle_actions_iterator = itertools.cycle(self.actions)

        self._warmup_processes()

    @property
    def _reuse_processes(self) -> bool:
        """
        Returns:
            Whether processes can be reused.
        """
        return self._settings.reuse_processes

    @property
    def max_processes(self) -> int:
        """
        Returns:
            The maximum number of processes that may be created by the process
            pool.
        """
        return self._settings.max_processes

    @property
    def min_processes(self) -> int:
        return self._settings.min_processes

    def _create_process(self, action: Action):
        action_package: ActionPackage = self.action_package_id_to_action_package[
            action.action_package_id
        ]

        process_handle = ProcessHandle(
            self._settings, action_package, self._post_run_cmd_args
        )
        assert self._lock.locked(), "Lock must be acquired at this point."
        self._add_to_idle_processes(process_handle)

    def dispose(self):
        with self._lock:
            for processes in itertools.chain(
                self._idle_processes.values(), self._running_processes.values()
            ):
                for process_handle in processes:
                    process_handle.kill()
            self._idle_processes.clear()
            self._running_processes.clear()

    def get_idle_processes_count(self) -> int:
        with self._lock:
            return self._get_idle_processes_count_unlocked()

    def _get_idle_processes_count_unlocked(self) -> int:
        assert self._lock.locked(), "Lock must be acquired at this point."
        count = 0
        for v in self._idle_processes.values():
            count += len(v)
        return count

    def get_running_processes_count(self) -> int:
        with self._lock:
            return self._get_running_processes_count_unlocked()

    def _get_running_processes_count_unlocked(self) -> int:
        assert self._lock.locked(), "Lock must be acquired at this point."
        count = 0
        for v in self._running_processes.values():
            count += len(v)
        return count

    def _count_total_processes(self) -> int:
        assert self._lock.locked(), "Lock must be acquired at this point."
        count = 0
        for v in itertools.chain(
            self._running_processes.values(), self._idle_processes.values()
        ):
            count += len(v)
        return count

    def _add_to_idle_processes(self, process_handle: ProcessHandle):
        print("Add to idle", process_handle.pid)
        assert self._lock.locked(), "Lock must be acquired at this point."
        processes = self._idle_processes.get(process_handle.key)
        if processes is None:
            processes = self._idle_processes[process_handle.key] = set()
        processes.add(process_handle)

    def _add_to_running_processes(self, process_handle: ProcessHandle):
        assert self._lock.locked(), "Lock must be acquired at this point."
        self._processes_running_semaphore.acquire()
        processes = self._running_processes.get(process_handle.key)
        if processes is None:
            processes = self._running_processes[process_handle.key] = set()
        processes.add(process_handle)

    def _remove_from_running_processes(self, process_handle: ProcessHandle):
        assert self._lock.locked(), "Lock must be acquired at this point."
        self._processes_running_semaphore.release()
        processes = self._running_processes.get(process_handle.key)
        if not processes:
            return
        processes.discard(process_handle)

    def _warmup_processes(self):
        if not self.actions:
            return

        with self._lock:
            while self._count_total_processes() < self._settings.min_processes:
                one_action = next(self._cycle_actions_iterator)
                self._create_process(one_action)

    @contextmanager
    def obtain_process_for_action(self, action: Action) -> Iterator[ProcessHandle]:
        action_package: ActionPackage = self.action_package_id_to_action_package[
            action.action_package_id
        ]

        key = _get_process_handle_key(self._settings, action_package)
        process_handle: Optional[ProcessHandle] = None
        while True:
            with self._lock:
                processes = self._idle_processes.get(key)
                if processes:
                    # Get any process from the (compatible) idle processes.
                    process_handle = processes.pop()
                    log.debug(
                        f"Process Pool: Using idle process ({process_handle.pid})."
                    )
                    if not process_handle.is_alive():
                        # Process died while trying to get it.
                        log.critical(
                            f"Process Pool: Unexpected: Idle process exited "
                            f"({process_handle.pid})."
                        )
                        continue

                    self._add_to_running_processes(process_handle)
                else:
                    # No compatible process: we need to create one now.
                    n_running = self._get_running_processes_count_unlocked()
                    if n_running < self.max_processes:
                        self._create_process(action)
                        processes = self._idle_processes.get(key)
                        assert (
                            processes
                        ), f"Expected idle processes bound to key: {key} at this point!"
                        process_handle = processes.pop()
                        log.debug(
                            f"Process Pool: Created process ({process_handle.pid})."
                        )
                        if not process_handle.is_alive():
                            # Process died while trying to get it.
                            log.critical(
                                f"Process Pool: Unexpected: Idle process exited right "
                                f"after creation ({process_handle.pid})."
                            )
                            continue
                        self._add_to_running_processes(process_handle)
                    else:
                        log.critical(
                            f"Delayed running action: {action.name} because "
                            f"{self.max_processes} actions are already running ("
                            f"waiting for another action to finish running)."
                        )

            if process_handle is not None:
                break
            else:
                # Each 5 seconds check again and print delayed message if still
                # not able to run.
                if self._processes_running_semaphore.acquire(timeout=5):
                    self._processes_running_semaphore.release()

        if process_handle is not None:
            try:
                yield process_handle
            finally:
                with self._lock:
                    self._remove_from_running_processes(process_handle)
                    if process_handle.is_alive():
                        if self._reuse_processes:
                            curr_idle = self._get_idle_processes_count_unlocked()
                            if not process_handle.can_reuse:
                                log.debug(
                                    f"Process Pool: Exited process ({process_handle.pid}) -- process marked as non-reusable."
                                )
                                # We cannot reuse it!
                                process_handle.kill()

                            elif self.min_processes <= curr_idle:
                                log.debug(
                                    f"Process Pool: Exited process ({process_handle.pid}) -- min processes already satisfied."
                                )
                                # We cannot reuse it!
                                process_handle.kill()
                            else:
                                log.debug(
                                    f"Process Pool: Adding back to pool ({process_handle.pid})."
                                )
                                self._add_to_idle_processes(process_handle)
                        else:
                            log.debug(
                                f"Process Pool: Exited process ({process_handle.pid}) -- not reusing processes."
                            )
                            # We cannot reuse it!
                            process_handle.kill()

                # If needed recreate idle processes which were removed (needed
                # especially when not reusing processes, but if some process
                # crashes it's also needed).
                self._warmup_processes()

            return

        raise AssertionError("Expected process_handle to be not None!")


_actions_process_pool: Optional[ActionsProcessPool] = None


@contextmanager
def setup_actions_process_pool(
    settings: Settings,
    action_package_id_to_action_package: Dict[str, ActionPackage],
    actions: List[Action],
):
    global _actions_process_pool

    _actions_process_pool = ActionsProcessPool(
        settings, action_package_id_to_action_package, actions
    )
    yield
    _actions_process_pool = None


def get_actions_process_pool() -> ActionsProcessPool:
    assert _actions_process_pool is not None
    return _actions_process_pool
