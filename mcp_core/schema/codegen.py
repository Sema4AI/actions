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


class TextIndenter:
    """Helper class to manage indentation in generated code."""

    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size
        self.current_indent = 0
        self.lines: list[str] = []

    def indent(self) -> None:
        """Increase the current indentation level."""
        self.current_indent += self.indent_size

    def dedent(self) -> None:
        """Decrease the current indentation level."""
        self.current_indent = max(0, self.current_indent - self.indent_size)

    def add_line(self, line: str, extra_indent: int = 0) -> None:
        """Add a line with the current indentation plus extra indentation levels."""
        if line.strip():
            self.lines.append(
                " " * (self.current_indent + extra_indent * self.indent_size) + line
            )
        else:
            self.lines.append("")

    def add_lines(self, lines: list[str]) -> None:
        """Add multiple lines with the current indentation."""
        for line in lines:
            self.add_line(line)

    def add_block(self, block: str) -> None:
        """Add a block of text, preserving relative indentation."""
        lines = block.split("\n")
        for line in lines:
            self.add_line(line)

    def get_text(self) -> str:
        """Get the final text with proper indentation."""
        return "\n".join(self.lines)

    def clear(self) -> None:
        """Clear all lines and reset indentation."""
        self.lines = []
        self.current_indent = 0


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
                items.get("type", "string"),
                items,
                parent_name=parent_name,
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
            return make_params_class_name(parent_name, field_name)
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

    # Create indenter for the docstring
    indenter = TextIndenter(indent_size=indent)

    # Split into words and build lines
    words = text.split()
    current_line = []
    current_length = 0

    for word in words:
        # If adding this word would exceed width, start a new line
        if current_length + len(word) + 1 > width:
            indenter.add_line(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1

    if current_line:
        indenter.add_line(" ".join(current_line))

    # Get the final text and wrap it in triple quotes
    lines = indenter.get_text().split("\n")
    if len(lines) == 1:
        return f'    """{lines[0]}"""'
    else:
        # Create a new indenter for the final docstring formatting
        final_indenter = TextIndenter(indent_size=4)
        final_indenter.add_line('"""', extra_indent=1)
        for line in lines:
            final_indenter.add_line(line, extra_indent=1)
        final_indenter.add_line('"""', extra_indent=1)
        return final_indenter.get_text()


def make_params_class_name(parent_name: str, field_name: str) -> str:
    """Generate a class name for a params object, avoiding double Params suffixes.

    Args:
        parent_name: The name of the parent class
        field_name: The name of the field

    Returns:
        A class name for the params object
    """
    # First try the standard format
    base_name = f"{parent_name}{field_name.capitalize()}"

    # If the name already contains "Params", don't add it again
    if "Params" in base_name:
        return base_name

    return f"{base_name}Params"


def generate_class(
    name: str,
    schema: dict[str, Any],
    definitions: dict[str, Any],
    base_class: str = "MCPBaseModel",
) -> tuple[str, list[str]]:
    """Generate a Python class from a JSON schema definition.

    Args:
        name: The name of the class to generate
        schema: The JSON schema for the class
        definitions: All available type definitions
        base_class: The base class to inherit from

    Returns:
        tuple[str, list[str]]: The generated class definition and a list of nested class definitions
    """
    # For Result class, ensure it has no properties
    if name == "Result":
        schema = {"type": "object", "properties": {}, "required": []}

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
            nested_name = make_params_class_name(name, prop_name)
            nested_class, nested_nested = generate_class(
                nested_name, prop_schema, definitions
            )
            nested_classes.append(nested_class)
            nested_classes.extend(nested_nested)

    # Generate class fields
    required_fields_no_default = []  # Fields that are required and have no default
    required_fields_with_default = []  # Fields that are required but have a default
    optional_fields = []  # Optional fields (all have defaults)
    field_types = {}  # Store field types for from_dict generation

    # Add jsonrpc and id fields for Request classes if they don't already exist
    if name.endswith("Request"):
        if "jsonrpc" not in properties:
            required_fields_with_default.append(
                'jsonrpc: "Literal[\'2.0\']" = field(default="2.0")'
            )
            field_types["jsonrpc"] = "Literal['2.0']"
        if "id" not in properties:
            required_fields_no_default.append('id: "RequestId"')
            field_types["id"] = "RequestId"

    for prop_name, prop_schema in properties.items():
        prop_type = create_python_type(
            prop_schema.get("type", "string"), prop_schema, prop_name, name
        )
        field_types[prop_name] = prop_type

        # Check for const values
        const_value = prop_schema.get("const")
        if const_value is not None:
            # For const fields, always set the default value
            if isinstance(const_value, str):
                default_value = f'field(default="{const_value}")'
            else:
                default_value = f"field(default={const_value})"
            if prop_name in required:
                required_fields_with_default.append(
                    f'{prop_name}: "{prop_type}" = {default_value}'
                )
            else:
                optional_fields.append(f'{prop_name}: "{prop_type}" = {default_value}')
        elif prop_name not in required:
            # For optional fields, wrap type in union with None and set default
            prop_type = f"None | {prop_type}"
            optional_fields.append(f'{prop_name}: "{prop_type}" = field(default=None)')
        else:
            # For required fields without const, just specify the type without default
            required_fields_no_default.append(f'{prop_name}: "{prop_type}"')

    # Combine fields in the correct order: required without defaults, required with defaults, optional
    fields = required_fields_no_default + required_fields_with_default + optional_fields

    # Generate class docstring
    description = schema.get("description", "")
    docstring = wrap_docstring(description) if description else ""

    # Create indenter for the class
    indenter = TextIndenter()

    # Determine the base class for this class
    if name.endswith("Result") and name != "Result":
        actual_base_class = "Result"
    else:
        actual_base_class = base_class

    # Generate class definition
    indenter.add_line("@dataclass")
    indenter.add_line(f"class {name}({actual_base_class}):")
    if docstring:
        indenter.add_block(docstring)
    indenter.add_line("")

    # Add fields
    if fields:
        indenter.indent()
        for field in fields:
            indenter.add_line(field)
        indenter.dedent()
        indenter.add_line("")

    # Generate from_dict method
    indenter.indent()
    indenter.add_line("@classmethod")
    indenter.add_line("def from_dict(cls: Type[T], data: dict[str, Any]) -> T:")
    indenter.add_line('"""Create an instance from a dictionary."""', extra_indent=1)
    indenter.add_line("if not isinstance(data, dict):", extra_indent=1)
    indenter.add_line(
        'raise ValueError(f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}")',
        extra_indent=2,
    )
    indenter.add_line("kwargs = {}", extra_indent=1)
    indenter.add_line("", extra_indent=0)

    # Add field processing for each field
    for field_name, field_type in field_types.items():
        indenter.add_line(f"# Process {field_name}", extra_indent=1)
        indenter.add_line(f"value = data.get({repr(field_name)})", extra_indent=1)

        # Handle different field types
        if "list[" in field_type:
            # Handle lists
            indenter.add_line("if value is not None:", extra_indent=1)
            indenter.add_line("if not isinstance(value, list):", extra_indent=2)
            indenter.add_line(
                f'raise ValueError(f"Expected a list for field {field_name}, got {{type(value)}}")',
                extra_indent=3,
            )
            item_type = field_type[5:-1]  # Extract type from list[type]
            indenter.add_line("converted_items = []", extra_indent=2)
            indenter.add_line("for item in value:", extra_indent=2)
            # Check if the item type is a union
            if "|" in item_type:
                types = [t.strip() for t in item_type.split("|")]
                indenter.add_line(
                    "# Try to disambiguate using const fields", extra_indent=3
                )
                indenter.add_line("if not isinstance(item, dict):", extra_indent=3)
                indenter.add_line(
                    f'raise ValueError(f"Expected a dict for union type {item_type}, got {{type(item)}}")',
                    extra_indent=4,
                )
                indenter.add_line("type_value = item.get('type')", extra_indent=3)
                indenter.add_line("type_to_class = {}", extra_indent=3)
                indenter.add_line("required_props_map = {}", extra_indent=3)
                for t in types:
                    if t != "None":
                        type_schema = definitions.get(t, {})
                        properties_ = type_schema.get("properties", {})
                        required_ = type_schema.get("required", [])
                        found_const = False
                        for prop_name_, prop_schema_ in properties_.items():
                            if "const" in prop_schema_:
                                const_value = prop_schema_["const"]
                                indenter.add_line(
                                    f"type_to_class[{repr(const_value)}] = {t}",
                                    extra_indent=3,
                                )
                                found_const = True
                        if not found_const and required_:
                            indenter.add_line(
                                f"required_props_map[{t}] = {required_}",
                                extra_indent=3,
                            )
                indenter.add_line(
                    "if type_value is not None and type_value in type_to_class:",
                    extra_indent=3,
                )
                indenter.add_line(
                    "converted_items.append(type_to_class[type_value].from_dict(item))",
                    extra_indent=4,
                )
                indenter.add_line("else:", extra_indent=3)
                indenter.add_line(
                    "# Try to disambiguate by required properties", extra_indent=4
                )
                indenter.add_line("matches = []", extra_indent=4)
                indenter.add_line(
                    "for type_name, reqs in required_props_map.items():",
                    extra_indent=4,
                )
                indenter.add_line("if all(r in item for r in reqs):", extra_indent=5)
                indenter.add_line("matches.append(type_name)", extra_indent=6)
                indenter.add_line("if len(matches) == 1:", extra_indent=4)
                indenter.add_line(
                    "converted_items.append(matches[0].from_dict(item))",
                    extra_indent=5,
                )
                indenter.add_line("elif len(matches) > 1:", extra_indent=4)
                indenter.add_line(
                    "match_details = [f'{name} (requires any of {required_props_map[name]})' for name in matches]",
                    extra_indent=5,
                )
                indenter.add_line(
                    "raise ValueError(f\"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}\")",
                    extra_indent=5,
                )
                indenter.add_line("else:", extra_indent=4)
                indenter.add_line(
                    "available_fields = list(item.keys())", extra_indent=5
                )
                indenter.add_line(
                    "type_details = [f'{name} (requires any of {required_props_map[name]})' for name in required_props_map]",
                    extra_indent=5,
                )
                indenter.add_line(
                    "raise ValueError(f\"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}\")",
                    extra_indent=5,
                )
            else:
                if (
                    item_type
                    in [
                        "str",
                        "int",
                        "float",
                        "bool",
                        "ProgressToken",
                        "RequestId",
                        "Role",
                        "LoggingLevel",
                    ]
                    or "Literal[" in item_type
                ):
                    indenter.add_line("converted_items.append(item)", extra_indent=3)
                else:
                    indenter.add_line(
                        f"converted_items.append({item_type}.from_dict(item))",
                        extra_indent=3,
                    )
            indenter.add_line("value = converted_items", extra_indent=2)
        elif field_type in ["str", "int", "float", "bool"]:
            pass
        elif "Literal[" in field_type:
            pass
        elif field_type in ["ProgressToken", "RequestId", "Role", "LoggingLevel"]:
            pass
        elif "|" in field_type:
            indenter.add_line("if value is not None:", extra_indent=1)
            indenter.add_line("if isinstance(value, dict):", extra_indent=2)
            indenter.add_line(
                "# Try to disambiguate using const fields", extra_indent=3
            )
            indenter.add_line("type_value = value.get('type')", extra_indent=3)
            indenter.add_line("type_to_class = {}", extra_indent=3)
            indenter.add_line("required_props_map = {}", extra_indent=3)
            types = [t.strip() for t in field_type.split("|")]
            for t in types:
                if t != "None":
                    type_schema = definitions.get(t, {})
                    properties_ = type_schema.get("properties", {})
                    required_ = type_schema.get("required", [])
                    found_const = False
                    for prop_name_, prop_schema_ in properties_.items():
                        if "const" in prop_schema_:
                            const_value = prop_schema_["const"]
                            indenter.add_line(
                                f"type_to_class[{repr(const_value)}] = {t}",
                                extra_indent=3,
                            )
                            found_const = True
                    if not found_const and required_:
                        indenter.add_line(
                            f"required_props_map[{t}] = {required_}", extra_indent=3
                        )
            indenter.add_line(
                "if type_value is not None and type_value in type_to_class:",
                extra_indent=3,
            )
            indenter.add_line(
                "value = type_to_class[type_value].from_dict(value)", extra_indent=4
            )
            indenter.add_line("else:", extra_indent=3)
            indenter.add_line(
                "# Try to disambiguate by required properties", extra_indent=4
            )
            indenter.add_line("matches = []", extra_indent=4)
            indenter.add_line(
                "for type_name, reqs in required_props_map.items():", extra_indent=4
            )
            indenter.add_line("if all(r in value for r in reqs):", extra_indent=5)
            indenter.add_line("matches.append(type_name)", extra_indent=6)
            indenter.add_line("if len(matches) == 1:", extra_indent=4)
            indenter.add_line("value = matches[0].from_dict(value)", extra_indent=5)
            indenter.add_line("elif len(matches) > 1:", extra_indent=4)
            indenter.add_line(
                "match_details = [f'{name} (requires any of {required_props_map[name]})' for name in matches]",
                extra_indent=5,
            )
            indenter.add_line(
                "raise ValueError(f\"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}\")",
                extra_indent=5,
            )
            indenter.add_line("else:", extra_indent=4)
            indenter.add_line("available_fields = list(value.keys())", extra_indent=5)
            indenter.add_line(
                "type_details = [f'{name} (requires any of {required_props_map[name]})' for name in required_props_map]",
                extra_indent=5,
            )
            indenter.add_line(
                "raise ValueError(f\"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}\")",
                extra_indent=5,
            )
        elif field_type == "dict[str, Any]":
            pass
        else:
            indenter.add_line("if value is not None:", extra_indent=1)
            if (
                field_type
                in [
                    "str",
                    "int",
                    "float",
                    "bool",
                    "ProgressToken",
                    "RequestId",
                    "LoggingLevel",
                ]
                or "Literal[" in field_type
            ):
                pass
            else:
                indenter.add_line(
                    f"value = {field_type}.from_dict(value)", extra_indent=2
                )

        indenter.add_line(f"kwargs[{repr(field_name)}] = value", extra_indent=1)
        indenter.add_line("", extra_indent=0)

    indenter.add_line("return cls(**kwargs)", extra_indent=1)
    indenter.add_line("", extra_indent=0)

    return indenter.get_text(), nested_classes


def generate_all_classes(schema_data: dict[str, Any]) -> str:
    """Generate all Python classes from the schema."""
    definitions = schema_data.get("definitions", {})

    # Create indenter for the entire file
    indenter = TextIndenter()

    # Generate imports
    indenter.add_block(
        """from typing import Any, TypeVar, Literal, Type
from dataclasses import dataclass, field
from sema4ai.mcp_core.mcp_base_model import MCPBaseModel

T = TypeVar('T')
"""
    )
    indenter.add_line("")

    # Generate classes
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
    # First handle the Result class if it exists
    if "Result" in definitions:
        schema = definitions["Result"]
        class_def, nested_classes = generate_class("Result", schema, definitions)
        indenter.add_block(class_def)
        for nested_class in nested_classes:
            indenter.add_block(nested_class)

    # Then handle all other classes
    for name, schema in definitions.items():
        if name == "Result":  # Skip Result as it was already handled
            continue

        # Handle types defined with type arrays first (like ProgressToken)
        if "type" in schema and isinstance(schema["type"], list):
            type_name = create_python_type(schema["type"], schema)
            indenter.add_line(f"# Type alias for {name.lower()}")
            indenter.add_line(f"{name} = {type_name}")
            indenter.add_line("")
            continue

        # Handle string enums as Literal types
        if "enum" in schema and schema.get("type") == "string":
            enum_values = [repr(x) for x in schema["enum"]]
            indenter.add_line(f"# Type alias for {name.lower()}")
            indenter.add_line(f"{name} = Literal[{', '.join(enum_values)}]")
            indenter.add_line("")
            continue

        # Skip empty classes that aren't referenced
        if not schema.get("properties") and name not in referenced_types:
            continue

        # If this is a referenced type but has no properties, check for special cases
        if not schema.get("properties") and name in referenced_types:
            if "type" in schema:
                # Handle basic types (like RequestId)
                type_name = create_python_type(schema["type"], schema)
                if name in ["RequestId", "ProgressToken", "Role", "LoggingLevel"]:
                    # Special case for RequestId and ProgressToken - make them type aliases
                    indenter.add_line(f"# Type alias for {name.lower()}")
                    indenter.add_line(f"{name} = {type_name}")
                    indenter.add_line("")
                else:
                    indenter.add_line(f"@dataclass")
                    indenter.add_line(f"class {name}(MCPBaseModel):")
                    if schema.get("description"):
                        indenter.add_block(
                            wrap_docstring(schema.get("description", ""))
                        )
                    indenter.indent()
                    indenter.add_line(f"value: {type_name} = field(default=None)")
                    indenter.dedent()
                    indenter.add_line("")
            else:
                # Fallback for unknown types
                indenter.add_line(f"@dataclass")
                indenter.add_line(f"class {name}(MCPBaseModel):")
                if schema.get("description"):
                    indenter.add_block(wrap_docstring(schema.get("description", "")))
                indenter.indent()
                indenter.add_line("value: Any = field(default=None)")
                indenter.dedent()
                indenter.add_line("")
        else:
            class_def, nested_classes = generate_class(name, schema, definitions)
            indenter.add_block(class_def)
            for nested_class in nested_classes:
                indenter.add_block(nested_class)

        # Check if this class has a method field with a const value
        properties = schema.get("properties", {})
        if "method" in properties and "const" in properties["method"]:
            method_value = properties["method"]["const"]
            method_to_class[method_value] = name

    # Generate class map with proper typing
    indenter.add_line("_class_map: dict[str, Type[MCPBaseModel]] = {")
    indenter.indent()
    for method, class_name in method_to_class.items():
        indenter.add_line(f"{repr(method)}: {class_name},")
    indenter.dedent()
    indenter.add_line("}")
    indenter.add_line("")

    return indenter.get_text()


def code_format(code: str) -> str:
    """Format code using ruff via stdin/stdout."""
    import subprocess

    try:
        result = subprocess.run(
            ["ruff", "format", "-"],
            input=code.encode("utf-8"),
            stdout=subprocess.PIPE,
            check=True,
        )
        return result.stdout.decode("utf-8")
    except Exception as e:
        print(f"Error formatting code using ruff: {e}")
        return code


def main():
    """Main function to generate Python classes from schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "2025-03-26-schema.json")

    # Read schema file
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    # Generate Python classes
    python_code = generate_all_classes(schema_data)

    # Format the code using ruff
    formatted_code = code_format(python_code)

    # Write to output file
    output_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "sema4ai",
        "mcp_core",
        "mcp_models",
        "_generated_mcp_models.py",
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_code)

    print(f"Generated and formatted Python classes in {output_path}")


if __name__ == "__main__":
    main()
