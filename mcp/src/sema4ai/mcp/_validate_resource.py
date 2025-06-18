import inspect
import re
from typing import Any

from sema4ai.actions._protocols import IAction


def _resource_template_matches(uri_template: str, uri: str) -> dict[str, Any] | None:
    """Check if URI matches template and extract parameters."""

    # Same logic as https://github.com/modelcontextprotocol/python-sdk/blob/v1.9.4/src/mcp/server/fastmcp/resources/templates.py#L54

    # Convert template to regex pattern
    pattern = uri_template.replace("{", "(?P<").replace("}", ">[^/]+)")
    match = re.match(f"^{pattern}$", uri)
    if match:
        return match.groupdict()
    return None


def _validate_resource(action: IAction) -> list[str]:
    # Resource may be regular or template resources depending on the uri.
    # If the URI follows the RFC 6570 template syntax, it's a template resource.

    def add_file_info(msg: str) -> str:
        return f"{msg}\nFile: {action.filename}:{action.lineno}: in {action.name}"

    errors = []
    options = action.options
    use_name = action.name
    if not options:
        errors.append(add_file_info(f"Resource {use_name} has no options."))
        return errors  # Cannot proceed

    uri = options.get("uri")
    if not uri:
        errors.append(add_file_info(f"Resource {use_name} has no URI."))
        return errors  # Cannot proceed

    has_uri_params = "{" in uri and "}" in uri
    signature = inspect.signature(action.method)
    params = signature.parameters
    has_func_params = bool(params)

    if has_uri_params or has_func_params:
        # If we have parameters, check if the URI parameters match the function parameter
        # and create a resource template accordingly.
        uri_params: set[str] = set(re.findall(r"{(\w+)}", uri))

        # Get managed parameters from the action
        managed_params: dict[str, Any] = {}
        if action.managed_params_schema:
            managed_params = action.managed_params_schema

        # Remove managed parameters from func_params
        func_params: set[str] = {p for p in params.keys() if p not in managed_params}

        if uri_params != func_params:
            msg = (
                f"When collecting @resource, the parameters in the uri (found: {sorted(uri_params)}) "
                f"and the function parameters (found: {sorted(func_params)}) must match.\n"
                f"uri found: {uri}\n"
                "Define uri parameters as '{param}' in the uri (example: https://example.com/resource/{param}).\n"
                "Define function parameters as arguments in the function (example: def func(a: int, b: int): ...)."
            )
            errors.append(add_file_info(msg))

        # Check that all parameters are basic types (str, int, float, bool)
        for param_name, param in params.items():
            # Skip managed parameters
            if param_name in managed_params:
                continue

            param_type = param.annotation
            if param_type:
                # empty means no type is specified (consider it as str)
                if param_type not in (str, int, float, bool, inspect.Parameter.empty):
                    msg = (
                        f"When collecting @resource, parameter '{param_name}' has type '{param_type}' "
                        f"but only basic types (str, int, float, bool) are supported."
                    )
                    errors.append(add_file_info(msg))

    return errors
