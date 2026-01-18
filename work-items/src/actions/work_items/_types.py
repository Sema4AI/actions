"""
Type definitions for work items.

Based on robocorp-workitems (Apache 2.0 License).
"""

from enum import Enum
from typing import Any, Dict, List, Union

# JSON-compatible types
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


class State(str, Enum):
    """Work item processing states."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"


class ExceptionType(str, Enum):
    """Types of exceptions that can occur during work item processing."""

    # Business exception - expected failure that should not be retried
    BUSINESS = "BUSINESS"
    # Application exception - unexpected failure that may be retried
    APPLICATION = "APPLICATION"
