from dataclasses import dataclass
from typing import Any, Type, TypeVar

from sema4ai.mcp_core.protocols import MessageType

T = TypeVar("T")


@dataclass
class MCPBaseModel:
    """Base class for all MCP models."""

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        raise NotImplementedError("Subclasses must implement this method")

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        result: dict[str, Any] = {}
        for field_name, value in self.__dict__.items():
            # Skip private fields
            if field_name.startswith("_"):
                continue

            if value is None:
                continue

            if isinstance(value, MCPBaseModel):
                result[field_name] = value.to_dict()
            elif isinstance(value, list):
                result[field_name] = [
                    item.to_dict() if isinstance(item, MCPBaseModel) else item for item in value
                ]
            else:
                result[field_name] = value
        return result

    def __str__(self) -> str:
        import json

        try:
            return f"{self.__class__.__name__} -- {json.dumps(self.to_dict(), indent=4)}"
        except Exception:
            return f"{self.__class__.__name__} -- {self.__dict__}"

    __repr__ = __str__

    def __eq__(self, other: Any) -> bool:
        """Check if two instances are equal."""
        if not isinstance(other, MCPBaseModel):
            return False
        return self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        raise NotImplementedError("Hashing is not supported for MCPBaseModel (it's mutable)")

    @classmethod
    def get_message_type(cls) -> MessageType:
        """Get the type of message this class represents."""
        if cls.__name__.endswith("Request"):
            return MessageType.REQUEST
        elif cls.__name__.endswith("Notification"):
            return MessageType.NOTIFICATION
        elif cls.__name__.endswith("Result"):
            return MessageType.RESULT  # A Result is contained inside a Response
        elif cls.__name__.endswith("Response"):
            return MessageType.RESPONSE

        # This is for inner messages that are not requests, notifications, responses, or results
        return MessageType.OTHER
