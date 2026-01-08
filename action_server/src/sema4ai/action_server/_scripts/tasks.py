"""
UV task entry points for action_server.

These functions are exposed as [project.scripts] entry points in pyproject.toml,
allowing commands like `uv run lint`, `uv run test`, `uv run build-frontend`.

Usage:
    uv run list           # List all available tasks
    uv run lint           # Run linting checks
    uv run format         # Auto-format code
    uv run typecheck      # Run type checking
    uv run test           # Run all tests
    uv run test-unit      # Run non-integration tests
    uv run test-binary    # Run integration tests against binary
    uv run build          # Build wheel
    uv run build-frontend # Build frontend assets
    uv run build-exe      # Build PyInstaller executable
    uv run build-go       # Build Go wrapper
    uv run dev-frontend   # Run frontend dev server
    uv run clean          # Clean build artifacts
"""

import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

# Project paths
# __file__ is at src/sema4ai/action_server/_scripts/tasks.py
# action_server project root is 5 levels up
_SCRIPTS_DIR = Path(__file__).parent.resolve()
_ACTION_SERVER_PKG = _SCRIPTS_DIR.parent  # src/sema4ai/action_server
_SRC_DIR = _ACTION_SERVER_PKG.parent.parent  # src/
ROOT = _SRC_DIR.parent  # action_server project root
REPO_ROOT = ROOT.parent  # actions repo root
FRONTEND_DIR = ROOT / "frontend"
GO_WRAPPER_DIR = ROOT / "go-wrapper"
TESTS_DIR = ROOT / "tests"
RUFF_CONFIG = REPO_ROOT / "ruff.toml"
TARGETS = ["src", "tests"]


# =============================================================================
# Utilities
# =============================================================================

@contextmanager
def chdir(path: Path):
    """Context manager to change directory temporarily."""
    old = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)


def _run(*args: str, check: bool = True, cwd: Path | None = None, env: dict | None = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, env=env)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


def _print_help(name: str, description: str):
    """Print help for a command if --help is passed."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"{name}: {description}")
        sys.exit(0)


# =============================================================================
# Task Listing
# =============================================================================

TASKS = {
    "list": "List all available tasks",
    "lint": "Run linting checks (ruff, isort)",
    "format": "Auto-format code (ruff --fix, isort)",
    "typecheck": "Run mypy type checking",
    "test": "Run all tests with pytest",
    "test-unit": "Run non-integration tests",
    "test-binary": "Run integration tests against built binary",
    "build": "Build wheel distribution",
    "build-frontend": "Build frontend static assets",
    "build-oauth2-config": "Fetch and embed OAuth2 configs",
    "build-exe": "Build PyInstaller executable",
    "build-go": "Build Go wrapper",
    "dev-frontend": "Run frontend dev server (vite)",
    "download-rcc": "Download RCC binary",
    "clean": "Clean build artifacts",
}


def list_tasks():
    """List all available tasks."""
    print("Available tasks:\n")
    for name, description in TASKS.items():
        print(f"  {name:20} {description}")
    print("\nUsage: uv run <task>")


# =============================================================================
# Linting and Formatting
# =============================================================================

def lint():
    """Run all linting checks (ruff, isort)."""
    _print_help("lint", "Run linting checks (ruff, isort)")

    with chdir(ROOT):
        # Ruff basic checks
        _run("ruff", "check", *TARGETS)

        # Ruff format check
        _run(
            "ruff", "format", "--check",
            "--config", str(RUFF_CONFIG),
            "--exclude", "_static_contents.py,_oauth2_config.py",
            *TARGETS,
        )

        # isort check
        _run("isort", "--check", *TARGETS)

    print("\nAll lint checks passed!")


def format():
    """Auto-format code with ruff and isort."""
    _print_help("format", "Auto-format code (ruff --fix, isort)")

    with chdir(ROOT):
        # Ruff fix
        _run("ruff", "check", "--fix", *TARGETS)

        # Ruff format
        _run(
            "ruff", "format",
            "--config", str(RUFF_CONFIG),
            "--exclude", "_static_contents.py,_oauth2_config.py",
            *TARGETS,
        )

        # isort
        _run("isort", *TARGETS)

    print("\nFormatting complete!")


def typecheck():
    """Run mypy type checking."""
    _print_help("typecheck", "Run mypy type checking")

    strict = "--strict" in sys.argv

    with chdir(ROOT):
        args = [
            "mypy",
            "--follow-imports=silent",
            "--show-column-numbers",
            "--namespace-packages",
            "--explicit-package-bases",
            *TARGETS,
        ]
        if strict:
            args.append("--strict")

        _run(*args)

    print("\nType check passed!")


# =============================================================================
# Testing
# =============================================================================

def test():
    """Run all tests with pytest."""
    _print_help("test", "Run all tests with pytest")

    with chdir(ROOT):
        _run(
            "pytest",
            "-rfE", "-vv", "--force-regen",
            "-n", "auto",
            *sys.argv[1:],  # Pass through any extra args
        )


def test_unit():
    """Run non-integration tests."""
    _print_help("test-unit", "Run non-integration tests")

    with chdir(TESTS_DIR):
        _run(
            sys.executable, "-m", "pytest",
            "-m", "not integration_test",
            "-rfE", "-vv", "--force-regen",
            "-n", "auto",
        )


def test_binary():
    """Run integration tests against the built binary."""
    _print_help("test-binary", "Run integration tests against built binary")

    action_server_executable = (
        ROOT / "dist" / "final" / ("action-server" + (".exe" if sys.platform == "win32" else ""))
    )

    if not action_server_executable.exists():
        print(f"Error: Expected {action_server_executable} to exist.")
        print("Build the executable first with: uv run build-exe")
        sys.exit(1)

    # Set up clean environment
    env = os.environ.copy()
    env.pop("PYTHONPATH", "")
    env.pop("PYTHONHOME", "")
    env.pop("VIRTUAL_ENV", "")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHON_EXE"] = str(sys.executable)
    env["SEMA4AI_INTEGRATION_TEST_ACTION_SERVER_EXECUTABLE"] = str(action_server_executable)

    # Parse -k argument for test filter
    test_filter = ""
    for i, arg in enumerate(sys.argv):
        if arg == "-k" and i + 1 < len(sys.argv):
            test_filter = sys.argv[i + 1]

    args = [
        sys.executable, "-m", "pytest",
        "-m", "integration_test",
        "-rfE", "-vv", "--force-regen",
        "-n", "0",  # No parallelism due to RCC issues
    ]
    if test_filter:
        args.extend(["-k", test_filter])

    _run(*args, env=env, cwd=TESTS_DIR)


# =============================================================================
# Building
# =============================================================================

def build():
    """Build wheel distribution."""
    _print_help("build", "Build wheel distribution")

    with chdir(ROOT):
        _run("uv", "build")


def build_frontend():
    """Build frontend static assets."""
    _print_help("build-frontend", "Build frontend static assets")

    debug = "--debug" in sys.argv
    no_install = "--no-install" in sys.argv

    with chdir(FRONTEND_DIR):
        if not no_install:
            _run("npm", "ci", "--no-audit", "--no-fund")
        if debug:
            _run("npm", "run", "build:debug")
        else:
            _run("npm", "run", "build")

    index_src = FRONTEND_DIR / "dist" / "index.html"
    if not index_src.exists():
        print(f"Error: Expected {index_src} to exist.")
        sys.exit(1)

    dest_static_contents = ROOT / "src" / "sema4ai" / "action_server" / "_static_contents.py"

    file_contents = {"index.html": index_src.read_bytes()}

    with open(dest_static_contents, "w", encoding="utf-8", newline="\n") as stream:
        print(f"Writing static contents to: {dest_static_contents}")
        stream.write(
            f"""# coding: utf-8
# Note: autogenerated file.
# To regenerate this file use: uv run build-frontend

# The FILE_CONTENTS contains the contents of the files with
# html/javascript code for the static assets we use.

FILE_CONTENTS = {repr(file_contents)}
"""
        )


def build_oauth2_config():
    """Fetch and embed OAuth2 configs from GitHub."""
    _print_help("build-oauth2-config", "Fetch and embed OAuth2 configs")

    sema4ai_config_file_name = "sema4ai-oauth-config.yaml"
    default_user_config_file_name = "oauth-config.yaml"
    base_api_url = "repos/Sema4AI/oauth-public-configs/contents"
    dest_path = ROOT / "src" / "sema4ai" / "action_server" / "_oauth2_config.py"

    result_sema4ai_config_contents = subprocess.run(
        [
            "gh", "api",
            "-H", "Accept: application/vnd.github.raw",
            f"{base_api_url}/{sema4ai_config_file_name}",
        ],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.decode("utf-8")

    default_user_config_contents = subprocess.run(
        [
            "gh", "api",
            "-H", "Accept: application/vnd.github.raw",
            f"{base_api_url}/{default_user_config_file_name}",
        ],
        stdout=subprocess.PIPE,
        check=True,
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
# To regenerate this file use: uv run build-oauth2-config

# The FILE_CONTENTS contains the contents of the Sema4.ai OAuth2 configuration, as well as default user configuration.

FILE_CONTENTS = {repr(file_contents)}
"""
        )


def build_executable():
    """Build PyInstaller executable."""
    _print_help("build-exe", "Build PyInstaller executable")

    # Import here to avoid issues when packages aren't installed yet
    from sema4ai.build_common.root_dir import get_root_dir
    from sema4ai.build_common.workflows import build_and_sign_executable

    debug = "--debug" in sys.argv
    sign = "--sign" in sys.argv
    go_wrapper = "--go-wrapper" in sys.argv

    version = None
    for arg in sys.argv:
        if arg.startswith("--version="):
            version = arg.split("=", 1)[1]

    if version is None:
        from sema4ai.action_server import __version__
        version = __version__

    root_dir = get_root_dir()
    build_and_sign_executable(
        root_dir=root_dir,
        name="action-server",
        debug=debug,
        ci=True,
        dist_path=root_dir / "dist",
        sign=sign,
        go_wrapper=go_wrapper,
        version=version,
        go_wrapper_name=None,
    )


def build_go_wrapper():
    """Build the Go wrapper."""
    _print_help("build-go", "Build Go wrapper")

    with chdir(GO_WRAPPER_DIR):
        target = "action-server-unsigned" + (".exe" if sys.platform == "win32" else "")
        _run("go", "build", "-o", target)
        print(f"Built go wrapper at: {os.path.abspath(target)}")


def dev_frontend():
    """Run frontend dev server (vite)."""
    _print_help("dev-frontend", "Run frontend dev server")

    with chdir(FRONTEND_DIR):
        _run("npm", "run", "dev")


def download_rcc():
    """Download RCC binary."""
    _print_help("download-rcc", "Download RCC binary")

    env = os.environ.copy()
    curr_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = curr_pythonpath + os.pathsep + str(ROOT / "src")

    _run(sys.executable, "-m", "sema4ai.action_server", "download-rcc", env=env)


def clean():
    """Clean build artifacts."""
    _print_help("clean", "Clean build artifacts")

    from sema4ai.build_common.root_dir import get_root_dir
    from sema4ai.build_common.workflows import clean_common_build_artifacts

    clean_common_build_artifacts(get_root_dir())


# =============================================================================
# Entry point for direct execution
# =============================================================================

if __name__ == "__main__":
    list_tasks()
