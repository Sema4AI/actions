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
