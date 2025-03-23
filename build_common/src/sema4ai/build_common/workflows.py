from pathlib import Path


def make_executable(target_executable: Path) -> None:
    """
    Make the executable executable.
    """
    target_executable.chmod(0o755)


def clean_common_build_artifacts(root_dir: Path):
    """Clean common build artifacts."""
    import shutil

    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    entitlements_file = root_dir / "entitlements.mac.plist"
    assets_zip = root_dir / "go-wrapper" / "assets" / "assets.zip"
    zip_hash = root_dir / "go-wrapper" / "assets" / "app_hash"
    assets_version = root_dir / "go-wrapper" / "assets" / "version.txt"

    paths_to_delete = [
        (dist_dir, "dir"),
        (build_dir, "dir"),
        (entitlements_file, "file"),
        (assets_zip, "file"),
        (assets_version, "file"),
        (zip_hash, "file"),
    ]

    for path, kind in paths_to_delete:
        if path.exists():
            if kind == "dir":
                print(f"Deleting {path}")
                shutil.rmtree(path)
            elif kind == "file":
                print(f"Deleting {path}")
                path.unlink()


def is_in_github_actions() -> bool:
    """Check if we are in GitHub Actions."""
    import os

    return os.environ.get("GITHUB_ACTIONS") == "true"


def build_and_sign_executable(
    *,
    root_dir: Path,
    name: str,
    debug: bool,
    ci: bool,
    dist_path: Path,
    sign: bool,
    go_wrapper: bool,
    version: str | None = None,
):
    """Default workflow to build and sign the executable.

    Args:
        root_dir: Root directory of the project.
        name: Name of the project (e.g. sai-server, agent-server, etc.)
            - The name of the executable will be <name>.exe on Windows and <name> on other platforms.
            - The spec file will be <name>.spec
        debug: Whether to build in debug mode.
        ci: Whether to build in CI mode.
        dist_path: Path to the dist directory.
        sign: Whether to sign the executable.
        go_wrapper: Whether to build the Go wrapper.
        version: Version of the executable (gotten from git tag/pr if not passed)
    """
    import shutil
    import sys

    from sema4ai.build_common.process_call import run_and_capture_output

    from .build_executable import build_executable_with_pyinstaller
    from .signing import setup_keychain, sign_macos_executable, sign_windows_executable
    from .version_from_github_actions import get_version_from_github_actions
    from .zip_assets import write_version_to_go_wrapper, zip_go_wrapper_assets

    if go_wrapper:
        go_wrapper_dir = root_dir / "go-wrapper"
        assert go_wrapper_dir.exists(), f"Go wrapper directory: {go_wrapper_dir} not found, unable to build Go wrapper"
        assert go_wrapper_dir.is_dir(), f"Go wrapper directory: {go_wrapper_dir} is not a directory, unable to build Go wrapper"

        print("Checking Go version...")
        go_executable = shutil.which("go")
        assert (
            go_executable is not None
        ), "Go executable not found in the PATH, unable to build Go wrapper"

        stdout, stderr = run_and_capture_output(
            [go_executable, "version"], cwd=root_dir / "go-wrapper"
        )
        print(" ============== Go version: ============== ")
        print(stdout)
        print(stderr)
        print(" ============== END Go version: ============== ")

    if version is None:
        version = get_version_from_github_actions()

    onefile = False  # We no longer support the onefile mode!

    if is_in_github_actions():
        if not sign:
            print("WARNING: Not signing in GitHub Actions (flag --sign not passed)")
            print("WARNING: Not signing in GitHub Actions (flag --sign not passed)")
            print("WARNING: Not signing in GitHub Actions (flag --sign not passed)")

    if sign and sys.platform == "darwin":
        setup_keychain()  # Needed for macos code signing

    spec_name = f"{name}.spec"
    assert (
        root_dir / spec_name
    ).exists(), f"spec file: {root_dir / spec_name} not found"

    build_executable_with_pyinstaller(
        root_dir=root_dir,
        debug=debug,
        ci=ci,
        onefile=onefile,
        name=name,
        dist_path=str(dist_path),
        spec_name=spec_name,
    )

    assert dist_path.exists(), f"dist directory: {dist_path} not created"
    executable_name = (name + ".exe") if sys.platform == "win32" else name

    if onefile:
        target_executable = dist_path / executable_name
        assert (
            target_executable.exists()
        ), f"Executable {target_executable} does not exist (onefile mode)"

    else:
        app_dir_inside_dist_dir = dist_path / name
        assert (
            app_dir_inside_dist_dir.exists()
        ), f"Directory {app_dir_inside_dist_dir} does not exist (NOT onefile mode)"
        target_executable = app_dir_inside_dist_dir / executable_name
        assert (
            target_executable.exists()
        ), f"Executable {target_executable} does not exist (NOT onefile mode)"

        print(f"Finished building executable with pyinstaller: {target_executable}")
        if sign:
            print("Signing executable...")
            if sys.platform == "darwin":
                sign_macos_executable(root_dir, target_executable)
            elif sys.platform == "win32":
                sign_windows_executable(target_executable)
            else:
                print(
                    f"Signing not supported on this platform (sys.platform == {sys.platform})"
                )
        make_executable(target_executable)

        if go_wrapper:
            assets_dir = root_dir / "go-wrapper" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            zip_go_wrapper_assets(app_dir_inside_dist_dir, assets_dir)
            write_version_to_go_wrapper(assets_dir, version)

            print("Building Go wrapper...")
            assert go_executable is not None, "Go executable not found in the PATH"

            print(" ============== Building Go wrapper: ============== ")
            stdout, stderr = run_and_capture_output(
                [go_executable, "build", "-o", executable_name],
                cwd=root_dir / "go-wrapper",
                shell=True if sys.platform == "win32" else False,
            )
            print(stdout)
            print(stderr)
            print(" ============== END Building Go wrapper: ============== ")

            built_go_wrapper = root_dir / "go-wrapper" / executable_name
            assert (
                built_go_wrapper.exists()
            ), f"Go wrapper executable {built_go_wrapper} not built"

            print("Copying Go wrapper executable to dist directory...")
            final_executable = dist_path / "final" / executable_name
            final_executable.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(built_go_wrapper, final_executable)

            # Now, sign the final executable
            if sign:
                if sys.platform == "darwin":
                    sign_macos_executable(root_dir, final_executable)
                elif sys.platform == "win32":
                    sign_windows_executable(final_executable)
                else:
                    print(
                        f"Signing not supported on this platform (sys.platform == {sys.platform})"
                    )

            make_executable(final_executable)
            print(f"Final executable available at: {final_executable}")
