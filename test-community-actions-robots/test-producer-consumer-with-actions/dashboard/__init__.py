"""
Consolidated Robocorp Task Logs Dashboard with DuckDB WASM

This package provides tools to consolidate and visualize logs from
Producer, Consumer, and Reporter tasks in a modern web dashboard.
"""

from .log_consolidator import LogConsolidator
#from .dashboard_generator import DashboardGenerator
from .jinja2_dashboard_generator import Jinja2DashboardGenerator

__version__ = "1.0.0"
__all__ = ["LogConsolidator", "Jinja2DashboardGenerator"]