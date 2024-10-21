import logging

from sema4ai.action_server._protocols import (
    ArgumentsNamespace,
    ArgumentsNamespaceDevEnvTask,
)

log = logging.getLogger(__name__)


def _handle_devenv_task_command(devenv_args: ArgumentsNamespaceDevEnvTask) -> int:
    import os.path
    import shlex
    import subprocess
    import sys
    from pathlib import Path

    from sema4ai.action_server._robo_utils.process import build_python_launch_env

    from ._action_package_handler import ActionPackageHandler
    from ._settings import setup_settings

    devenv_task_names: list[str] = devenv_args.task_names
    if not devenv_task_names:
        log.critical("No task names specified.")
        return 1

    if not isinstance(devenv_task_names, list):
        log.critical(
            f"Task names must be a list of strings (internal error parsing command line -- found: {devenv_task_names!r} type: {type(devenv_task_names)})."
        )
        return 1

    with setup_settings(devenv_args) as settings:
        datadir = settings.datadir

        # Note: the cwd is the action package directory.
        cwd = "."
        action_package_handler = ActionPackageHandler(cwd, Path(datadir))

        if not action_package_handler.package_yaml_exists:
            log.critical(
                f"No `package.yaml` found in the current directory ({os.path.abspath('.')}). Unable to proceed with dev-environment related command."
            )
            return 1

        package_yaml_contents = action_package_handler.package_yaml_contents
        if not package_yaml_contents:
            log.critical(
                "package.yaml is empty or invalid. Unable to proceed with dev-environment related command."
            )
            return 1
        _condahash, use_env = action_package_handler.bootstrap_environment(devenv=True)
        env = build_python_launch_env(use_env)

        dev_tasks = package_yaml_contents.get("dev-tasks", {})

        for task_name in devenv_task_names:
            task_command = dev_tasks.get(task_name)
            if not task_command:
                log.critical(
                    f"Task: {task_name} is not defined in `dev-tasks` section of package.yaml."
                )
                return 1

            if not isinstance(task_command, str):
                log.critical(
                    f"Task: {task_name} has an invalid `dev-tasks` definition in package.yaml (expected a string, found: {task_command!r}, type: {type(task_command)})."
                )
                return 1

            task_commands: list[list[str]] = []
            for line in task_command.splitlines():
                if line.strip():
                    try:
                        c = shlex.split(line.strip())
                    except Exception as e:
                        log.critical(
                            f"Unable to shlex.split command: {line.strip()}. Error: {e}"
                        )
                        return 1

                    if not c:
                        log.critical(
                            f"Unable to make sense of command: {line.strip()}."
                        )
                        return 1
                    task_commands.append(c)

            if settings.verbose:
                if len(task_commands) == 1:
                    log.debug(f"Parsed command as: {task_commands[0]}")
                else:
                    m = "\n    ".join(str(x) for x in task_commands)
                    log.debug(f"Parsed (multiple) commands as:\n{m}")
                log.debug("Environment variables:")
                for env_key in ("PATH", "PYTHONPATH"):
                    env_val = env.get(env_key)
                    if env_val:
                        log.debug(f"{env_key}:")
                        for path_part in env_val.split(os.path.pathsep):
                            log.debug(f"  {path_part}")
                    else:
                        log.debug(f"{env_key}: (none)")
            try:
                PATH = env["PATH"]

                for command in task_commands:
                    # search for command[0] in PATH

                    command_path = None
                    for path in PATH.split(os.path.pathsep):
                        if os.path.exists(os.path.join(path, command[0])):
                            command_path = os.path.join(path, command[0])
                            break
                        if sys.platform == "win32":
                            if os.path.exists(os.path.join(path, command[0] + ".exe")):
                                command_path = os.path.join(path, command[0] + ".exe")
                                break

                    if not command_path:
                        log.critical(f"Command: {command[0]} not found in PATH.")
                        return 1
                    log.debug(f"Target program: {command_path}")

                    popen = subprocess.Popen(
                        [command_path] + command[1:], env=env, cwd=cwd, shell=False
                    )
                    popen.wait()
                    if popen.returncode != 0:
                        log.critical(
                            f"Task: {task_name} failed with return code: {popen.returncode}. Command: {shlex.join(command)}"
                        )
                        return 1
            except Exception as e:
                log.critical(
                    f"It was not possible to run the task: {task_name}.\nThe error below happened when running the command:\n{task_command}\n{e}"
                )
                return 1

    return 0


def handle_devenv_command(base_args: ArgumentsNamespace) -> int:
    import typing

    from sema4ai.action_server._protocols import ArgumentsNamespaceDevEnv

    devenv_args: ArgumentsNamespaceDevEnv = typing.cast(
        ArgumentsNamespaceDevEnv, base_args
    )

    devenv_command = devenv_args.devenv_command
    if not devenv_command:
        log.critical("Command for devenv operation not specified.")
        return 1

    if devenv_args.devenv_command == "task":
        return _handle_devenv_task_command(
            typing.cast(ArgumentsNamespaceDevEnvTask, devenv_args)
        )

    log.critical(f"Unexpected command: {devenv_command}.")
    return 1
