import inspect
from typing import Any, get_args, get_origin

from sema4ai.actions._protocols import IAction


def _is_valid_type(t: Any) -> bool:
    from types import NoneType, UnionType

    if t in (str, int, float, bool, inspect.Parameter.empty, NoneType):
        return True
    if get_origin(t) is UnionType:
        return all(_is_valid_type(arg) for arg in get_args(t))
    return False


def _validate_prompt(action: IAction) -> list[str]:
    """Validate that prompt parameters use basic types (str, int, float, bool)."""
    errors: list[str] = []

    def add_file_info(msg: str) -> str:
        return f"{msg}\nFile: {action.filename}:{action.lineno}: in {action.name}"

    signature = inspect.signature(action.method)
    params = signature.parameters

    # Get managed parameters from the action
    managed_params: dict[str, Any] = {}
    if action.managed_params_schema:
        managed_params = action.managed_params_schema

    # Check that all parameters are basic types (str, int, float, bool)
    for param_name, param in params.items():
        # Skip managed parameters
        if param_name in managed_params:
            continue

        param_type = param.annotation
        if param_type:
            # empty means no type is specified (consider it as str)
            if not _is_valid_type(param_type):
                msg = (
                    f"When collecting @prompt, parameter '{param_name}' has type '{param_type}' "
                    f"but only basic types (str, int, float, bool) and their Unions with None are supported."
                )
                errors.append(add_file_info(msg))

    return errors
