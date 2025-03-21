from pathlib import Path


def build_executable_with_pyinstaller(
    root_dir: Path,
    debug: bool,
    ci: bool,
    onefile: bool,
    name: str,
    dist_path: str,
    spec_name: str,
) -> None:
    """Builds the executable via PyInstaller. Expects the spec_name to be in the cwd."""
    import sys

    from .process_call import run

    spec_file = root_dir / spec_name
    if not spec_file.exists():
        raise FileNotFoundError(f"Spec file {spec_file} not found")
    args = [sys.executable, "-m", "PyInstaller"]
    spec_args = []
    if debug:
        ci = False
        spec_args.append("--debug")
        args.append("--log-level=DEBUG")
    if ci:
        args.append("-y")
    if onefile:
        spec_args.append("--onefile")
    args.append(f"--distpath={dist_path}")
    spec_args.append(f"--name={name}")
    args.append(spec_name)
    if spec_args:
        args.append("--")
        args.extend(spec_args)

    run(args, cwd=root_dir)


def make_executable(target_executable: Path) -> None:
    """
    Make the executable executable.
    """
    target_executable.chmod(0o755)
