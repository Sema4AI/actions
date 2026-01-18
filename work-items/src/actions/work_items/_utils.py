"""
Utility functions for work items.

Based on robocorp-workitems (Apache 2.0 License).
"""

import json
import os
from typing import Any, Optional


def truncate(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to max_length characters with ellipsis.

    Args:
        text: The text to truncate.
        max_length: Maximum length including ellipsis.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def json_dumps(obj: Any, indent: Optional[int] = None) -> str:
    """
    Serialize object to JSON string with consistent formatting.

    Args:
        obj: Object to serialize.
        indent: Indentation level (None for compact).

    Returns:
        JSON string.
    """
    return json.dumps(obj, indent=indent, default=str, ensure_ascii=False)


def required_env(name: str, default: Optional[str] = None) -> str:
    """
    Get required environment variable.

    Args:
        name: Environment variable name.
        default: Default value if not set.

    Returns:
        Environment variable value.

    Raises:
        RuntimeError: If variable is not set and no default provided.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Required environment variable not set: {name}")
    return value


def optional_env(name: str, default: str = "") -> str:
    """
    Get optional environment variable with default.

    Args:
        name: Environment variable name.
        default: Default value if not set.

    Returns:
        Environment variable value or default.
    """
    return os.environ.get(name, default)
