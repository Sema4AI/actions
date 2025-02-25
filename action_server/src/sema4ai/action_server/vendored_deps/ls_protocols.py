from typing import Any, TypedDict


class _DiagnosticSeverity:
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


class _PositionTypedDict(TypedDict):
    # Line position in a document (zero-based).
    line: int

    # Character offset on a line in a document (zero-based). Assuming that
    # the line is represented as a string, the `character` value represents
    # the gap between the `character` and `character + 1`.
    #
    # If the character value is greater than the line length it defaults back
    # to the line length.
    character: int


class _RangeTypedDict(TypedDict):
    start: _PositionTypedDict
    end: _PositionTypedDict


class _DiagnosticsTypedDict(TypedDict, total=False):
    # The range at which the message applies.
    range: _RangeTypedDict

    # The diagnostic's severity. Can be omitted. If omitted it is up to the
    # client to interpret diagnostics as error, warning, info or hint.
    severity: int | None  # DiagnosticSeverity

    # The diagnostic's code, which might appear in the user interface.
    code: int | str

    # An optional property to describe the error code.
    #
    # @since 3.16.0
    codeDescription: Any

    # A human-readable string describing the source of this
    # diagnostic, e.g. 'typescript' or 'super lint'.
    source: str | None

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
    data: Any | None  # unknown;
