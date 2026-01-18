"""
Adapters for work item storage backends.

Available adapters:
- SQLiteAdapter: Persistent local storage using SQLite database
- FileAdapter: JSON file-based storage compatible with Control Room format
"""

from ._base import BaseAdapter
from ._file import FileAdapter
from ._sqlite import SQLiteAdapter

__all__ = ["BaseAdapter", "FileAdapter", "SQLiteAdapter"]
