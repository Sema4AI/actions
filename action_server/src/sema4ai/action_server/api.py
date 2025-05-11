from pathlib import Path
from typing import Optional
from sema4ai.action_server import _api_action_package, _api_actions, _api_runs
from sema4ai.action_server import _api_robots


def package_metadata(
    action_package_dir: Path, *, datadir: Optional[Path] = None
) -> dict:
    """
    Collects metadata from the action package in the target dir and returns it.

    Args:
        action_package_dir: The directory with the action package whose metadata
            should be collected.
        datadir: Directory to store the data for operating the actions server
            (by default a datadir will be generated based on the `action_package_dir`).

    Returns:
        A dict containing the metadata.

    Raises:
        RuntimeError if it was not possible to collect the metadata.
    """
    import json

    from sema4ai.action_server._selftest import sema4ai_action_server_run

    any_return = None
    cmdline: list[str] = ["package", "metadata"]
    if datadir:
        cmdline.extend(["--datadir", str(datadir)])
    result = sema4ai_action_server_run(
        cmdline,
        returncode=any_return,
        cwd=str(action_package_dir),
        capture_output=True,
    )

    if result.returncode == 0:
        return json.loads(result.stdout)
    raise RuntimeError(
        f"It was not possible to collect the package metadata.\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
    )


app.include_router(_api_action_package.router)
app.include_router(_api_actions.router)
app.include_router(_api_runs.router)
app.include_router(_api_robots.router)
