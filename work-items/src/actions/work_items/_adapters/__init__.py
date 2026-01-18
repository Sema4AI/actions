"""
Adapters for work item storage backends.
"""

from ._base import BaseAdapter
from ._sqlite import SQLiteAdapter

__all__ = ["BaseAdapter", "SQLiteAdapter"]
