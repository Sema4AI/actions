import sys
import typing
from contextlib import contextmanager
from logging import getLogger
from typing import List, Optional

from sema4ai.actions import _constants
from sema4ai.actions._customization._plugin_manager import PluginManager

log = getLogger(__name__)


class _ArgDispatcher:
    def __init__(self):
        self._name_to_func = {}

    def register(self, name: str, func):
        self._name_to_func[name] = func

    def _get_description(self):
        return "Sema4.ai framework for AI actions."

    def _add_action_argument(self, run_parser):
        run_parser.add_argument(
            "-a",
            "--action",
            dest="action_name",
            help="The name of the action that should be run.",
            action="append",
        )

    def _add_lint_argument(self, parser):
        parser.add_argument(
            "--skip-lint",
            dest="skip_lint",
            action="store_true",
            default=False,
            help="Skip `@action` linting when an action is found (by default any "
            "`@action` is linted for errors when found).",
        )

    def _create_run_parser(self, main_parser):
        # Run
        run_parser = main_parser.add_parser(
            "run",
            help="Collects actions with the @action decorator and all actions that matches based on the action name filter.",
        )
        run_parser.add_argument(
            dest="path",
            help="The directory or file with the actions to run.",
            nargs="?",
            default=".",
        )
        run_parser.add_argument(
            "--glob",
            help=f"May be used to specify a glob to select from which files actions should be searched (default '{_constants.DEFAULT_ACTION_SEARCH_GLOB}')",
        )
        self._add_action_argument(run_parser)
        run_parser.add_argument(
            "-o",
            "--output-dir",
            dest="output_dir",
            help=(
                "The directory where the logging output files will be stored "
                "(default `ROBOT_ARTIFACTS` environment variable or `./output`)."
            ),
            default="",
        )
        run_parser.add_argument(
            "--max-log-files",
            dest="max_log_files",
            type=int,
            help="The maximum number of output files to store the logs.",
            default=5,
        )
        run_parser.add_argument(
            "--max-log-file-size",
            dest="max_log_file_size",
            help="The maximum size for the log files (i.e.: 1MB, 500kb).",
            default="1MB",
        )

        run_parser.add_argument(
            "--console-colors",
            help="""Define how the console messages shown should be color encoded.

"auto" (default) will color either using the windows API or the ansi color codes.
"plain" will disable console coloring.
"ansi" will force the console coloring to use ansi color codes.
""",
            dest="console_colors",
            type=str,
            choices=["auto", "plain", "ansi"],
            default="auto",
        )

        run_parser.add_argument(
            "--log-output-to-stdout",
            help="Can be used so that log messages are also sent to the 'stdout' (if not specified the RC_LOG_OUTPUT_STDOUT is also queried).",
            dest="log_output_to_stdout",
            type=str,
            choices=["no", "json"],
            default="",
        )

        run_parser.add_argument(
            "--json-input",
            help="May be used to pass the arguments to the action by loading the arguments from a file (defined as a json object, where keys are the arguments names and the values are the values to be set to the arguments).",
            dest="json_input",
        )
        run_parser.add_argument(
            "--json-output",
            help='May be used to save the result of running the action in json format (object with "result", "message" and "status")',
            dest="json_output",
        )
        run_parser.add_argument(
            "--preload-module",
            action="append",
            help="May be used to load a module(s) as the first step when collecting actions.",
            dest="preload_module",
        )

        run_parser.add_argument(
            "--no-status-rc",
            help="When set, if running actions has an error inside the action the return code of the process is 0.",
            dest="no_status_rc",
            action="store_true",
        )

        run_parser.add_argument(
            "--teardown-dump-threads-timeout",
            dest="teardown_dump_threads_timeout",
            type=float,
            help="The timeout (in seconds) to print running threads after the teardown starts (if not specified the RC_TEARDOWN_DUMP_THREADS_TIMEOUT is also queried). Defaults to 5 seconds.",
        )

        run_parser.add_argument(
            "--teardown-interrupt-timeout",
            dest="teardown_interrupt_timeout",
            type=float,
            help="The timeout (in seconds) to interrupt the teardown process  (if not specified the RC_TEARDOWN_INTERRUPT_TIMEOUT is also queried).",
        )

        run_parser.add_argument(
            "--os-exit",
            dest="os_exit",
            type=str,
            choices=["no", "before-teardown", "after-teardown"],
            help="Can be used to do an early os._exit to avoid the actions session teardown or the interpreter teardown. Not recommended in general.",
        )
        run_parser.add_argument(
            "--print-input",
            dest="print_input",
            action="store_true",
            default=False,
            help="Can be used to see the input of the actions run in the terminal.",
        )
        run_parser.add_argument(
            "--print-result",
            dest="print_result",
            action="store_true",
            default=False,
            help="Can be used to see the result of the actions run in the terminal.",
        )

        return run_parser

    def _create_list_actions_parser(self, main_parser):
        # List actions
        list_parser = main_parser.add_parser(
            "list",
            help="Provides output to stdout with json contents of the actions available.",
        )
        list_parser.add_argument(
            dest="path",
            help="The directory or file from where the actions should be listed (default is the current directory).",
            nargs="?",
            default=".",
        )
        list_parser.add_argument(
            "--glob",
            help=(
                f"May be used to specify a glob to select from which files actions should be searched (default '{_constants.DEFAULT_ACTION_SEARCH_GLOB}')"
            ),
        )

        self._add_lint_argument(list_parser)

        return list_parser

    def _create_argparser(self):
        import argparse

        parser = argparse.ArgumentParser(
            prog=_constants.MODULE_ENTRY_POINT,
            description=self._get_description(),
            epilog="View https://github.com/sema4ai/actions for more information",
        )

        subparsers = parser.add_subparsers(dest="command")
        self._create_run_parser(subparsers)
        self._create_list_actions_parser(subparsers)
        return parser

    def parse_args(self, args: List[str]):
        log.debug("Processing args: %s", " ".join(args))
        additional_args = []
        new_args = []
        for i, arg in enumerate(args):
            if arg == "--":
                # argparse.REMAINDER is buggy:
                # https://bugs.python.org/issue17050
                # So, remove '--' and everything after from what's passed to
                # argparser.
                additional_args.extend(args[i + 1 :])
                break
            new_args.append(arg)

        parser = self._create_argparser()
        parsed = parser.parse_args(new_args)

        if additional_args:
            parsed.additional_arguments = additional_args
        return parsed


class _ActionsArgDispatcher(_ArgDispatcher):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.register("list", self._list)
        self.register("run", self._run)
        self._pm: Optional[PluginManager] = None

    @contextmanager
    def _register_lint(self, stream: typing.IO):
        from pathlib import Path

        from sema4ai.actions import _hooks, _lint_action
        from sema4ai.actions._lint_action import format_lint_results

        files_found = set()

        def on_func_found(func, *args, **kwargs) -> None:
            import json

            from sema4ai.actions._lint_action import (
                DiagnosticSeverity,
                DiagnosticsTypedDict,
                LintResultTypedDict,
            )

            filename = Path(func.__code__.co_filename).absolute()

            if filename not in files_found:
                files_found.add(filename)
                errors = list(
                    x.to_lsp_diagnostic()
                    for x in _lint_action.iter_lint_errors(
                        filename.read_bytes(), self._pm
                    )
                )
                if errors:
                    found_critical = False
                    error: DiagnosticsTypedDict
                    lint_result_contents: LintResultTypedDict = {
                        "file": str(filename),
                        "errors": errors,
                    }
                    lint_result = {"lint_result": lint_result_contents}

                    for error in errors:
                        if error["severity"] == DiagnosticSeverity.Error:
                            found_critical = True

                    if found_critical:
                        stream.write(json.dumps(lint_result))
                        stream.flush()
                        sys.exit(1)

                    # Critical not found: print to stderr
                    formatted = format_lint_results(lint_result_contents)
                    if formatted is not None:
                        sys.stderr.write(formatted.message)
                        sys.stderr.flush()

        with _hooks.on_action_func_found.register(on_func_found):
            yield

    def _list(self, *args, **kwargs):
        from contextlib import nullcontext, redirect_stdout

        from sema4ai.actions import _commands

        skip_lint = kwargs.pop("skip_lint", True)

        original_stdout = sys.stdout

        with redirect_stdout(sys.stderr):
            ctx = (
                self._register_lint(original_stdout) if not skip_lint else nullcontext()
            )
            with ctx:
                return _commands.list_actions(
                    *args, __stream__=original_stdout, **kwargs
                )

    def _run(self, *args, **kwargs):
        from sema4ai.actions import _commands

        return _commands.run(*args, **kwargs)

    def _dispatch(self, parsed, pm: Optional[PluginManager] = None) -> int:
        # Custom dispatch as we need to account for custom flags.
        if not parsed.command:
            self._create_argparser().print_help()
            return 1

        method = self._name_to_func[parsed.command]
        dct = parsed.__dict__.copy()
        dct.pop("command")
        dct["pm"] = pm
        self._pm = pm

        return method(**dct)

    def process_args(self, args: List[str], pm: Optional[PluginManager] = None) -> int:
        """
        Processes the arguments and return the returncode.
        """
        try:
            parsed = self.parse_args(args)
        except SystemExit as e:
            code = e.code
            if isinstance(code, int):
                return code
            if code is None:
                return 0
            return int(code)

        return self._dispatch(parsed, pm)
