from sema4ai.mcp_core.protocols import IMCPRequestModel

from . import _generated_mcp_models
from ._generated_mcp_models import *


def create_mcp_model(data: dict[str, Any]) -> MCPBaseModel:
    """Create an MCP model instance from a dictionary based on its method field (notification or request)

    Args:
        data: Dictionary containing the model data

    Returns:
        An instance of the appropriate MCP model class

    Raises:
        ValueError: If the method field is missing or no matching class is found
    """
    if "method" not in data:
        raise ValueError("Input dictionary must contain a 'method' field")
    method = data["method"]
    if method not in _generated_mcp_models._class_map:
        raise ValueError(f"No MCP model class found for method: {method}")
    return _generated_mcp_models._class_map[method].from_dict(data)


def build_result_model(request_model: MCPBaseModel, kwargs: dict) -> MCPBaseModel:
    """Build the result model for a given request.

    Args:
        request_model: The request model
        kwargs: The keyword arguments to pass to the result model constructor

    Returns:
        The result model
    """
    return _generated_mcp_models._request_to_result_map[type(request_model)].from_dict(kwargs)


def build_json_rpc_response_model(
    request_model: IMCPRequestModel, result_model: Result
) -> JSONRPCResponse:
    """Build the response model for a given request.

    Args:
        request_model: The request model
        result_model: The result model

    Returns:
        The response model
    """
    response = JSONRPCResponse(
        id=request_model.id,
        result=result_model,
    )
    return response


ERROR_CODE_PARSE_ERROR = -32700  # Invalid JSON was received by the server.
ERROR_CODE_INVALID_REQUEST = -32600  # The JSON sent is not a valid Request object.
ERROR_CODE_METHOD_NOT_FOUND = -32601  # The method does not exist / is not available.
ERROR_CODE_INVALID_PARAMS = -32602  # Invalid method parameter(s).
ERROR_CODE_INTERNAL_ERROR = -32603  # Internal JSON-RPC error.
ERROR_CODE_SERVER_ERROR_CUSTOM_MIN = (
    -32099
)  # Reserved for implementation-defined server errors (min)
ERROR_CODE_SERVER_ERROR_CUSTOM_MAX = (
    -32000
)  # Reserved for implementation-defined server errors (max)


def create_json_rpc_error(
    error: str, id: int | None = None, code: int = ERROR_CODE_INTERNAL_ERROR
) -> dict[str, Any]:
    """Create a JSON-RPC error response.

    Args:
        id: The request ID
        error: The error details
    """
    if id is not None:
        return {"jsonrpc": "2.0", "error": {"code": code, "message": error}, "id": id}

    return {"jsonrpc": "2.0", "error": {"code": code, "message": error}}
