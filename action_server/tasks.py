import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).absolute().parent

try:
    import devutils
except ImportError:
    devutils_src = ROOT.parent / "devutils" / "src"
    assert devutils_src.exists(), f"{devutils_src} does not exist!"
    sys.path.append(str(devutils_src))

from devutils.invoke_utils import build_common_tasks

globals().update(
    build_common_tasks(
        ROOT,
        "sema4ai.action_server",
        ruff_format_arguments=r"--exclude=_static_contents.py,_oauth2_config.py",
    )
)

from invoke import Context, task

CURDIR = Path(__file__).parent.absolute()


@contextmanager
def chdir(path: Path):
    old = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)


def run(ctx: Context, *args: str, **options):
    cmd = " ".join(args)
    options.setdefault("pty", sys.platform != "win32")
    options.setdefault("echo", True)
    ctx.run(cmd, **options)


@contextmanager
def _change_to_frontend_dir():
    RESOLVED_CURDIR = CURDIR.resolve()

    # vite build has a bug which makes it misbehave when working with a subst
    # (presumably this is because it's resolving the actual location of
    # things and then compares with unresolved paths).
    # In order to fix that we resolve the directory ourselves prior to the
    # build and switch to that directory.
    with chdir(RESOLVED_CURDIR / "frontend"):
        yield


@contextmanager
def _change_to_build_binary():
    RESOLVED_CURDIR = CURDIR.absolute()

    with chdir(RESOLVED_CURDIR / "build-binary"):
        yield


@contextmanager
def _change_to_build_go_wrapper():
    RESOLVED_CURDIR = CURDIR.absolute()

    with chdir(RESOLVED_CURDIR / "go-wrapper"):
        yield


@task
def dev_frontend(ctx: Context):
    """Run the frontend in dev mode (starts its own localhost server using vite)."""

    with _change_to_frontend_dir():
        run(ctx, "npm", "run", "dev")


@task
def build_frontend(
    ctx: Context,
    debug: bool = False,
    install: bool = True,
    tier: str = None,
    json_output: bool = False,
):
    """Build static .html frontend with tier-based configuration.
    
    Args:
        debug: Build in debug mode (not minified)
        install: Run npm ci before build
        tier: Build tier ('community' or 'enterprise'), defaults to 'community' if not set via env var
        json_output: Output build result as JSON
    """
    import json as json_lib
    import os
    import sys
    from pathlib import Path
    
    # Import build system modules
    sys.path.insert(0, str(CURDIR / "build-binary"))
    from tier_selector import select_tier, ConfigurationError
    from package_manifest import PackageManifest
    from determinism import set_source_date_epoch
    
    try:
        # Step 1: Select tier
        env_tier = os.environ.get("TIER")
        build_tier = select_tier(cli_flag=tier, env_var=env_tier)
        
        if not json_output:
            print(f"🔨 Building with tier: {build_tier.name.value}")
        
        # Step 2: Set deterministic timestamp
        timestamp = set_source_date_epoch(CURDIR.parent)
        if not json_output:
            print(f"⏰ Using SOURCE_DATE_EPOCH: {timestamp}")
        
        # Step 3: Load and validate manifest
        frontend_dir = CURDIR / "frontend"
        manifest = PackageManifest.load(build_tier.name.value, frontend_dir)
        
        validation_result = manifest.validate()
        if not validation_result.passed:
            if not json_output:
                print("❌ Manifest validation failed:")
                for error in validation_result.errors:
                    print(f"  - {error}")
            if json_output:
                result = {
                    "status": "error",
                    "tier": build_tier.name.value,
                    "error": "Manifest validation failed",
                    "details": validation_result.errors,
                }
                print(json_lib.dumps(result, indent=2))
            sys.exit(3)  # Config error
        
        # Step 4: Copy manifest to root
        manifest.copy_to_root(frontend_dir)
        
        if not json_output:
            print(f"✓ Using {build_tier.name.value} package manifest")
        
        # Step 5: Install and build
        with _change_to_frontend_dir():
            if install:
                if not json_output:
                    print("📦 Installing dependencies...")
                run(ctx, "npm", "ci", "--no-audit", "--no-fund")
            
            if not json_output:
                print("🏗️  Building frontend...")
            
            # Set TIER environment variable for Vite
            os.environ["TIER"] = build_tier.name.value
            
            if debug:
                run(ctx, "npm", "run", "build:debug")
            else:
                run(ctx, "npm", "run", "build")
        
        # Step 6: Write static contents
        index_src = CURDIR / "frontend" / "dist" / "index.html"
        assert index_src.exists(), f"Expected: {index_src} to exist."
        dest_static_contents = (
            CURDIR / "src" / "sema4ai" / "action_server" / "_static_contents.py"
        )

        file_contents = {"index.html": index_src.read_bytes()}

        with open(dest_static_contents, "w", encoding="utf-8", newline="\n") as stream:
            if not json_output:
                print(f"📝 Writing static contents to: {dest_static_contents}")
            stream.write(
                f"""# coding: utf-8
# Note: autogenerated file.
# To regenerate this file use: inv build-frontend.

# The FILE_CONTENTS contains the contents of the files with
# html/javascript code for the static assets we use.

FILE_CONTENTS = {repr(file_contents)}
"""
            )
        
        # Success output
        if json_output:
            result = {
                "status": "success",
                "tier": build_tier.name.value,
                "artifact": {
                    "path": str(index_src),
                    "size_bytes": index_src.stat().st_size,
                },
                "timestamp": timestamp,
            }
            print(json_lib.dumps(result, indent=2))
        else:
            print(f"✅ Frontend built successfully ({build_tier.name.value} tier)")
    
    except ConfigurationError as e:
        if json_output:
            result = {
                "status": "error",
                "error": "Configuration error",
                "message": str(e),
            }
            print(json_lib.dumps(result, indent=2))
        else:
            print(f"❌ Configuration error: {e}")
        sys.exit(3)
    except Exception as e:
        if json_output:
            result = {
                "status": "error",
                "error": "Build error",
                "message": str(e),
            }
            print(json_lib.dumps(result, indent=2))
        else:
            print(f"❌ Build error: {e}")
        sys.exit(1)


@task
def build_frontend_community(ctx: Context, debug: bool = False, install: bool = True, json_output: bool = False):
    """Build frontend with community tier (alias for build-frontend --tier=community)."""
    build_frontend(ctx, debug=debug, install=install, tier="community", json_output=json_output)


@task
def build_frontend_enterprise(ctx: Context, debug: bool = False, install: bool = True, json_output: bool = False):
    """Build frontend with enterprise tier (alias for build-frontend --tier=enterprise)."""
    build_frontend(ctx, debug=debug, install=install, tier="enterprise", json_output=json_output)


@task
def validate_imports(ctx: Context, tier: str = "community", json_output: bool = False):
    """Validate that community artifacts have no enterprise imports.
    
    Args:
        tier: Build tier to validate (typically 'community')
        json_output: Output validation result as JSON
    """
    import json as json_lib
    from pathlib import Path
    
    sys.path.insert(0, str(CURDIR / "build-binary"))
    from tree_shaker import scan_imports, detect_enterprise_imports
    
    dist_path = CURDIR / "frontend" / "dist"
    if not dist_path.exists():
        msg = f"Distribution directory not found: {dist_path}"
        if json_output:
            print(json_lib.dumps({"status": "error", "message": msg}, indent=2))
        else:
            print(f"❌ {msg}")
        sys.exit(2)
    
    # Scan all built files for enterprise imports
    violations = detect_enterprise_imports(str(dist_path))
    
    if violations:
        msg = f"Found {len(violations)} enterprise import(s) in {tier} build"
        details = []
        for v in violations:
            details.append({
                "file": str(v.file_path),
                "line": v.line_number,
                "import": v.import_statement,
                "module": v.prohibited_module,
                "severity": v.severity
            })
        
        if json_output:
            print(json_lib.dumps({
                "status": "failed",
                "message": msg,
                "violations": details
            }, indent=2))
        else:
            print(f"❌ {msg}")
            for v in violations:
                print(f"  {v.file_path}:{v.line_number}: {v.import_statement}")
        sys.exit(2)
    
    if json_output:
        print(json_lib.dumps({
            "status": "passed",
            "message": f"No enterprise imports found in {tier} build"
        }, indent=2))
    else:
        print(f"✅ No enterprise imports found in {tier} build")


@task
def validate_artifact(ctx: Context, tier: str = "community", json_output: bool = False):
    """Validate built artifacts meet all requirements.
    
    Args:
        tier: Build tier to validate
        json_output: Output validation result as JSON
    """
    import json as json_lib
    
    sys.path.insert(0, str(CURDIR / "build-binary"))
    from artifact_validator import validate_artifact as validate_artifact_func
    
    artifact_path = CURDIR / "frontend" / "dist"
    if not artifact_path.exists():
        msg = f"Artifact path not found: {artifact_path}"
        if json_output:
            print(json_lib.dumps({"status": "error", "message": msg}, indent=2))
        else:
            print(f"❌ {msg}")
        sys.exit(2)
    
    baseline_path = CURDIR / "tests" / "performance_tests" / "baseline.json"
    
    try:
        all_passed, checks = validate_artifact_func(
            artifact_path, 
            tier, 
            baseline_path if baseline_path.exists() else None,
            json_output
        )
        
        if json_output:
            output = {
                "status": "passed" if all_passed else "failed",
                "checks": [
                    {
                        "name": check.name,
                        "passed": check.passed,
                        "message": check.message,
                        "severity": check.severity
                    }
                    for check in checks
                ]
            }
            print(json_lib.dumps(output, indent=2))
        else:
            for check in checks:
                status = "✅" if check.passed else "❌"
                print(f"{status} {check.name}: {check.message}")
        
        if not all_passed:
            sys.exit(2)
    
    except Exception as e:
        if json_output:
            print(json_lib.dumps({"status": "error", "message": str(e)}, indent=2))
        else:
            print(f"❌ Validation error: {e}")
        sys.exit(2)


@task
def build_frontend_cdn(ctx: Context, version: str = "latest"):
    """Build static .html frontend from CDN (bypasses npm dependencies)"""
    import subprocess
    import time
    import requests
    import shutil
    
    print(f"Building frontend from CDN (version: {version})...")
    
    # Download the Linux binary
    binary_url = f"https://cdn.sema4.ai/action-server/releases/{version}/linux64/action-server"
    temp_dir = CURDIR / "temp_cdn_extract"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        binary_path = temp_dir / "action-server"
        print(f"Downloading binary from {binary_url}...")
        response = requests.get(binary_url, stream=True)
        response.raise_for_status()
        
        with open(binary_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        os.chmod(binary_path, 0o755)
        
        # Create action package using the basic template
        package_dir = temp_dir / "temp_package"
        print("Creating action package from template...")
        subprocess.run(
            [str(binary_path), "new", "--name", "temp_package", "--template", "basic"],
            cwd=str(temp_dir),
            check=True
        )
        
        # Start server in the background
        print("Starting action server...")
        log_path = package_dir / "action_server.log"
        process = subprocess.Popen(
            [str(binary_path), "start", "--port", "8080"],
            cwd=str(package_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to be ready
        print("Waiting for server to start...")
        url = "http://localhost:8080"
        timeout = 60
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if log file indicates server is ready
            if log_path.exists():
                with open(log_path, "r") as f:
                    log_content = f.read()
                    if url in log_content:
                        print(f"Server started successfully at {url}")
                        break
                    if "Error executing action-server" in log_content:
                        raise RuntimeError(f"Server failed to start. Log:\n{log_content}")
            
            # Also try direct connection
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    print("Server is responding!")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        
        # Download frontend
        response = requests.get("http://localhost:8080/")
        response.raise_for_status()
        html_content = response.content
        
        # Write to file
        dest_static_contents = (
            CURDIR / "src" / "sema4ai" / "action_server" / "_static_contents.py"
        )
        file_contents = {"index.html": html_content}
        with open(dest_static_contents, "w", encoding="utf-8") as stream:
            print(f"Writing static contents to: {dest_static_contents}")
            stream.write(
                f"""# coding: utf-8
# Note: autogenerated file from CDN.
# To regenerate this file use: inv build-frontend-cdn.
# The FILE_CONTENTS contains the contents of the files with
# html/javascript code for the static assets we use.
FILE_CONTENTS = {repr(file_contents)}
"""
            )
        print("Frontend successfully extracted from CDN!")
        
    finally:
        # Cleanup
        if 'process' in locals():
            process.terminate()
            process.wait()
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@task
def build_oauth2_config(ctx: Context):
    """Build static OAuth2 .yaml config."""
    import subprocess

    sema4ai_config_file_name = "sema4ai-oauth-config.yaml"
    default_user_config_file_name = "oauth-config.yaml"
    sema4ai_config_local_file_path = CURDIR / sema4ai_config_file_name
    default_user_config_local_file_path = CURDIR / default_user_config_file_name

    base_api_url = "repos/Sema4AI/oauth-public-configs/contents"

    dest_path = CURDIR / "src" / "sema4ai" / "action_server" / "_oauth2_config.py"

    result_sema4ai_config_contents = subprocess.run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github.raw",
            f"{base_api_url}/{sema4ai_config_file_name}",
        ],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")

    default_user_config_contents = subprocess.run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github.raw",
            f"{base_api_url}/{default_user_config_file_name}",
        ],
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")

    file_contents = {
        "sema4ai_config": result_sema4ai_config_contents,
        "default_user_config": default_user_config_contents,
    }

    with open(dest_path, "w", encoding="utf-8", newline="\n") as stream:
        print(f"Writing OAuth2 configs to: {dest_path}")
        stream.write(
            f"""# coding: utf-8
# Note: autogenerated file.
# To regenerate this file use: inv build-oauth2-config.

# The FILE_CONTENTS contains the contents of the Sema4.ai OAuth2 configuration, as well as default user configuration.

FILE_CONTENTS = {repr(file_contents)}
"""
        )


@task(
    help={
        "debug": "Build in debug mode",
        "ci": "Build in CI mode, disabling interactive prompts",
        "dist_path": "Path to the dist directory",
        "sign": "Sign the executable",
        "go_wrapper": "Build the Go wrapper too",
        "version": "Version of the executable (gotten from github tag/pr if not passed)",
    }
)
def build_executable(
    ctx: Context,
    debug: bool = False,
    ci: bool = True,
    dist_path: str = "dist",
    sign: bool = False,
    go_wrapper: bool = False,
    version: str = None,
    go_wrapper_name: str | None = None,
) -> None:
    """Build the project executable via PyInstaller."""
    from sema4ai.build_common.root_dir import get_root_dir
    from sema4ai.build_common.workflows import build_and_sign_executable

    if version is None:
        from sema4ai.action_server import __version__

        version = __version__

    root_dir = get_root_dir()
    build_and_sign_executable(
        root_dir=root_dir,
        name="action-server",
        debug=debug,
        ci=ci,
        dist_path=root_dir / dist_path,
        sign=sign,
        go_wrapper=go_wrapper,
        version=version,
        go_wrapper_name=go_wrapper_name,
    )

    # to check if signed:  spctl -a -vvv -t install dist/final/action-server


@task
def clean(ctx: Context):
    """Clean build artifacts."""
    from sema4ai.build_common.root_dir import get_root_dir
    from sema4ai.build_common.workflows import clean_common_build_artifacts

    clean_common_build_artifacts(get_root_dir())


@task
def build_go_wrapper(ctx: Context) -> None:
    with _change_to_build_go_wrapper():
        target = "action-server-unsigned" + (".exe" if sys.platform == "win32" else "")
        run(
            ctx,
            "go",
            "build",
            "-o",
            target,
        )
        print(f"Built go wrapper at: {os.path.abspath(target)}")


@task
def download_rcc(ctx: Context, system: Optional[str] = None) -> None:
    """
    Downloads RCC in the place where the action server expects it
    """
    env = os.environ.copy()
    curr_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = curr_pythonpath + os.pathsep + str(CURDIR / "src")
    run(ctx, "python -m sema4ai.action_server download-rcc", env=env)


def _replace_deps(content, new_deps):
    """Replaces the contents between ## START DEPS and ## ENDS DEPS with new_deps.

    Args:
      content: The content of the file as a string.
      new_deps: The new dependencies to insert.

    Returns:
      The content of the file with the dependencies replaced.
    """

    start_marker = "## START DEPS\n"
    end_marker = "## END DEPS\n"

    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)

    if start_pos == -1 or end_pos == -1:
        raise ValueError("Markers not found in content")

    return content[:start_pos] + start_marker + new_deps + content[end_pos:]


@task
def test_not_integration(ctx: Context):
    from sema4ai.build_common.process_call import run
    from sema4ai.build_common.root_dir import get_root_dir

    action_server_dir = get_root_dir()
    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "not integration_test",
            "-rfE",
            "-vv",
            "--force-regen",
            "-n",
            "auto",
        ],
        cwd=str(action_server_dir / "tests"),
    )


@task
def test_binary(ctx: Context, test: str = "", jobs: str = "auto"):
    """Test the binary"""
    import subprocess

    from sema4ai.build_common.process_call import run
    from sema4ai.build_common.root_dir import get_root_dir

    # The binary should be in the dist directory already.
    # Run all the tests using pytest -m integration_test
    # While setting an environment variable to point to the
    # created executable.
    action_server_dir = get_root_dir()
    action_server_executable = (
        action_server_dir
        / "dist"
        / "final"
        / ("action-server" + (".exe" if sys.platform == "win32" else ""))
    )
    assert (
        action_server_executable.exists()
    ), f"Expected: {action_server_executable} to exist."
    env = os.environ.copy()
    env.pop("PYTHONPATH", "")
    env.pop("PYTHONHOME", "")
    env.pop("VIRTUAL_ENV", "")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHON_EXE"] = str(sys.executable)

    env["SEMA4AI_INTEGRATION_TEST_ACTION_SERVER_EXECUTABLE"] = str(
        action_server_executable
    )
    args = [
        sys.executable,
        "-m",
        "pytest",
        "-m",
        "integration_test",
        "-rfE",
        "-vv",
        "--force-regen",
        "-n",
        "0",  # Bad rcc: when we run too many rcc tests in parallel from the binary, tests fail because rcc seems to crash (needs more investigation)
    ]
    if test:
        args.append("-k")
        args.append(test)
    run(
        args,
        cwd=str(action_server_dir / "tests"),
        env=env,
    )


@task
def set_rcc_version(ctx: Context, version: str):
    """Set RCC version in both build.py and _download_rcc.py files."""
    import re
    
    # Files to update
    files_to_update = [
        CURDIR / "build.py",
        CURDIR / "src" / "sema4ai" / "action_server" / "_download_rcc.py"
    ]
    
    for file_path in files_to_update:
        if not file_path.exists():
            print(f"Warning: {file_path} does not exist, skipping...")
            continue
            
        # Read current content
        with open(file_path, "r", encoding="utf-8", newline="\n") as f:
            content = f.read()
        
        # Replace RCC_VERSION = "..." with new version
        pattern = r'RCC_VERSION = "[^"]*"'
        replacement = f'RCC_VERSION = "{version}"'
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            # Write updated content with LF line endings
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_content)
            print(f"Updated {file_path} with RCC version {version}")
        else:
            print(f"No RCC_VERSION found in {file_path}")


@task
def print_env(ctx: Context):
    import os

    print(" ============== ENV ============== ")
    for key, value in os.environ.items():
        if len(value) > 100:
            print(f"{key}:")
            parts = value.split(os.pathsep)
            for part in parts:
                print(f"  {part}")
        else:
            print(f"{key}={value}")
    print(" ============== END ENV ============== ")


@task
def setup_hooks(ctx: Context):
    """Setup git hooks for local development (optional).
    
    This task symlinks the pre-commit hook from .githooks/ to .git/hooks/
    to enable local tier separation validation.
    """
    import os
    import subprocess
    
    root_dir = CURDIR.parent
    githooks_dir = root_dir / ".githooks"
    git_hooks_dir = root_dir / ".git" / "hooks"
    
    # Ensure .git/hooks directory exists
    git_hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Source and destination paths
    source_hook = githooks_dir / "pre-commit"
    dest_hook = git_hooks_dir / "pre-commit"
    
    if not source_hook.exists():
        print(f"Error: Pre-commit hook not found at {source_hook}")
        sys.exit(1)
    
    # Create symlink (or copy on Windows)
    if sys.platform == "win32":
        # Windows: copy instead of symlink
        import shutil
        shutil.copy2(source_hook, dest_hook)
        print(f"✅ Copied pre-commit hook to {dest_hook}")
    else:
        # Unix-like: create symlink
        if dest_hook.exists() or dest_hook.is_symlink():
            dest_hook.unlink()
        dest_hook.symlink_to(source_hook)
        print(f"✅ Symlinked pre-commit hook to {dest_hook}")
    
    print("Pre-commit hook installed successfully!")
    print("The hook will check for enterprise imports in core/ files.")
    print("To bypass the hook, use: git commit --no-verify")


@task
def test_run_in_parallel(ctx: Context):
    """
    Just runs the action server in dist/final/action-server 3 times in parallel
    (may be used to manually check issues with the lock file).
    """
    import subprocess

    from sema4ai.build_common.process_call import run
    from sema4ai.build_common.root_dir import get_root_dir

    # The binary should be in the dist directory already.
    action_server_dir = get_root_dir()
    action_server_executable = (
        action_server_dir
        / "dist"
        / "final"
        / ("action-server" + (".exe" if sys.platform == "win32" else ""))
    )
    assert (
        action_server_executable.exists()
    ), f"Expected: {action_server_executable} to exist."
    subprocess.Popen([action_server_executable, "-h"])
    subprocess.Popen([action_server_executable, "-h"])
    subprocess.Popen([action_server_executable, "-h"])
