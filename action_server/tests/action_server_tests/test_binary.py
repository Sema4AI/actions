from pathlib import Path


def get_internal_version_location(version: str) -> Path:
    import os
    import sys

    if sys.platform == "win32":
        app_data_dir = os.getenv("LOCALAPPDATA")
        if not app_data_dir:
            raise RuntimeError("LOCALAPPDATA environment variable is not set")
        target_path = os.path.join(
            app_data_dir, "sema4ai", "bin", "action-server", "internal"
        )
    else:
        home_dir = os.path.expanduser("~")
        target_path = os.path.join(
            home_dir, ".sema4ai", "bin", "action-server", "internal"
        )

    return Path(target_path) / version


def test_binary_build():
    import os
    import shutil
    import sys

    from sema4ai.common.run_in_thread import run_in_thread

    CURDIR = Path(__file__).absolute().parent
    action_server_dir = CURDIR.parent.parent
    assert (action_server_dir / "pyproject.toml").exists()

    import subprocess

    env = os.environ.copy()
    env.pop("PYTHONPATH", "")
    env.pop("PYTHONHOME", "")
    env.pop("VIRTUAL_ENV", "")
    env["PYTHONIOENCODING"] = "utf-8"

    dist_dir = action_server_dir / "dist" / "final"
    go_wrapper_name = f"action-server-test-{os.getpid()}"
    target_executable = dist_dir / (
        go_wrapper_name + (".exe" if sys.platform == "win32" else "")
    )

    if target_executable.exists():
        try:
            os.remove(target_executable)
        except Exception:
            raise RuntimeError(f"Failed to remove {target_executable}")

    assets = action_server_dir / "go-wrapper" / "assets"
    for asset_name in ("app_hash", "version.txt", "assets.zip"):
        asset_path = assets / asset_name
        if asset_path.exists():
            asset_path.unlink()

    version = f"test_binary_build-local-{os.getpid()}"
    build_executable_output = subprocess.check_output(
        [
            "uv",
            "run",
            "build-exe",
            "--go-wrapper",
            f"--version={version}",
            f"--go-wrapper-name={go_wrapper_name}",
        ],
        cwd=action_server_dir,
        env=env,
        stderr=subprocess.STDOUT,
    )

    # Binary should be in the dist directory
    assert target_executable.exists(), (
        f"Binary {target_executable} does not exist. Build output:\n{build_executable_output}"
    )

    env["SEMA4AI_GO_WRAPPER_DEBUG"] = "1"

    # Run the executable
    def run_executable():
        proc = subprocess.Popen(
            [target_executable, "-h"],
            cwd=action_server_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout, _ = proc.communicate()
        return stdout.decode("utf-8", errors="replace")

    extracted_location = get_internal_version_location(version)
    if extracted_location.exists():
        shutil.rmtree(extracted_location)

    try:
        fut1 = run_in_thread(run_executable)
        fut2 = run_in_thread(run_executable)
        fut3 = run_in_thread(run_executable)

        futures = [fut1, fut2, fut3]

        outputs = [fut.result() for fut in futures]
        skipped = 0
        extracted = 0
        for output in outputs:
            if "Zip hash matches, skipping asset expansion" in output:
                skipped += 1
            if "Expanding assets to: " in output:
                extracted += 1

        full_outputs = "\n".join(outputs)
        assert skipped == 2, (
            f"Expected 2 skipped, got {skipped}. Full outputs:\n{full_outputs}"
        )
        assert extracted == 1, (
            f"Expected 1 extracted, got {extracted}. Full outputs:\n{full_outputs}"
        )

        assert "(ignored) Error touching" not in full_outputs, full_outputs
        assert "(ignored) Error creating" not in full_outputs, full_outputs

        assert extracted_location.exists()

        assert (extracted_location / "app_hash").exists()
        assert (extracted_location / "lastLaunchTouch").exists()
    finally:
        shutil.rmtree(extracted_location)

        if target_executable.exists():
            try:
                os.remove(target_executable)
            except Exception:
                raise RuntimeError(f"Failed to remove {target_executable}")
