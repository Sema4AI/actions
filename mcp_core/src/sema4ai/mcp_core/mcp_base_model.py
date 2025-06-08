from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T")


class MessageType(Enum):
    REQUEST = "request"
    NOTIFICATION = "notification"
    RESPONSE = "response"


@dataclass
class BaseModel:
    """Base class for all MCP models."""

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create an instance from a dictionary.

        This method recursively converts dictionaries to their proper class instances
        and handles lists of objects.
        """
        if not isinstance(data, dict):
            return data

        # Get type hints for the class
        type_hints = get_type_hints(cls)

        # Process each field
        kwargs = {}
        for field_name, field_type in type_hints.items():
            # Skip private fields
            if field_name.startswith("_"):
                continue

            # Get value from data or use None for missing fields
            value = data.get(field_name)

            # Handle None values
            if value is None:
                kwargs[field_name] = None
                continue

            # Handle lists of objects
            origin = get_origin(field_type)
            if origin is list:
                item_type = get_args(field_type)[0]
                # Handle union types in list items
                if get_origin(item_type) is Union:
                    # Try each possible type in the union
                    converted_items = []
                    for item in value:
                        if not isinstance(item, dict):
                            converted_items.append(item)
                            continue

                        # Try each type in the union
                        for possible_type in get_args(item_type):
                            if hasattr(possible_type, "from_dict"):
                                try:
                                    converted_items.append(
                                        possible_type.from_dict(item)
                                    )
                                    break
                                except (TypeError, ValueError):
                                    continue
                        else:
                            # If no type worked, keep the original item
                            converted_items.append(item)
                    kwargs[field_name] = converted_items
                elif hasattr(item_type, "from_dict"):
                    # For single type lists, convert each item
                    converted_items = []
                    for item in value:
                        if isinstance(item, dict):
                            converted_items.append(item_type.from_dict(item))
                        else:
                            converted_items.append(item)
                    kwargs[field_name] = converted_items
                else:
                    kwargs[field_name] = value
            # Handle union types for single values
            elif get_origin(field_type) is Union:
                if not isinstance(value, dict):
                    kwargs[field_name] = value
                    continue

                # Try each possible type in the union
                for possible_type in get_args(field_type):
                    if hasattr(possible_type, "from_dict"):
                        try:
                            kwargs[field_name] = possible_type.from_dict(value)
                            break
                        except (TypeError, ValueError):
                            continue
                else:
                    # If no type worked, keep the original value
                    kwargs[field_name] = value
            # Handle nested objects
            elif hasattr(field_type, "from_dict"):
                if isinstance(value, dict):
                    kwargs[field_name] = field_type.from_dict(value)
                else:
                    kwargs[field_name] = value
            else:
                kwargs[field_name] = value

        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        result = {}
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
