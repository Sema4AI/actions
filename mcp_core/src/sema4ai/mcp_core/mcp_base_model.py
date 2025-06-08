from dataclasses import dataclass
from enum import Enum
from typing import Any, Type, TypeVar

T = TypeVar("T")


class MessageType(Enum):
    REQUEST = "request"
    NOTIFICATION = "notification"
    RESPONSE = "response"


@dataclass
class BaseModel:
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

            if isinstance(value, BaseModel):
                result[field_name] = value.to_dict()
            elif isinstance(value, list):
                result[field_name] = [
                    item.to_dict() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            else:
                result[field_name] = value
        return result

    @classmethod
    def get_message_type(cls) -> MessageType:
        """Get the type of message this class represents."""
        if cls.__name__.endswith("Request"):
            return MessageType.REQUEST
        elif cls.__name__.endswith("Notification"):
            return MessageType.NOTIFICATION
        elif cls.__name__.endswith("Result") or cls.__name__.endswith("Response"):
            return MessageType.RESPONSE
        return MessageType.REQUEST  # Default to request if unknown
