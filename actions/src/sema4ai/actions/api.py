"""
This module contains the public API for the actions.

These should be kept backward compatible (breakage here can still occur, but 
it should not be taken lightly).
"""
from typing import Any, Optional, TypedDict, Union


class PositionTypedDict(TypedDict):
    # Line position in a document (zero-based).
    line: int

    # Character offset on a line in a document (zero-based). Assuming that
    # the line is represented as a string, the `character` value represents
    # the gap between the `character` and `character + 1`.
    #
    # If the character value is greater than the line length it defaults back
    # to the line length.
    character: int


class RangeTypedDict(TypedDict):
    start: PositionTypedDict
    end: PositionTypedDict


class DiagnosticsTypedDict(TypedDict, total=False):
    # The range at which the message applies.
    range: RangeTypedDict

    # The diagnostic's severity. Can be omitted. If omitted it is up to the
    # client to interpret diagnostics as error, warning, info or hint.
    severity: Optional[int]  # DiagnosticSeverity

    # The diagnostic's code, which might appear in the user interface.
    code: Union[int, str]

    # An optional property to describe the error code.
    #
    # @since 3.16.0
    codeDescription: Any

    # A human-readable string describing the source of this
    # diagnostic, e.g. 'typescript' or 'super lint'.
    source: Optional[str]

    # The diagnostic's message.
    message: str

    # Additional metadata about the diagnostic.
    #
    # @since 3.15.0
    tags: list  # DiagnosticTag[];

    # An array of related diagnostic information, e.g. when symbol-names within
    # a scope collide all definitions can be marked via this property.
    relatedInformation: list  # DiagnosticRelatedInformation[];

    # A data entry field that is preserved between a
    # `textDocument/publishDiagnostics` notification and
    # `textDocument/codeAction` request.
    #
    # @since 3.16.0
    data: Optional[Any]  # unknown;


def collect_lint_errors(contents_to_lint: str) -> list[DiagnosticsTypedDict]:
    """
    Provides lint errors from the contents of a file containing the `@action`s.

    Args:
        contents_to_lint: The contents which should be linted.

    Returns:
        A list with the diagnostics found.
    """
    from sema4ai.actions import _lint_action
    from sema4ai.actions._customization._extension_points import (  # noqa #type: ignore
        EPManagedParameters,
    )
    from sema4ai.actions._customization._plugin_manager import (  # noqa #type: ignore
        PluginManager,
    )
    from sema4ai.actions._managed_parameters import (  # noqa #type: ignore
        ManagedParameters,
    )

    pm = PluginManager()
    pm.set_instance(EPManagedParameters, ManagedParameters({}))
    errors = list(_lint_action.iter_lint_errors(contents_to_lint, pm=pm))

    lst = []
    for error in errors:
        lsp_err = error.to_lsp_diagnostic()

        # Lines should be 0-based.
        lsp_err["range"]["start"]["line"] -= 1
        lsp_err["range"]["end"]["line"] -= 1
        lst.append(lsp_err)

    return lst
