import enum
import inspect
import json
import os
import sys
import time
import traceback
import typing
from argparse import ArgumentParser, ArgumentTypeError
from ast import FunctionDef
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Union, overload

from sema4ai.actions import _constants
from sema4ai.actions._constants import SUPPORTED_TYPES_IN_SCHEMA
from sema4ai.actions._customization._extension_points import EPManagedParameters
from sema4ai.actions._customization._plugin_manager import PluginManager
from sema4ai.actions._protocols import IAction


def list_actions(
    *,
    path: str,
    glob: Optional[str] = None,
    __stream__: Optional[typing.IO] = None,
    pm: Optional[PluginManager] = None,
) -> int:
    """
    Prints the actions available at a given path to the stdout in json format.

    [
        {
            "name": "action_name",
            "line": 10,
            "file": "/usr/code/projects/actions.py",
            "docs": "Action docstring",
        },
        ...
    ]

    Args:
        path: The path (file or directory) from where actions should be collected.
    """
    from contextlib import redirect_stdout

    from sema4ai.actions._action import Context
    from sema4ai.actions._collect_actions import collect_actions
    from sema4ai.actions._exceptions import ActionsCollectError
    from sema4ai.actions._protocols import ActionsListActionTypedDict

    from ._collect_actions import update_pythonpath

    p = Path(path)
    context = Context()
    if not p.exists():
        context.show_error(f"Path: {path} does not exist")
        return 1

    if pm is None:
        pm = PluginManager()

    original_stdout = sys.stdout
    if __stream__ is not None:
        write_to = __stream__
    else:
        write_to = original_stdout

    update_pythonpath(p.absolute())
    with redirect_stdout(sys.stderr):
        try:
            action: IAction
            actions_found: List[ActionsListActionTypedDict] = []
            for action in collect_actions(pm, p, glob=glob):
                entry: ActionsListActionTypedDict = {
                    "name": action.name,
                    "line": action.lineno,
                    "file": action.filename,
                    "docs": getattr(action.method, "__doc__") or "",
                    "input_schema": action.input_schema,
                    "output_schema": action.output_schema,
                    "managed_params_schema": action.managed_params_schema,
                    "options": action.options,
                }
                actions_found.append(entry)

            write_to.write(json.dumps(actions_found))
            write_to.flush()
        except Exception as e:
            if not isinstance(e, ActionsCollectError):
                traceback.print_exc()
            else:
                context.show_error(str(e))
            return 1

    return 0


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

            log.info(f"sema4ai-actions killing processes after run: {names}")
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


class _OsExit(enum.Enum):
    NO = 0
    BEFORE_TEARDOWN = 1
    AFTER_TEARDOWN = 2


def _has_response_schema(action: IAction) -> bool:
    output_schema = action.output_schema
    if isinstance(output_schema, dict):
        properties = output_schema.get("properties")
        if properties and isinstance(properties, dict):
            if set(properties.keys()) == {"result", "error"}:
                return True
    return False


def run(
    *,
    output_dir: str,
    path: str,
    action_name: Union[Sequence[str], str, None],
    max_log_files: int = 5,
    max_log_file_size: str = "1MB",
    console_colors: str = "auto",
    log_output_to_stdout: str = "",
    no_status_rc: bool = False,
    teardown_dump_threads_timeout: Optional[float] = None,
    teardown_interrupt_timeout: Optional[float] = None,
    os_exit: Optional[str] = None,
    additional_arguments: Optional[List[str]] = None,
    preload_module: Optional[List[str]] = None,
    glob: Optional[str] = None,
    json_input: Optional[str] = None,
    pm: Optional[PluginManager] = None,
    print_input: bool = False,
    print_result: bool = False,
    json_output: Optional[str] = None,
) -> int:
    """
    Runs an action.

    Args:
        output_dir: The directory where output should be put.
        path: The file or directory where the actions should be collected from.
        action_name: The name(s) of the action to run.
        max_log_files: The maximum number of log files to be created (if more would
            be needed the oldest one is deleted).
        max_log_file_size: The maximum size for the created log files.
        console_colors:
            "auto": uses the default console
            "plain": disables colors
            "ansi": forces ansi color mode
        log_output_to_stdout:
            "": query the RC_LOG_OUTPUT_STDOUT value.
            "no": don't provide log output to the stdout.
            "json": provide json output to the stdout.
        no_status_rc:
            Set to True so that if running actions has an error inside the action
            the return code of the process is 0.
        teardown_dump_threads_timeout: Can be used to customize the time
            to dump threads in the teardown process if it doesn't complete
            until the specified timeout.
            It's also possible to specify it with the
            RC_TEARDOWN_DUMP_THREADS_TIMEOUT environment variable.
            Defaults to 5 seconds if not specified.
        teardown_interrupt_timeout: Can be used to customize the time
            to interrupt the teardown process after a given timeout.
            It's also possible to specify it with the
            RC_TEARDOWN_INTERRUPT_TIMEOUT environment variable.
            Defaults to not interrupting.
        os_exit: Can be used to exit the process early, without going through
            the regular process teardown. In general it's not recommended, but
            it can be used as a workaround to avoid crashes or deadlocks under
            specific situations found either during the actions session teardown
            or during the interpreter exit.
            Note that subprocesses will be force-killed before exiting.
            Accepted values: 'before-teardown', 'after-teardown'.
            'before-teardown' means that the process will exit without running
                the actions session teardown.
            'after-teardown' means that the process will exit right after the
                actions session teardown takes place.
        additional_arguments: The arguments passed to the action.
        preload_module: The modules which should be pre-loaded (i.e.: loaded
            after the logging is in place but before any other action is collected).
        glob: A glob to define from which module names the actions should be loaded.
        json_input: The path to a json file to be loaded to get the arguments.
        print_input: If set the input passed to an @action will be shown
            in the console (note that even if false it should be also added to the
            `log.html`).
        print_result: If set the result generated by running an @action will be shown
            in the console (note that even if false it should be also added to the
            `log.html`).
        json_output: The path to a json output file with the result gotten from
            running the action (dict with "result", "message" and "status").

    Returns:
        0 if everything went well.
        1 if there was some error running the action.
    """
    from sema4ai.actions._collect_actions import update_pythonpath
    from sema4ai.actions._response import ActionError, Response

    # If it's set it'll only consider files under the ROBOT_ROOT to contain user code
    # we leave it unset so that it considers all files under lib or site-packages as
    # lib code and everything else is user code.
    os.environ.pop("ROBOT_ROOT", None)
    import copy

    from robocorp.log import ConsoleMessageKind, console, redirect
    from robocorp.log.pyproject_config import (
        read_pyproject_toml,
        read_robocorp_auto_log_config,
    )

    from sema4ai.actions._action import Context, set_current_action
    from sema4ai.actions._collect_actions import collect_actions
    from sema4ai.actions._config import RunConfig, set_config
    from sema4ai.actions._exceptions import ActionsCollectError
    from sema4ai.actions._hooks import (
        after_action_run,
        after_all_actions_run,
        before_action_run,
        before_all_actions_run,
    )
    from sema4ai.actions._interrupts import interrupt_on_timeout
    from sema4ai.actions._log_auto_setup import setup_cli_auto_logging
    from sema4ai.actions._log_output_setup import (
        setup_log_output,
        setup_log_output_to_port,
    )
    from sema4ai.actions._protocols import Status

    if not output_dir:
        output_dir = os.environ.get("ROBOT_ARTIFACTS", "")

    if not output_dir:
        output_dir = "./output"

    if pm is None:
        pm = PluginManager()

    console.set_mode(console_colors)

    # Don't show internal machinery on tracebacks:
    # setting __tracebackhide__ will make it so that robocorp-log
    # won't show this frame onwards in the logging.
    __tracebackhide__ = 1

    p = Path(path).absolute()
    context = Context(print_result=print_result, json_output_file=json_output)
    if not p.exists():
        context.show_error(f"Path: {path} does not exist")
        return 1

    if teardown_dump_threads_timeout is None:
        v = os.getenv("RC_TEARDOWN_DUMP_THREADS_TIMEOUT", "5")

        try:
            teardown_dump_threads_timeout = float(v)
        except ValueError:
            sys.stderr.write(
                f"Value set for RC_TEARDOWN_DUMP_THREADS_TIMEOUT ({v}) is not a valid float."
            )
            sys.exit(1)

    if teardown_interrupt_timeout is None:
        v = os.getenv("RC_TEARDOWN_INTERRUPT_TIMEOUT", "-1")

        try:
            teardown_interrupt_timeout = float(v)
        except ValueError:
            sys.stderr.write(
                f"Value set for RC_TEARDOWN_INTERRUPT_TIMEOUT ({v}) is not a valid float."
            )
            sys.exit(1)

    os_exit_enum = _OsExit.NO
    used_env = False
    if not os_exit:
        os_exit = os.getenv("RC_OS_EXIT", "")
        used_env = True

    if os_exit:
        if os_exit == "before-teardown":
            os_exit_enum = _OsExit.BEFORE_TEARDOWN
        elif os_exit == "after-teardown":
            os_exit_enum = _OsExit.AFTER_TEARDOWN
        else:
            if used_env:
                context.show_error(f"Error: RC_OS_EXIT invalid value: {os_exit}")
            else:
                context.show_error(
                    f"Error: --os-exit argument invalid value: {os_exit}"
                )
            sys.exit(1)

    # Enable faulthandler (writing to sys.stderr) early on in the
    # action execution process.
    import faulthandler

    faulthandler.enable()

    from robocorp import log

    action_names: Sequence[str]
    if not action_name:
        action_names = []
        action_or_actions = "actions"
    elif isinstance(action_name, str):
        action_names = [action_name]
        action_or_actions = "action"
    else:
        action_names = action_name
        action_name = ", ".join(str(x) for x in action_names)
        action_or_actions = "action" if len(action_names) == 1 else "actions"

    config: log.AutoLogConfigBase
    pyproject_path_and_contents = read_pyproject_toml(p)
    pyproject_toml_contents: dict
    if pyproject_path_and_contents is None:
        config = log.DefaultAutoLogConfig()
        pyproject_toml_contents = {}
    else:
        config = read_robocorp_auto_log_config(context, pyproject_path_and_contents)
        pyproject_toml_contents = pyproject_path_and_contents.toml_contents

    output_dir_path = Path(output_dir).absolute()
    output_dir_path.mkdir(parents=True, exist_ok=True)

    run_config = RunConfig(
        output_dir_path,
        p,
        action_names,
        max_log_files,
        max_log_file_size,
        console_colors,
        log_output_to_stdout,
        no_status_rc,
        pyproject_toml_contents,
    )

    json_loaded_arguments: Optional[Dict[str, Any]] = None
    if json_input:
        json_path: Path = Path(json_input)
        if not json_path.exists():
            context.show_error(
                f"Error: The file passed as `--json-arguments` does not exist ({json_input})"
            )
            sys.exit(1)

        with json_path.open("rb") as stream:
            try:
                arguments = json.load(stream)
            except Exception as e:
                context.show_error(
                    f"Error: Unable to read the contents of {json_input} as json.\nOriginal error: {e}"
                )
                sys.exit(1)
            if not isinstance(arguments, dict):
                context.show_error(
                    f"Error: Expected the root of '{json_input}' to be a json object. Found: {type(arguments)} ({arguments})"
                )
                sys.exit(1)
            for key in arguments.keys():
                if not isinstance(key, str):
                    context.show_error(
                        f"Error: Expected all the keys in '{json_input}' to be strings. Found: {type(key)} ({key})"
                    )
                    sys.exit(1)
            json_loaded_arguments = arguments

    retcode = 22  # Something went off if this was kept until the end.
    update_pythonpath(p.absolute())
    try:
        with set_config(run_config), setup_cli_auto_logging(
            # Note: we can't customize what's a "project" file or a "library" file,
            # right now the customizations are all based on module names.
            config
        ), redirect.setup_stdout_logging(log_output_to_stdout), setup_log_output(
            output_dir=output_dir_path,
            max_files=max_log_files,
            max_file_size=max_log_file_size,
        ), setup_log_output_to_port(), context.register_lifecycle_prints():
            run_name = os.path.basename(p)
            if action_name:
                run_name += f" - {action_name}"

            run_status: Union[Literal["PASS"], Literal["ERROR"]] = "PASS"
            log.start_run(run_name)
            try:
                setup_message = ""
                log.start_task("Collect actions", "setup", "", 0)
                try:
                    if preload_module:
                        import importlib

                        for module in preload_module:
                            context.show(f"\nPre-loading module: {module}")
                            importlib.import_module(module)

                    if not action_name:
                        context.show(f"\nCollecting actions from: {path}")
                    else:
                        context.show(
                            f"\nCollecting {action_or_actions} {action_name} from: {path}"
                        )

                    actions: List[IAction] = list(
                        collect_actions(pm, p, action_names, glob)
                    )

                    if not actions:
                        raise ActionsCollectError(
                            f"Did not find any actions in: {path}"
                        )
                    if len(actions) > 1:
                        raise ActionsCollectError(
                            f"Expected a single action to be run. Found: {', '.join(x.name for x in actions)}."
                        )
                except Exception as e:
                    run_status = "ERROR"
                    setup_message = str(e)

                    log.exception()
                    if not isinstance(e, ActionsCollectError):
                        traceback.print_exc()
                    else:
                        context.show_error(setup_message)

                    retcode = 1
                    return retcode
                finally:
                    log.end_task("Collect actions", "setup", run_status, setup_message)

                before_all_actions_run(actions)

                try:
                    for action in actions:
                        set_current_action(action)
                        before_action_run(action)
                        try:
                            if print_input and json_loaded_arguments is not None:
                                input_as_json_str = json.dumps(
                                    json_loaded_arguments, indent=4
                                )
                                context.show(
                                    "input:", kind=ConsoleMessageKind.IMPORTANT
                                )
                                context.show(
                                    input_as_json_str,
                                    flush=True,
                                )
                            if json_loaded_arguments is not None:
                                kwargs = copy.deepcopy(json_loaded_arguments)
                                kwargs = _validate_and_convert_kwargs(
                                    pm, action, kwargs
                                )

                            else:
                                kwargs = _normalize_arguments(
                                    pm, action, additional_arguments or []
                                )

                            result = action.run(**kwargs)

                            action.result = result
                            action.status = Status.PASS

                            if _has_response_schema(action):
                                if getattr(result, "error", None):
                                    action.status = Status.FAIL
                                    action.message = str(result.error)

                        except Exception as e:
                            action.status = Status.FAIL
                            action.exc_info = sys.exc_info()

                            if isinstance(e, ActionError):
                                # Custom support: if an action raised an
                                # expected error, provide a custom response
                                error_msg = (
                                    str(e)
                                    or (
                                        f"Error ({e.__class__.__name__})"  # Maybe it's a subclass?
                                    )
                                )
                                action.message = error_msg
                            else:
                                # In this case, as it's unexpected, just show the class
                                # (we don't show the message because it could contain
                                # private information and that goes out to the LLM).
                                action.message = (
                                    f"Unexpected error ({e.__class__.__name__})"
                                )

                            if _has_response_schema(action):
                                action.result = Response(error=action.message)

                        finally:
                            with interrupt_on_timeout(
                                teardown_dump_threads_timeout,
                                teardown_interrupt_timeout,
                                "Teardown",
                                "--teardown-dump-threads-timeout",
                                "RC_TEARDOWN_DUMP_THREADS_TIMEOUT",
                                "--teardown-interrupt-timeout",
                                "RC_TEARDOWN_INTERRUPT_TIMEOUT",
                            ):
                                after_action_run(action)
                            set_current_action(None)
                            if action.failed:
                                run_status = "ERROR"
                finally:
                    log.start_task("Teardown actions", "teardown", "", 0)
                    try:
                        with interrupt_on_timeout(
                            teardown_dump_threads_timeout,
                            teardown_interrupt_timeout,
                            "Teardown",
                            "--teardown-dump-threads-timeout",
                            "RC_TEARDOWN_DUMP_THREADS_TIMEOUT",
                            "--teardown-interrupt-timeout",
                            "RC_TEARDOWN_INTERRUPT_TIMEOUT",
                        ):
                            if os_exit_enum == _OsExit.BEFORE_TEARDOWN:
                                log.info(
                                    "The actions teardown was skipped due to option to os._exit before teardown."
                                )
                            else:
                                after_all_actions_run(actions)
                        # Always do a process snapshot as the process is about to finish.
                        log.process_snapshot()
                    finally:
                        log.end_task("Teardown actions", "teardown", Status.PASS, "")

                if no_status_rc:
                    retcode = 0
                    return retcode
                else:
                    retcode = int(any(action.failed for action in actions))
                    return retcode
            finally:
                log.end_run(run_name, run_status)
    except:
        # This means we had an error in the framework (as user errors should
        # be handled on the parts that call user code).
        if os_exit_enum != _OsExit.NO:
            # Show the exception if we'll do an early exit, otherwise
            # let Python itself print it.
            retcode = 23
            traceback.print_exc()
        raise
    finally:
        if os_exit_enum != _OsExit.NO:
            # Either before or after will exit here (the difference is that
            # if before teardown was requested the teardown is skipped).
            log.info(f"sema4ai.actions: os._exit option: {os_exit}")
            _os_exit(retcode)

        # After the run is finished, start a timer which will print the
        # current threads if the process doesn't exit after a given timeout.
        from threading import Timer

        teardown_time = time.monotonic()
        var_name_dump_threads = "RC_DUMP_THREADS_AFTER_RUN"
        if os.environ.get(var_name_dump_threads, "1").lower() not in (
            "",
            "0",
            "f",
            "false",
        ):
            var_name_dump_threads_timeout = "RC_DUMP_THREADS_AFTER_RUN_TIMEOUT"
            try:
                timeout = float(os.environ.get(var_name_dump_threads_timeout, "40"))
            except Exception:
                sys.stderr.write(
                    f"Invalid value for: {var_name_dump_threads_timeout} environment value. Cannot convert to float."
                )
                timeout = 40

            from sema4ai.actions._interrupts import dump_threads

            def on_timeout():
                dump_threads(
                    message=(
                        f"All actions have run but the process still hasn't exited "
                        f"elapsed {time.monotonic() - teardown_time:.2f} seconds after teardown end. Showing threads found:"
                    )
                )

            t = Timer(timeout, on_timeout)
            t.daemon = True
            t.start()


class _CustomArgumentParser(ArgumentParser):
    def error(self, msg):
        raise RuntimeError(msg)

    def exit(self, status=0, message=None):
        raise RuntimeError(message or "")


def str_to_bool(s):
    # Convert string to boolean
    return s.lower() in ["true", "t", "yes", "1"]


def check_boolean(value):
    if value.lower() not in ["true", "false", "t", "f", "yes", "no", "1", "0"]:
        raise ArgumentTypeError(f"Invalid value for boolean flag: {value}")
    return str_to_bool(value)


def _validate_and_convert_kwargs(
    pm: PluginManager, action: IAction, kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    from typing import get_type_hints

    from sema4ai.actions._exceptions import InvalidArgumentsError
    from sema4ai.actions._variables_scope import (
        create_validate_and_convert_kwargs_scope,
    )

    target_method = action.method
    sig = inspect.signature(target_method)
    type_hints = get_type_hints(target_method)
    method_name = target_method.__code__.co_name
    new_kwargs: Dict[str, Any] = {}

    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name)

        is_managed_param = _is_managed_param(pm, param.name, param=param)
        if param_type is None:
            # If not given, default to `str`.
            if is_managed_param:
                param_type = _get_managed_param_type(pm, param.name, param=param)
            else:
                param_type = str

        with create_validate_and_convert_kwargs_scope(
            param_name=param_name, param_type=param_type
        ):
            if param.default is inspect.Parameter.empty:
                # It's required, so, let's see if it's in the kwargs.
                if not is_managed_param:
                    if param_name not in kwargs:
                        raise InvalidArgumentsError(
                            f"Error. The parameter `{param_name}` was not defined in the input."
                        )

            passed_value = kwargs.get(param_name, inspect.Parameter.empty)

            if passed_value is not inspect.Parameter.empty:
                if param_type not in SUPPORTED_TYPES_IN_SCHEMA:
                    model_validate = getattr(param_type, "model_validate", None)
                    if model_validate is not None:
                        # Support for pydantic models.
                        try:
                            created = model_validate(passed_value)
                        except Exception as e:
                            msg = f"Error converting received json contents to pydantic model: {e}."
                            raise InvalidArgumentsError(
                                f"It's not possible to call: '{method_name}' because the passed arguments don't match the expected signature.\n{msg}"
                            )
                        new_kwargs[param_name] = created
                        continue
                    else:
                        raise InvalidArgumentsError(
                            f"Error. The param type '{param_type.__name__}' in '{method_name}' is not supported. Supported parameter types: str, int, float, bool and pydantic.Model."
                        )

                check_type = param_type
                if param_type == float:
                    check_type = (float, int)
                if not isinstance(passed_value, check_type):
                    raise InvalidArgumentsError(
                        f"Error. Expected the parameter: `{param_name}` to be of type: {param_type.__name__}. Found type: {type(passed_value).__name__}."
                    )

                new_kwargs[param_name] = passed_value

    new_kwargs = _inject_managed_params(pm, sig, new_kwargs, kwargs)
    error_message = ""
    try:
        sig.bind(**new_kwargs)
    except Exception as e:
        error_message = f"It's not possible to call: '{method_name}' because the passed arguments don't match the expected signature.\nError: {e}"
    if error_message:
        raise InvalidArgumentsError(error_message)

    return new_kwargs


def _inject_managed_params(
    pm: PluginManager,
    sig: inspect.Signature,
    new_kwargs: Dict[str, Any],
    original_kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    if pm.has_instance(EPManagedParameters):
        ep_managed_parameters = pm.get_instance(EPManagedParameters)
        return ep_managed_parameters.inject_managed_params(
            sig, new_kwargs, original_kwargs
        )
    return new_kwargs


@overload
def _is_managed_param(
    pm: PluginManager,
    param_name: str,
    *,
    node: FunctionDef,
) -> bool:
    pass


@overload
def _is_managed_param(
    pm: PluginManager,
    param_name: str,
    *,
    param: inspect.Parameter,
) -> bool:
    pass


def _is_managed_param(
    pm: PluginManager,
    param_name: str,
    *,
    node: Optional[FunctionDef] = None,
    param: Optional[inspect.Parameter] = None,
) -> bool:
    """
    Verified if the given parameter is a managed parameter.

    Args:
        pm: The plugin manager.
        param_name: The name of the parameter to check.
        node: The FunctionDef node (ast), should be passed when doing lint
            analysis.
        param: The actual introspected parameter of the function, should
            be passed when actually calling the function.

    Returns: True if the given parameter is managed and False otherwise.

    Note: either node or param must be passed (but not both at the same time).
    """
    if node is None and param is None:
        raise AssertionError("Either node or param must be passed.")

    if node is not None and param is not None:
        raise AssertionError(
            "Either the node or param must be passed, but not both at the same time."
        )

    if pm.has_instance(EPManagedParameters):
        ep_managed_parameters = pm.get_instance(EPManagedParameters)
        if node is not None:
            return ep_managed_parameters.is_managed_param(param_name, node=node)
        elif param is not None:
            return ep_managed_parameters.is_managed_param(param_name, param=param)
        else:
            raise AssertionError("Not expected to get here.")
    return False


@overload
def _get_managed_param_type(
    pm: PluginManager,
    param_name: str,
    *,
    node: FunctionDef,
) -> str:
    raise NotImplementedError()


@overload
def _get_managed_param_type(
    pm: PluginManager,
    param_name: str,
    *,
    param: inspect.Parameter,
) -> type:
    raise NotImplementedError()


def _get_managed_param_type(
    pm: PluginManager,
    param_name: str,
    *,
    node: Optional[FunctionDef] = None,
    param: Optional[inspect.Parameter] = None,
):
    if pm.has_instance(EPManagedParameters):
        ep_managed_parameters = pm.get_instance(EPManagedParameters)
        if node is not None:
            return ep_managed_parameters.get_managed_param_type(param_name, node=node)
        elif param is not None:
            return ep_managed_parameters.get_managed_param_type(param_name, param=param)
        else:
            raise AssertionError("Not expected to get here.")

        managed_param_type = ep_managed_parameters.get_managed_param_type(param)
        assert managed_param_type is not None
        return managed_param_type
    raise RuntimeError(
        "Error: Asked managed param type for a param which is not managed."
    )


def _normalize_arguments(
    pm: PluginManager, action: IAction, args: list[str]
) -> Dict[str, Any]:
    from typing import get_type_hints

    from sema4ai.actions._exceptions import InvalidArgumentsError

    target_method = action.method
    sig = inspect.signature(target_method)
    type_hints = get_type_hints(target_method)
    method_name = target_method.__code__.co_name

    # Prepare the argument parser
    parser = _CustomArgumentParser(
        prog=f"python -m {_constants.MODULE_ENTRY_POINT} {method_name} --",
        description=f"{method_name} action.",
        add_help=False,
    )

    # Add arguments to the parser based on the function signature and type hints
    for param_name, param in sig.parameters.items():
        if _is_managed_param(pm, param.name, param=param):
            continue

        param_type = type_hints.get(param_name)

        if param_type:
            if param_type not in SUPPORTED_TYPES_IN_SCHEMA:
                if hasattr(param_type, "model_validate"):
                    # Support for pydantic models.
                    parser.add_argument(f"--{param_name}", required=True)
                    continue

                raise InvalidArgumentsError(
                    f"Error. The param type '{param_type.__name__}' in '{method_name}' is not supported. Supported parameter types: str, int, float, bool and pydantic.Model."
                )

            if param_type == bool:
                param_type = check_boolean
            if param.default is not inspect.Parameter.empty:
                parser.add_argument(
                    f"--{param_name}", type=param_type, default=param.default
                )
            else:
                parser.add_argument(f"--{param_name}", type=param_type, required=True)
        else:
            parser.add_argument(f"--{param_name}", required=True)

    error_message = None
    try:
        parsed_args, argv = parser.parse_known_args(args)
    except (Exception, SystemExit) as e:
        error_message = f"It's not possible to call: '{method_name}' because the passed arguments don't match the expected signature.\n{_get_usage(parser)}.\nError: {str(e)}."

    if error_message:
        raise InvalidArgumentsError(error_message)

    if argv:
        msg = "Unrecognized arguments: %s" % " ".join(argv)
        raise InvalidArgumentsError(
            f"It's not possible to call: '{method_name}' because the passed arguments don't match the expected signature.\n{_get_usage(parser)}.\n{msg}"
        )

    # Call the user function with the parsed arguments.
    kwargs = {}
    for param_name in sig.parameters:
        param_value = getattr(parsed_args, param_name)

        if param_type not in SUPPORTED_TYPES_IN_SCHEMA:
            model_validate = getattr(param_type, "model_validate", None)
            if model_validate is not None:
                try:
                    param_value = json.loads(param_value)
                except Exception:
                    msg = f"(error interpreting contents for {param_name} as a json)."
                    raise InvalidArgumentsError(
                        f"It's not possible to call: '{method_name}' because the passed arguments don't match the expected signature.\n{msg}"
                    )

        kwargs[param_name] = param_value

    kwargs = _validate_and_convert_kwargs(pm, action, kwargs)
    return kwargs


def _get_usage(parser) -> str:
    f = StringIO()
    parser.print_usage(f)
    usage = f.getvalue().strip()
    if usage:
        usage = usage[0].upper() + usage[1:]
    return usage
