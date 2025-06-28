from sema4ai.mcp_core.mcp_base_model import MCPBaseModel
from sema4ai.mcp_core.protocols import IMCPRequestModel, IMessageHandler


def convert_from_camel_to_underscores(text: str) -> str:
    """Convert a camel case string to a snake case string."""
    return "".join(["_" + i.lower() if i.isupper() else i for i in text]).lstrip("_")


class DefaultMcpMessageHandler(IMessageHandler):
    """Default implementation of the IMessageHandler protocol."""

    async def handle_request(self, request: IMCPRequestModel) -> MCPBaseModel:
        """Handle an MCP message."""
        name = f"on_{convert_from_camel_to_underscores(request.__class__.__name__)}"

        if not hasattr(self, name):
            raise ValueError(
                f"No handler found for request: {request.__class__.__name__} (expected: {name} in {self.__class__.__name__})"
            )

        return getattr(self, name)(request)
