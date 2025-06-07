import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, TypeVar, Union, get_type_hints

T = TypeVar("T")


class MessageType(Enum):
    REQUEST = "request"
    NOTIFICATION = "notification"
    RESPONSE = "response"


def create_python_type(
    schema_type: str, schema: dict[str, Any], field_name: str = ""
) -> str:
    """Convert JSON schema type to Python type annotation."""
    if schema_type == "string":
        if "enum" in schema:
            return f"Literal[{', '.join(repr(x) for x in schema['enum'])}]"
        # Special case for method fields
        if field_name == "method":
            if schema.get("const"):
                return f"Literal[{repr(schema['const'])}]"
        return "str"
    elif schema_type == "integer":
        return "int"
    elif schema_type == "number":
        return "float"
    elif schema_type == "boolean":
        return "bool"
    elif schema_type == "array":
        items = schema.get("items", {})
        if isinstance(items, dict):
            item_type = create_python_type(items.get("type", "string"), items)
        else:
            item_type = "Any"
        return f"list[{item_type}]"
    elif schema_type == "object":
        return "dict[str, Any]"
    return "Any"


def generate_class(
    name: str, schema: dict[str, Any], base_class: str = "BaseModel"
) -> str:
    """Generate a Python class from a JSON schema definition."""
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Generate class fields
    fields = []
    for prop_name, prop_schema in properties.items():
        prop_type = create_python_type(
            prop_schema.get("type", "string"), prop_schema, prop_name
        )
        default = "None" if prop_name not in required else "..."
        fields.append(f"    {prop_name}: {prop_type} = field(default={default})")

    # Generate class docstring
    description = schema.get("description", "")
    docstring = f'    """{description}"""' if description else ""

    # Generate class definition
    class_def = f"""@dataclass
class {name}({base_class}):
{docstring}
"""

    # Add fields
    if fields:
        class_def += "\n".join(fields) + "\n"

    return class_def


def generate_all_classes(schema_data: dict[str, Any]) -> str:
    """Generate all Python classes from the schema."""
    definitions = schema_data.get("definitions", {})

    # Generate imports
    imports = """from typing import Any, TypeVar, Union, get_type_hints, Literal
from dataclasses import dataclass, field
from enum import Enum

T = TypeVar('T')

class MessageType(Enum):
    REQUEST = "request"
    NOTIFICATION = "notification"
    RESPONSE = "response"

"""

    # Generate base class
    base_class = """@dataclass
class BaseModel:
    \"\"\"Base class for all MCP models.\"\"\"
    
    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        \"\"\"Create an instance from a dictionary.\"\"\"
        return cls(**data)
    
    def to_dict(self) -> dict[str, Any]:
        \"\"\"Convert the instance to a dictionary.\"\"\"
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    @classmethod
    def get_message_type(cls) -> MessageType:
        \"\"\"Get the type of message this class represents.\"\"\"
        if cls.__name__.endswith('Request'):
            return MessageType.REQUEST
        elif cls.__name__.endswith('Notification'):
            return MessageType.NOTIFICATION
        elif cls.__name__.endswith('Result') or cls.__name__.endswith('Response'):
            return MessageType.RESPONSE
        return MessageType.REQUEST  # Default to request if unknown

"""

    # Generate classes
    classes = []
    for name, schema in definitions.items():
        # Skip empty classes
        if not schema.get("properties"):
            continue

        class_def = generate_class(name, schema)
        classes.append(class_def)

    # Combine everything
    return imports + base_class + "\n\n".join(classes)


def main():
    """Main function to generate Python classes from schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "2025-03-26-schema.json")

    # Read schema file
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    # Generate Python classes
    python_code = generate_all_classes(schema_data)

    # Write to output file
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "sema4ai", "mcp_core", "mcp_models.py"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(python_code)

    print(f"Generated Python classes in {output_path}")


if __name__ == "__main__":
    main()
