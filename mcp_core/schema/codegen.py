import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

T = TypeVar("T")


def create_python_type(
    schema_type: str | list[str],
    schema: dict[str, Any],
    field_name: str = "",
    parent_name: str = "",
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
                    sub_schema.get("type", "string"),
                    sub_schema,
                    parent_name=parent_name,
                )
                types.append(sub_type)
        return " | ".join(types)

    # Handle array of types
    if isinstance(schema_type, list):
        types = []
        for type_name in schema_type:
            if type_name == "string":
                types.append("str")
            elif type_name == "integer":
                types.append("int")
            elif type_name == "number":
                types.append("float")
            elif type_name == "boolean":
                types.append("bool")
            else:
                types.append("Any")
        return " | ".join(types)

    if schema_type == "string":
        if "enum" in schema:
            return f"Literal[{', '.join(repr(x) for x in schema['enum'])}]"
        # Handle const values for string types
        if "const" in schema:
            return f"Literal[{repr(schema['const'])}]"
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
            item_type = create_python_type(
                items.get("type", "string"), items, parent_name=parent_name
            )
        else:
            item_type = "Any"
        return f"list[{item_type}]"
    elif schema_type == "object":
        # For objects with additionalProperties and no specific properties, use dict
        if "additionalProperties" in schema and not schema.get("properties"):
            return "dict[str, Any]"
        # For object types with properties, return a reference to the generated class name
        if parent_name and field_name and schema.get("properties"):
            return f"{parent_name}{field_name.capitalize()}Params"
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
) -> tuple[str, list[str]]:
    """Generate a Python class from a JSON schema definition.

    Returns:
        tuple[str, list[str]]: The generated class definition and a list of nested class definitions
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Generate nested classes for object properties
    nested_classes = []
    for prop_name, prop_schema in properties.items():
        # Skip generating nested classes for objects with only additionalProperties
        if (
            prop_schema.get("type") == "object"
            and prop_schema.get("properties")
            and not (
                prop_schema.get("additionalProperties")
                and not prop_schema.get("properties")
            )
        ):
            nested_name = f"{name}{prop_name.capitalize()}Params"
            nested_class, nested_nested = generate_class(nested_name, prop_schema)
            nested_classes.append(nested_class)
            nested_classes.extend(nested_nested)

    # Generate class fields
    required_fields = []
    optional_fields = []

    for prop_name, prop_schema in properties.items():
        prop_type = create_python_type(
            prop_schema.get("type", "string"), prop_schema, prop_name, name
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

    return class_def, nested_classes


def generate_all_classes(schema_data: dict[str, Any]) -> str:
    """Generate all Python classes from the schema."""
    definitions = schema_data.get("definitions", {})

    # Generate imports
    imports = """from typing import Any, TypeVar, Literal, Type
from dataclasses import dataclass, field
from sema4ai.mcp_core.mcp_base_model import BaseModel

T = TypeVar('T')

"""

    # Generate classes
    classes = []
    method_to_class: dict[str, str] = {}

    # First pass: collect all referenced types and their schemas
    referenced_types = {}
    for name, schema in definitions.items():
        properties = schema.get("properties", {})
        for prop_schema in properties.values():
            if "$ref" in prop_schema:
                ref_type = prop_schema["$ref"].split("/")[-1]
                if ref_type not in referenced_types:
                    referenced_types[ref_type] = None  # Will be filled in second pass
            elif "anyOf" in prop_schema:
                for sub_schema in prop_schema["anyOf"]:
                    if "$ref" in sub_schema:
                        ref_type = sub_schema["$ref"].split("/")[-1]
                        if ref_type not in referenced_types:
                            referenced_types[
                                ref_type
                            ] = None  # Will be filled in second pass

    # Second pass: fill in referenced type schemas
    for name, schema in definitions.items():
        if name in referenced_types:
            referenced_types[name] = schema

    # Third pass: generate classes for all types
    for name, schema in definitions.items():
        # Handle types defined with type arrays first (like ProgressToken)
        if "type" in schema and isinstance(schema["type"], list):
            print("found type array", name)
            type_name = create_python_type(schema["type"], schema)
            class_def = f"""# Type alias for {name.lower()}
{name} = {type_name}
"""
            classes.append(class_def)
            continue

        # Handle string enums as Literal types
        if "enum" in schema and schema.get("type") == "string":
            enum_values = [repr(x) for x in schema["enum"]]
            class_def = f"""# Type alias for {name.lower()}
{name} = Literal[{', '.join(enum_values)}]
"""
            classes.append(class_def)
            continue

        # Skip empty classes that aren't referenced
        if not schema.get("properties") and name not in referenced_types:
            continue

        # If this is a referenced type but has no properties, check for special cases
        if not schema.get("properties") and name in referenced_types:
            if "type" in schema:
                # Handle basic types (like RequestId)
                type_name = create_python_type(schema["type"], schema)
                if name in ["RequestId", "ProgressToken"]:
                    # Special case for RequestId and ProgressToken - make them type aliases
                    class_def = f"""# Type alias for {name.lower()}
{name} = {type_name}
"""
                    classes.append(class_def)
                else:
                    class_def = f"""@dataclass
class {name}(BaseModel):
{wrap_docstring(schema.get('description', ''))}
    value: {type_name} = field(default=None)
"""
                    classes.append(class_def)
            else:
                # Fallback for unknown types
                class_def = f"""@dataclass
class {name}(BaseModel):
{wrap_docstring(schema.get('description', ''))}
    value: Any = field(default=None)
"""
                classes.append(class_def)
        else:
            class_def, nested_classes = generate_class(name, schema)
            classes.append(class_def)
            classes.extend(nested_classes)

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
    return imports + "\n\n".join(classes) + "\n\n" + class_map + factory_function


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
