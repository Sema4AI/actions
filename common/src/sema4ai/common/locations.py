import os
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_default_sema4ai_home_dir() -> Path:
    home_env_var = os.environ.get("SEMA4AI_HOME")
    if home_env_var:
        home = Path(home_env_var)
    else:
        if sys.platform == "win32":
            localappdata = os.environ.get("LOCALAPPDATA")
            if not localappdata:
                raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
            home = Path(localappdata) / "sema4ai"
        else:
            # Linux/Mac
            home = Path("~/.sema4ai").expanduser()
    return home


def get_default_executable_path(name: str, version: str) -> Path:
    """
    Provides the default path for a (sema4ai managed) executable.

    Args:
        name: The name of the executable (i.e.: "action-server", "agent-cli", etc).
        version: The version of the executable.

    Returns:
        The path to the executable. Something as:
        <sema4ai_home>/bin/action-server/0.1.0/action-server.exe
    """

    # We need to download the action server to the default sema4ai home dir
    # because the action server will use it to store the actions.

    action_server_download_dir = get_default_sema4ai_home_dir() / "bin" / name / version

    suffix = ""
    if sys.platform == "win32":
        suffix = ".exe"

    target_location = action_server_download_dir / f"{name}{suffix}"
    return target_location
