import json
import logging
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired
from typing import Dict, Iterator, List, Optional, Tuple

from sema4ai.action_server._protocols import ActionResult, RCCActionResult, Sentinel
from sema4ai.action_server._robo_utils.constants import NULL

log = logging.getLogger(__name__)


RCC_CLOUD_ROBOT_MUTEX_NAME = "rcc_cloud_activity"
RCC_CREDENTIALS_MUTEX_NAME = "rcc_credentials"


class EnvInfo(object):
    def __init__(self, env: Dict[str, str]):
        self.env = env


def as_str(s) -> str:
    if isinstance(s, bytes):
        return s.decode("utf-8", "replace")
    return str(s)


class Rcc(object):
    def __init__(self, rcc_location: Path, sema4ai_home: Optional[Path]):
        self._rcc_location = rcc_location
        self.sema4ai_home = sema4ai_home
        self.config_location = os.environ.get(
            "S4_ACTION_SERVER_RCC_CONFIG_LOCATION", ""
        )

    def _compute_env(self):
        env = os.environ.copy()
        env.pop("PYTHONPATH", "")
        env.pop("PYTHONHOME", "")
        env.pop("VIRTUAL_ENV", "")
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        if self.sema4ai_home:
            env["SEMA4AI_HOME"] = str(self.sema4ai_home)

        return env

    def _compute_launch_args_and_kwargs(
        self, cwd, env, args, stderr=Sentinel.SENTINEL
    ) -> Tuple[list, dict]:
        from sema4ai.action_server._robo_utils.process import build_subprocess_kwargs

        if stderr is Sentinel.SENTINEL:
            stderr = subprocess.PIPE

        kwargs: dict = build_subprocess_kwargs(cwd, env, stderr=stderr)
        rcc_location = str(self._rcc_location)
        args = (
            [rcc_location]
            + args
            + ["--controller", "action-server", "--bundled", "--sema4ai"]
        )

        return args, kwargs

    def _run_rcc(
        self,
        args: List[str],
        timeout: float = 35,
        error_msg: str = "",
        mutex_name=None,
        cwd: Optional[str] = None,
        log_errors=True,
        stderr=Sentinel.SENTINEL,
        show_interactive_output: bool = False,
        hide_in_log: Optional[str] = None,
    ) -> RCCActionResult:
        """
        Returns an ActionResult where the result is the stdout of the executed command.

        :param log_errors:
            If false, errors won't be logged (i.e.: should be false when errors-+
            are expected).

        :param stderr:
            If given sets the stderr redirection (by default it's subprocess.PIPE,
            but users could change it to something as subprocess.STDOUT).
        """
        from subprocess import check_output, list2cmdline

        from sema4ai.action_server._robo_utils.process import check_output_interactive

        env = self._compute_env()
        sema4ai_home = env.get("SEMA4AI_HOME")
        if not sema4ai_home:
            sema4ai_home = "<unset>"

        args, kwargs = self._compute_launch_args_and_kwargs(cwd, env, args, stderr)
        cmdline = list2cmdline([str(x) for x in args])

        try:
            if mutex_name:
                from ._robo_utils.system_mutex import timed_acquire_mutex
            else:
                timed_acquire_mutex = NULL
            with timed_acquire_mutex(mutex_name, timeout=15):
                if logging.root.level <= logging.DEBUG:
                    msg = f"Running: {cmdline}"
                    if hide_in_log:
                        msg = msg.replace(hide_in_log, "<HIDDEN_IN_LOG>")

                    log.debug(msg)

                curtime = time.monotonic()

                boutput: bytes
                # We have 2 main modes here: one in which we can print the output
                # interactively while the command is running and another where
                # we only print if some error happened.
                if not show_interactive_output:
                    boutput = check_output(args, timeout=timeout, **kwargs)
                else:

                    def on_output(content):
                        try:
                            sys.stderr.buffer.write(content)
                        except BaseException:
                            log.exception("Error reporting interactive output.")

                    boutput = check_output_interactive(
                        args,
                        timeout=timeout,
                        on_stderr=on_output,
                        on_stdout=on_output,
                        **kwargs,
                    )

        except CalledProcessError as e:
            stdout = as_str(e.stdout)
            stderr = as_str(e.stderr)

            msg = (
                f"Error running: {cmdline}.\nSEMA4AI_HOME: {sema4ai_home}\n\n"
                f"Stdout: {stdout}\nStderr: {stderr}"
            )
            if hide_in_log:
                msg = msg.replace(hide_in_log, "<HIDDEN_IN_LOG>")

            if log_errors:
                log.exception(msg)
            if not error_msg:
                return RCCActionResult(cmdline, success=False, message=msg)
            else:
                additional_info = [error_msg]
                if stdout or stderr:
                    if stdout and stderr:
                        additional_info.append("\nDetails: ")
                        additional_info.append("\nStdout")
                        additional_info.append(stdout)
                        additional_info.append("\nStderr")
                        additional_info.append(stderr)

                    elif stdout:
                        additional_info.append("\nDetails: ")
                        additional_info.append(stdout)

                    elif stderr:
                        additional_info.append("\nDetails: ")
                        additional_info.append(stderr)

                return RCCActionResult(
                    cmdline, success=False, message="".join(additional_info)
                )

        except TimeoutExpired:
            msg = f"Timed out ({timeout}s elapsed) when running: {cmdline}"
            log.exception(msg)
            return RCCActionResult(cmdline, success=False, message=msg)

        except Exception:
            msg = f"Error running: {cmdline}"
            log.exception(msg)
            return RCCActionResult(cmdline, success=False, message=msg)

        output = boutput.decode("utf-8", "replace")

        do_log_as_info = (
            log_errors and logging.root.level < logging.INFO
        ) or logging.root.level <= logging.DEBUG

        if do_log_as_info:
            elapsed = time.monotonic() - curtime
            msg = f"Output from: {cmdline} (took: {elapsed:.2f}s): {output}"
            if hide_in_log:
                msg = msg.replace(hide_in_log, "<HIDDEN_IN_LOG>")
            log.info(msg)

        return RCCActionResult(cmdline, success=True, message=None, result=output)

    def get_package_yaml_hash(self, package_yaml: Path, devenv: bool) -> str:
        args: list[str] = ["ht", "hash"]
        args.append(str(package_yaml))
        args.extend("--silent --no-temp-management --warranty-voided".split())
        if devenv:
            args.append("--devdeps")

        result = self._run_rcc(args)

        if result.success:
            if not result.result:
                raise RuntimeError(
                    f"No result found from running: {result.command_line}"
                )
            return result.result.strip()
        raise RuntimeError(
            f"Error when running: {result.command_line}: {result.message}"
        )

    def create_env_and_get_vars(
        self, datadir: Path, package_yaml: Path, package_yaml_hash: str, devenv: bool
    ) -> ActionResult[EnvInfo]:
        """
        Creates the environment if needed. Note: this function needs to be
        careful so that it doesn't call `_create_env_and_get_vars` unless
        the environment file really changed, as that will build an environment
        (with all the pypi/mamba caches it entails), meaning that if the user
        did use `action-server env clean-tools-caches` the caches will be
        rebuilt and the command will need to be called again.
        """

        env_info_dir = datadir / "env-info"
        env_info_dir.mkdir(parents=True, exist_ok=True)

        env_info_cache_file = env_info_dir / f"{package_yaml_hash}.json"
        if env_info_cache_file.exists():
            try:
                contents = env_info_cache_file.read_text(encoding="utf-8")
                if contents:
                    loaded = json.loads(contents)
                    loaded["lastUsage"] = self._get_curr_time_as_str()
                    env_info = EnvInfo(loaded["environ"])
                    python_exe = env_info.env.get("PYTHON_EXE")
                    if not python_exe or not os.path.exists(python_exe):
                        os.remove(env_info_cache_file)
                    else:
                        return ActionResult(True, None, env_info)
            except Exception:
                return ActionResult(
                    success=False,
                    message=(
                        f"It was not possible to get the environment info from:\n{env_info_cache_file}\n"
                        "to proceed delete that file or fix it (note: if the caches\n"
                        "were cleared they will need to be cleared again after restoring\n"
                        "the environment)."
                    ),
                )

        env_info_result = self._create_env_and_get_vars(
            package_yaml, package_yaml_hash, devenv
        )
        if env_info_result.success:
            assert isinstance(env_info_result.result, EnvInfo)
            dump = {
                "environ": env_info_result.result.env,
                "lastUsage": self._get_curr_time_as_str(),
            }
            env_info_cache_file.write_text(json.dumps(dump), encoding="utf-8")
        return env_info_result

    def _get_curr_time_as_str(self):
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f%Z")

    def _create_env_and_get_vars(
        self, package_yaml: Path, package_yaml_hash: str, devenv: bool
    ) -> ActionResult[EnvInfo]:
        """ """
        args = [
            "holotree",
            "variables",
            "--space",
            package_yaml_hash,
            str(package_yaml),
        ]
        self._add_config_to_args(args)
        args.append("--json")
        args.append("--no-retry-build")
        args.append("--no-pyc-management")

        if os.getenv("SEMA4AI_OPTIMIZE_FOR_CONTAINER") == "1":
            args.append("--liveonly")
        if devenv:
            args.append("--devdeps")

        timeout = 60 * 60  # Wait up to 1 hour for the env...
        ret = self._run_rcc(
            args,
            mutex_name=RCC_CLOUD_ROBOT_MUTEX_NAME,
            cwd=str(package_yaml.parent),
            timeout=timeout,  # Creating the env may be really slow!
            show_interactive_output=logging.root.level <= logging.DEBUG,
        )

        def return_failure(msg: Optional[str]) -> ActionResult[EnvInfo]:
            log.critical(
                (
                    "Unable to create environment from:\n%s\n"
                    "To recreate the environment, please fix the related package.yaml"
                ),
                package_yaml,
            )

            if not msg:
                msg = "<unknown reason>"
            log.critical(msg)
            action_result: ActionResult[EnvInfo] = ActionResult(False, msg, None)
            return action_result

        if not ret.success:
            return return_failure(ret.message)

        contents: Optional[str] = ret.result
        if not contents:
            return return_failure("Unable to get output when getting environment.")

        environ = {}
        for entry in json.loads(contents):
            key = str(entry["key"])
            value = str(entry["value"])
            if key:
                environ[key] = value

        if "CONDA_PREFIX" not in environ:
            msg = f"Did not find CONDA_PREFIX in {environ}"
            return return_failure(msg)

        if "PYTHON_EXE" not in environ:
            msg = f"Did not find PYTHON_EXE in {environ}"
            return return_failure(msg)

        return ActionResult(True, None, EnvInfo(environ))

    def pull(self, url: str, directory: str) -> ActionResult[str]:
        args = ["pull", url, "--directory", directory]
        ret = self._run_rcc(args, mutex_name=RCC_CLOUD_ROBOT_MUTEX_NAME)
        if not ret.success:
            return ActionResult(False, ret.message, None)
        return ActionResult(True, None, ret.result)

    def _add_config_to_args(self, args: List[str]) -> List[str]:
        config_location = self.config_location
        if config_location:
            args.append("--config")
            args.append(config_location)
        return args

    def feedack_metric(self, name, value="+1") -> None:
        env = self._compute_env()

        args = ["feedback", "metric", "-t", "action-server", "-n", name, "-v", value]
        self._add_config_to_args(args)
        cwd = None
        args, kwargs = self._compute_launch_args_and_kwargs(cwd, env, args)
        try:
            subprocess.Popen(args, **kwargs)
        except BaseException:
            log.exception("Error submitting feedback.")

    def clean_tools_caches(self):
        args = ["config", "cleanup", "--caches"]
        self._add_config_to_args(args)
        self._run_rcc(args, timeout=600, show_interactive_output=True)

    def get_network_settings(self) -> ActionResult:
        args = ["config", "settings", "--json"]
        return self._run_rcc(args)


_rcc: Optional["Rcc"] = None


@contextmanager
def initialize_rcc(rcc_location: Path, sema4ai_home: Optional[Path]) -> Iterator[Rcc]:
    global _rcc

    if _rcc:
        yield _rcc
        return

    rcc = Rcc(rcc_location, sema4ai_home)
    _rcc = rcc
    try:
        yield rcc
    finally:
        _rcc = None


def get_rcc() -> Rcc:
    assert _rcc is not None, "RCC not initialized"
    return _rcc
