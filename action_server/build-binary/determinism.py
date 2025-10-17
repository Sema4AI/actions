"""Deterministic build support for reproducible builds."""

import os
import subprocess
import time
from pathlib import Path


def set_source_date_epoch(root_dir: Path = None) -> int:
    """Set SOURCE_DATE_EPOCH for reproducible builds.
    
    Uses git commit timestamp if available, otherwise current time.
    
    Args:
        root_dir: Root directory of the git repository
        
    Returns:
        Unix timestamp used for SOURCE_DATE_EPOCH
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    try:
        # Try to get timestamp from git commit
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            os.environ["SOURCE_DATE_EPOCH"] = str(timestamp)
            return timestamp
        else:
            # Not in git repo or git command failed
            print("Warning: Not in git repository, using current timestamp")
            timestamp = int(time.time())
            os.environ["SOURCE_DATE_EPOCH"] = str(timestamp)
            return timestamp
            
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        # Git not available or command failed
        print("Warning: Git not available, using current timestamp")
        timestamp = int(time.time())
        os.environ["SOURCE_DATE_EPOCH"] = str(timestamp)
        return timestamp
