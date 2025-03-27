"""
Important: 

sema4ai.action_server.cli.main() 

is the only public API supported from the action-server.

Everything else is considered private and can be broken/changed without
being considered a backward-incompatible change!
"""
import logging
from typing import Optional

# Important: main() is the only public API supported from the action-server.
# Everything else is considered private and can be broken/changed without
# being considered a backward-incompatible change!
__all__ = ["main"]

log = logging.getLogger(__name__)


def main(args: Optional[list[str]] = None, *, exit=True) -> int:  # noqa
    import sys

    print(sys.executable)
    import sqlite3

    print("sqlite3.sqlite_version", sqlite3.sqlite_version)
    print("sqlite3.__file__", sqlite3.__file__)
    import _sqlite3

    print("_sqlite3.sqlite_version", _sqlite3.sqlite_version)
    print("_sqlite3.__file__", _sqlite3.__file__)
    return 0


if __name__ == "__main__":
    main()
