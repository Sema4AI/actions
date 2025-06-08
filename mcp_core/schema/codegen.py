import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Literal, Type, TypeVar, Union

T = TypeVar("T")


class MessageType(Enum):
    REQUEST = "request"
    NOTIFICATION = "notification"
    RESPONSE = "response"


def create_python_type(
    schema_type: str, schema: dict[str, Any], field_name: str = ""
) -> str:
    """Convert JSON schema type to Python type annotation."""
    # Handle $ref first
    if "$ref" in schema:
        # Extract the type name from the ref (e.g., "#/definitions/Role" -> "Role")
        return schema["$ref"].split("/")[-1]

    # Handle anyOf types
    if "anyOf" in schema:
        types = []
        for sub_schema in schema["anyOf"]:
            if "$ref" in sub_schema:
                # Extract the type name from the ref (e.g., "#/definitions/TextContent" -> "TextContent")
                ref_type = sub_schema["$ref"].split("/")[-1]
                types.append(ref_type)
            else:
                # Handle inline type definitions
                sub_type = create_python_type(
                    sub_schema.get("type", "string"), sub_schema
                )
                types.append(sub_type)
        return " | ".join(types)

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


def wrap_docstring(text: str, indent: int = 4) -> str:
    """Wrap a docstring at 89 columns, respecting indentation."""
    if not text:
        return ""

    # Trim whitespace and normalize newlines
    text = text.strip()

    # Calculate available width (89 - indentation - quotes)
    width = 89 - indent - 3  # 3 for quotes and space

    # Split into words and build lines
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        # If adding this word would exceed width, start a new line
        if current_length + len(word) + 1 > width:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1

    if current_line:
        lines.append(" ".join(current_line))

    # Join lines with proper indentation, ensuring no trailing newline
    if len(lines) == 1:
        return f'    """{lines[0]}"""'
    else:
        return (
            f'    """{lines[0]}\n'
            + "\n".join(f"    {line}" for line in lines[1:])
            + '"""'
        )


def generate_class(
    name: str, schema: dict[str, Any], base_class: str = "BaseModel"
) -> str:
    """Generate a Python class from a JSON schema definition."""
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Generate class fields
    required_fields = []
    optional_fields = []

    for prop_name, prop_schema in properties.items():
        prop_type = create_python_type(
            prop_schema.get("type", "string"), prop_schema, prop_name
        )

        if prop_name not in required:
            # For optional fields, wrap type in union with None and set default
            prop_type = f"None | {prop_type}"
            optional_fields.append(
                f'    {prop_name}: "{prop_type}" = field(default=None)'
            )
        else:
            # For required fields, just specify the type without default
            required_fields.append(f'    {prop_name}: "{prop_type}"')

    # Combine fields with required ones first
    fields = required_fields + optional_fields

    # Generate class docstring
    description = schema.get("description", "")
    docstring = wrap_docstring(description) if description else ""

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
    imports = """from typing import Any, TypeVar, Literal, Type
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
    method_to_class: dict[str, str] = {}

    # First pass: collect all referenced types
    referenced_types = set()
    for schema in definitions.values():
        properties = schema.get("properties", {})
        for prop_schema in properties.values():
            if "$ref" in prop_schema:
                ref_type = prop_schema["$ref"].split("/")[-1]
                referenced_types.add(ref_type)
            elif "anyOf" in prop_schema:
                for sub_schema in prop_schema["anyOf"]:
                    if "$ref" in sub_schema:
                        ref_type = sub_schema["$ref"].split("/")[-1]
                        referenced_types.add(ref_type)

    # Second pass: generate classes for all types
    for name, schema in definitions.items():
        # Skip empty classes
        if not schema.get("properties") and name not in referenced_types:
            continue

        # If this is a referenced type but has no properties, check for special cases
        if not schema.get("properties") and name in referenced_types:
            if "enum" in schema:
                # Handle enum types (like Role)
                enum_values = []
                for value in schema["enum"]:
                    # Convert value to uppercase for enum name
                    enum_name = str(value).upper()
                    enum_values.append(f"    {enum_name} = {repr(value)}")

                class_def = f"""class {name}(Enum):
{wrap_docstring(schema.get('description', ''))}
{chr(10).join(enum_values)}
"""
            elif "type" in schema:
                # Handle basic types (like RequestId)
                type_name = create_python_type(schema["type"], schema)
                if name == "RequestId":
                    # Special case for RequestId - make it a type alias
                    class_def = f"""# Type alias for request identifiers
{name} = int | str
"""
                else:
                    class_def = f"""@dataclass
class {name}(BaseModel):
{wrap_docstring(schema.get('description', ''))}
    value: {type_name} = field(default=None)
"""
            else:
                # Fallback for unknown types
                class_def = f"""@dataclass
class {name}(BaseModel):
{wrap_docstring(schema.get('description', ''))}
    value: Any = field(default=None)
"""
        else:
            class_def = generate_class(name, schema)

        classes.append(class_def)

        # Check if this class has a method field with a const value
        properties = schema.get("properties", {})
        if "method" in properties and "const" in properties["method"]:
            method_value = properties["method"]["const"]
            method_to_class[method_value] = name

    # Generate class map with proper typing
    class_map = "_class_map: dict[str, Type[BaseModel]] = {\n"
    for method, class_name in method_to_class.items():
        class_map += f"    {repr(method)}: {class_name},\n"
    class_map += "}\n\n"

    # Generate factory function
    factory_function = """def create_mcp_model(data: dict[str, Any]) -> BaseModel:
    \"\"\"Create an MCP model instance from a dictionary based on its method field.
    
    Args:
        data: Dictionary containing the model data
        
    Returns:
        An instance of the appropriate MCP model class
        
    Raises:
        ValueError: If the method field is missing or no matching class is found
    \"\"\"
    if "method" not in data:
        raise ValueError("Input dictionary must contain a 'method' field")
        
    method = data["method"]
    if method not in _class_map:
        raise ValueError(f"No MCP model class found for method: {method}")
        
    return _class_map[method].from_dict(data)
"""

    # Combine everything
    return (
        imports
        + base_class
        + "\n\n".join(classes)
        + "\n\n"
        + class_map
        + factory_function
    )


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
