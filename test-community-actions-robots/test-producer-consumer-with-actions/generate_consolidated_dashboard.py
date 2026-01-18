"""
Entry point script for generating consolidated dashboard
"""

import os
import sys
from pathlib import Path

# Add the project root to the path (repository root)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.jinja2_dashboard_generator import Jinja2DashboardGenerator
from robocorp import log
from robocorp.tasks import task





@task
def generate_consolidated_dashboard():
    """Robocorp task to generate the consolidated dashboard using Jinja2."""
    log.info("Starting consolidated dashboard generation task with Jinja2")
    
    # Get output directory
    output_dir = Path(os.getenv("ROBOT_ARTIFACTS", "output"))
    dashboard_dir = project_root / "dashboard"
    
    # Initialize Jinja2 generator
    generator = Jinja2DashboardGenerator(output_dir, dashboard_dir)
    
    # Generate dashboard
    dashboard_path = generator.generate_dashboard("consolidated_dashboard_jinja2.html")
    
    # Generate data exports
    exports = generator.generate_data_exports()
    
    log.info(f"Dashboard generation completed successfully")
    log.info(f"Dashboard file: {dashboard_path}")
    log.info(f"Data exports: {exports}")
    
    return {
        'dashboard_path': str(dashboard_path),
        'exports': {k: str(v) if isinstance(v, Path) else {k2: str(v2) for k2, v2 in v.items()} for k, v in exports.items()}
    }


