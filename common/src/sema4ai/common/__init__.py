"""
sema4ai-common is a library for common utilities to be shared across sema4ai
projects.

It should have as few dependencies as possible.

Each module should be a single utility (thus, sema4ai.common doesn't directly
contain anything).
"""

__version__ = "0.0.9"
version_info = [int(x) for x in __version__.split(".")]
