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
    name: str,
    schema: dict[str, Any],
    definitions: dict[str, Any],
    base_class: str = "BaseModel",
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
            nested_class, nested_nested = generate_class(
                nested_name, prop_schema, definitions
            )
            nested_classes.append(nested_class)
            nested_classes.extend(nested_nested)

    # Generate class fields
    required_fields = []
    optional_fields = []
    field_types = {}  # Store field types for from_dict generation

    for prop_name, prop_schema in properties.items():
        prop_type = create_python_type(
            prop_schema.get("type", "string"), prop_schema, prop_name, name
        )
        field_types[prop_name] = prop_type

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

    # Generate from_dict method
    from_dict_lines = []
    from_dict_lines.append("    @classmethod")
    from_dict_lines.append(
        "    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:"
    )
    from_dict_lines.append('        """Create an instance from a dictionary."""')
    from_dict_lines.append("        if not isinstance(data, dict):")
    from_dict_lines.append(
        f'            raise ValueError(f"Expected a dict instead of: {{type(data)}} to create type {{cls.__name__}}. Data: {{data}}")'
    )
    from_dict_lines.append("        kwargs = {}")

    # Add field processing for each field
    for field_name, field_type in field_types.items():
        from_dict_lines.append(f"        # Process {field_name}")
        from_dict_lines.append(f"        value = data.get({repr(field_name)})")

        # Handle different field types
        if "list[" in field_type:
            # Handle lists
            from_dict_lines.append("        if value is not None:")
            item_type = field_type[5:-1]  # Extract type from list[type]
            from_dict_lines.append("            if not isinstance(value, list):")
            from_dict_lines.append(
                f'                raise ValueError(f"Expected a list for field {field_name}, got {{type(value)}}")'
            )
            from_dict_lines.append("            converted_items = []")
            from_dict_lines.append("            for item in value:")
            from_dict_lines.append("                if isinstance(item, dict):")
            # Check if the item type is a union
            if "|" in item_type:
                types = [t.strip() for t in item_type.split("|")]
                from_dict_lines.append(
                    "                    # Try to disambiguate using const fields"
                )
                from_dict_lines.append(
                    "                    type_value = item.get('type')"
                )
                from_dict_lines.append("                    type_to_class = {}")
                from_dict_lines.append("                    required_props_map = {}")
                # For each type in the union, check if it has a const field or required properties
                for t in types:
                    if t != "None":
                        type_schema = definitions.get(t, {})
                        properties_ = type_schema.get("properties", {})
                        required_ = type_schema.get("required", [])
                        found_const = False
                        for prop_name_, prop_schema_ in properties_.items():
                            if "const" in prop_schema_:
                                const_value = prop_schema_["const"]
                                from_dict_lines.append(
                                    f"                    type_to_class[{repr(const_value)}] = {t}"
                                )
                                found_const = True
                        if not found_const and required_:
                            from_dict_lines.append(
                                f"                    required_props_map[{t}] = {required_}"
                            )
                from_dict_lines.append(
                    "                    if type_value is not None and type_value in type_to_class:"
                )
                from_dict_lines.append(
                    "                        converted_items.append(type_to_class[type_value].from_dict(item))"
                )
                from_dict_lines.append("                    else:")
                from_dict_lines.append(
                    "                        # Try to disambiguate by required properties"
                )
                from_dict_lines.append("                        matches = []")
                from_dict_lines.append(
                    "                        for type_name, reqs in required_props_map.items():"
                )
                from_dict_lines.append(
                    "                            if all(r in item for r in reqs):"
                )
                from_dict_lines.append(
                    "                                matches.append(type_name)"
                )
                from_dict_lines.append("                        if len(matches) == 1:")
                from_dict_lines.append(
                    "                            converted_items.append(matches[0].from_dict(item))"
                )
                from_dict_lines.append("                        elif len(matches) > 1:")
                from_dict_lines.append(
                    "                            match_details = [f'{name} (requires any of {required_props_map[name]})' for name in matches]"
                )
                from_dict_lines.append(
                    "                            raise ValueError(f\"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}\")"
                )
                from_dict_lines.append("                        else:")
                from_dict_lines.append(
                    "                            available_fields = list(item.keys())"
                )
                from_dict_lines.append(
                    "                            type_details = [f'{name} (requires any of {required_props_map[name]})' for name in required_props_map]"
                )
                from_dict_lines.append(
                    "                            raise ValueError(f\"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}\")"
                )
            else:
                # Skip from_dict for type aliases and basic types
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
                    ]
                    or "Literal[" in item_type
                ):
                    from_dict_lines.append(
                        "                    converted_items.append(item)"
                    )
                else:
                    from_dict_lines.append(
                        f"                    converted_items.append({item_type}.from_dict(item))"
                    )
            from_dict_lines.append("                else:")
            from_dict_lines.append("                    converted_items.append(item)")
            from_dict_lines.append("            value = converted_items")
        elif field_type in ["str", "int", "float", "bool"]:
            # Handle basic types - no conversion needed
            pass
        elif "Literal[" in field_type:
            # Handle literal types - no conversion needed
            pass
        elif field_type in ["ProgressToken", "RequestId", "Role"]:
            # Handle type aliases - no conversion needed
            pass
        elif "|" in field_type:
            # Handle union types
            from_dict_lines.append("        if value is not None:")
            types = [t.strip() for t in field_type.split("|")]
            from_dict_lines.append("            if isinstance(value, dict):")
            from_dict_lines.append(
                "                # Try to disambiguate using const fields"
            )
            from_dict_lines.append("                type_value = value.get('type')")
            from_dict_lines.append("                type_to_class = {}")
            from_dict_lines.append("                required_props_map = {}")
            for t in types:
                if t != "None":
                    type_schema = definitions.get(t, {})
                    properties_ = type_schema.get("properties", {})
                    required_ = type_schema.get("required", [])
                    found_const = False
                    for prop_name_, prop_schema_ in properties_.items():
                        if "const" in prop_schema_:
                            const_value = prop_schema_["const"]
                            from_dict_lines.append(
                                f"                type_to_class[{repr(const_value)}] = {t}"
                            )
                            found_const = True
                    if not found_const and required_:
                        from_dict_lines.append(
                            f"                required_props_map[{t}] = {required_}"
                        )
            from_dict_lines.append(
                "                if type_value is not None and type_value in type_to_class:"
            )
            from_dict_lines.append(
                "                    value = type_to_class[type_value].from_dict(value)"
            )
            from_dict_lines.append("                else:")
            from_dict_lines.append(
                "                    # Try to disambiguate by required properties"
            )
            from_dict_lines.append("                    matches = []")
            from_dict_lines.append(
                "                    for type_name, reqs in required_props_map.items():"
            )
            from_dict_lines.append(
                "                        if all(r in value for r in reqs):"
            )
            from_dict_lines.append(
                "                            matches.append(type_name)"
            )
            from_dict_lines.append("                    if len(matches) == 1:")
            from_dict_lines.append(
                "                        value = matches[0].from_dict(value)"
            )
            from_dict_lines.append("                    elif len(matches) > 1:")
            from_dict_lines.append(
                "                        match_details = [f'{name} (requires any of {required_props_map[name]})' for name in matches]"
            )
            from_dict_lines.append(
                "                        raise ValueError(f\"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}\")"
            )
            from_dict_lines.append("                    else:")
            from_dict_lines.append(
                "                        available_fields = list(value.keys())"
            )
            from_dict_lines.append(
                "                        type_details = [f'{name} (requires any of {required_props_map[name]})' for name in required_props_map]"
            )
            from_dict_lines.append(
                "                        raise ValueError(f\"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}\")"
            )
        elif field_type == "dict[str, Any]":
            # Handle dictionary type - no conversion needed
            pass
        else:
            # Handle custom types
            from_dict_lines.append("        if value is not None:")
            # Skip from_dict for type aliases and basic types
            if (
                field_type
                in ["str", "int", "float", "bool", "ProgressToken", "RequestId"]
                or "Literal[" in field_type
            ):
                pass
            else:
                from_dict_lines.append(
                    f"            value = {field_type}.from_dict(value)"
                )

        from_dict_lines.append(f"        kwargs[{repr(field_name)}] = value")
        from_dict_lines.append("")

    from_dict_lines.append("        return cls(**kwargs)")
    from_dict_lines.append("")

    # Generate class definition
    class_def = f"""@dataclass
class {name}({base_class}):
{docstring}
"""

    # Add fields
    if fields:
        class_def += "\n".join(fields) + "\n\n"

    # Add from_dict method
    class_def += "\n".join(from_dict_lines)

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
                if name in ["RequestId", "ProgressToken", "Role"]:
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
            class_def, nested_classes = generate_class(name, schema, definitions)
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
    \n    Args:
        data: Dictionary containing the model data
        \n    Returns:
        An instance of the appropriate MCP model class
        \n    Raises:
        ValueError: If the method field is missing or no matching class is found
    \"\"\"
    if "method" not in data:
        raise ValueError("Input dictionary must contain a 'method' field")
        \n    method = data["method"]
    if method not in _class_map:
        raise ValueError(f"No MCP model class found for method: {method}")
        \n    return _class_map[method].from_dict(data)
"""

    # Combine everything
    return imports + "\n\n".join(classes) + "\n\n" + class_map + factory_function


def code_format(code: str) -> str:
    """Format code using ruff via stdin/stdout."""
    import subprocess

    result = subprocess.run(
        ["ruff", "format", "-"],
        input=code.encode("utf-8"),
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8")


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
        os.path.dirname(__file__), "..", "src", "sema4ai", "mcp_core", "mcp_models.py"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_code)

    print(f"Generated and formatted Python classes in {output_path}")


if __name__ == "__main__":
    main()


def generate_union_type_disambiguation(cls: type, union_type: type) -> str:
    """Generate code to disambiguate between types in a union."""
    if not hasattr(union_type, "__origin__") or union_type.__origin__ is not Union:
        return ""

    # Get the actual types in the union
    union_types = get_args(union_type)
    if not union_types:
        return ""

    # Get the required fields for each type from the schema
    required_fields = {}
    for t in union_types:
        if hasattr(t, "__annotations__"):
            # Get the required fields from the schema
            schema = get_schema_for_type(t)
            if schema and "required" in schema:
                required_fields[t] = schema["required"]
            else:
                # If no required fields in schema, use all fields
                required_fields[t] = list(t.__annotations__.keys())

    # Generate the disambiguation code
    code = []
    code.append("    @classmethod")
    code.append("    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:")
    code.append('        """Create an instance from a dictionary."""')
    code.append("        if not isinstance(data, dict):")
    code.append(
        '            raise ValueError(f"Expected a dict instead of: {type(data)} to create type {cls.__name__}. Data: {data}")'
    )
    code.append("        kwargs = {}")
    code.append("")
    code.append("        # Create a mapping of required fields for each type")
    code.append("        required_props_map = {")
    for t, fields in required_fields.items():
        code.append(f"            {t.__name__}: {fields},")
    code.append("        }")
    code.append("")
    code.append("        # Check which type's required fields are present")
    code.append("        matches = []")
    code.append("        for type_name, required_fields in required_props_map.items():")
    code.append("            if any(field in data for field in required_fields):")
    code.append("                matches.append(type_name)")
    code.append("")
    code.append("        if len(matches) == 1:")
    code.append("            # Use globals()[type_name] to get the class by name")
    code.append("            return globals()[matches[0]].from_dict(data)")
    code.append("        elif len(matches) > 1:")
    code.append(
        "            match_details = [f'{name} (requires any of {required_props_map[name]})' for name in matches]"
    )
    code.append(
        "            raise ValueError(f\"Ambiguous match for union type. Multiple types match: {'; '.join(match_details)}\")"
    )
    code.append("        else:")
    code.append("            available_fields = list(data.keys())")
    code.append(
        "            type_details = [f'{name} (requires any of {required_props_map[name]})' for name in required_props_map]"
    )
    code.append(
        "            raise ValueError(f\"No match for union type. Available fields: {available_fields}. Expected one of: {'; '.join(type_details)}\")"
    )
    code.append("")
    code.append("        return cls(**kwargs)")

    return "\n".join(code)


def generate_class(cls: type) -> str:
    """Generate Python code for a Pydantic model class."""
    code = []
    code.append(f"class {cls.__name__}(BaseModel):")
    code.append('    """Generated from JSON Schema."""')
    code.append("")

    # Add fields
    for name, field in cls.model_fields.items():
        field_type = field.annotation
        field_info = field.json_schema_extra or {}
        description = field_info.get("description", "")
        if description:
            code.append(f"    # {description}")
        code.append(f"    {name}: {field_type}")
        code.append("")

    # Add union type disambiguation if needed
    for name, field in cls.model_fields.items():
        field_type = field.annotation
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
            code.append(generate_union_type_disambiguation(cls, field_type))
            code.append("")

    return "\n".join(code)
