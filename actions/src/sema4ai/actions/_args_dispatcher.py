import sys
import typing
from contextlib import contextmanager
from typing import Optional

from sema4ai.tasks._argdispatch import _ArgDispatcher
from sema4ai.tasks._customization._plugin_manager import PluginManager


def _translate(msg):
    return (
        msg.replace("task", "action")
        .replace("Action", "Action")
        .replace("TASK", "ACTION")
    )


class _ActionsArgDispatcher(_ArgDispatcher):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.register("list")(self._list)
        self.register("run")(self._run)
        self._pm: Optional[PluginManager] = None

    @contextmanager
    def _register_lint(self, stream: typing.IO):
        from pathlib import Path

        from sema4ai.actions import _lint_action
        from sema4ai.actions._lint_action import format_lint_results
        from sema4ai.tasks import _hooks

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

        from sema4ai.tasks import _commands

        skip_lint = kwargs.pop("skip_lint", True)

        original_stdout = sys.stdout

        with redirect_stdout(sys.stderr):
            ctx = (
                self._register_lint(original_stdout) if not skip_lint else nullcontext()
            )
            with ctx:
                return _commands.list_actions(*args, __stream__=original_stdout, **kwargs)

    def _run(self, *args, **kwargs):
        from sema4ai.tasks import _commands

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
