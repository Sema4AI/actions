from pathlib import Path


def get_root_dir() -> Path:
    """Get the root directory of the project."""
    import os.path

    # The root directory is the directory containing pyproject.toml
    initial_dir = curdir = Path(os.path.abspath(os.path.normpath(".")))

    while not (curdir / "pyproject.toml").exists():
        parent_dir = curdir.parent
        if parent_dir == curdir or not parent_dir:
            raise RuntimeError(
                f"pyproject.toml not found for: {initial_dir} (current: {curdir})"
            )
        curdir = parent_dir

    return curdir
