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
        ruff_format_arguments=r"--exclude=_static_contents.py,_oauth_config.py",
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
    RESOLVED_CURDIR = CURDIR.resolve()

    with chdir(RESOLVED_CURDIR / "build-binary"):
        yield


@contextmanager
def _change_to_build_go_wrapper():
    RESOLVED_CURDIR = CURDIR.resolve()

    with chdir(RESOLVED_CURDIR / "go-wrapper"):
        yield


@task
def dev_frontend(ctx: Context):
    """Run the frontend in dev mode (starts its own localhost server using vite)."""

    with _change_to_frontend_dir():
        run(ctx, "npm", "run", "dev")


@task
def build_frontend(ctx: Context, debug: bool = False, install: bool = True):
    """Build static .html frontend"""

    with _change_to_frontend_dir():
        if install:
            run(ctx, "npm", "ci", "--no-audit", "--no-fund")
        if debug:
            run(ctx, "npm", "run", "build:debug")
        else:
            run(ctx, "npm", "run", "build")

    index_src = CURDIR / "frontend" / "dist" / "index.html"
    assert index_src.exists(), f"Expected: {index_src} to exist."
    dest_static_contents = (
        CURDIR / "src" / "sema4ai" / "action_server" / "_static_contents.py"
    )

    file_contents = {"index.html": index_src.read_bytes()}

    with open(dest_static_contents, "w", encoding="utf-8") as stream:
        print(f"Writing static contents to: {dest_static_contents}")
        stream.write(
            f"""# coding: utf-8
# Note: autogenerated file.
# To regenerate this file use: inv built-frontend.

# The FILE_CONTENTS contains the contents of the files with
# html/javascript code for the static assets we use.

FILE_CONTENTS = {repr(file_contents)}
"""
        )
        
@task
def build_oauth_config(ctx: Context):
    """Build static OAuth2 .yaml config."""
    sema4ai_config_file_name = "sema4ai-oauth-config.yaml"
    default_user_config_file_name = "oauth-config.yaml"
    sema4ai_config_local_file_path = CURDIR / sema4ai_config_file_name
    default_user_config_local_file_path = CURDIR / default_user_config_file_name
    
    base_api_url = "repos/Sema4AI/oauth-public-configs/contents"
    
    dest_path = (
        CURDIR / "src" / "sema4ai" / "action_server" / "_oauth_config.py"
    )
    
    run(ctx,
        "gh",
        "api",
        "-H \"Accept: application/vnd.github.raw\"",
        f"{base_api_url}/{sema4ai_config_file_name}",
        f"> {sema4ai_config_local_file_path}"
    )
    
    assert sema4ai_config_local_file_path.exists(), f"Expected {sema4ai_config_local_file_path} to exist."

    run(ctx,
        "gh",
        "api",
        "-H \"Accept: application/vnd.github.raw\"",
        f"{base_api_url}/{default_user_config_file_name}",
        f"> {default_user_config_local_file_path}"
    )

    assert default_user_config_local_file_path.exists(), f"Expected {default_user_config_local_file_path} to exist."
    
    with open(sema4ai_config_local_file_path) as sema4ai_config_file, open(default_user_config_local_file_path) as user_config_file:
        file_contents = {
            "sema4ai_config": sema4ai_config_file.read(),
            "default_user_config": user_config_file.read()
        }
    
    with open(dest_path, "w", encoding='utf-8') as stream:
        print(f"Writing OAuth configs to: {dest_path}")
        stream.write(
            f"""# coding: utf-8
# Note: autogenerated file.
# To regenerate this file use: inv build-oauth-config.

# The FILE_CONTENTS contains the contents of the Sema4.ai OAuth configuration, as well as default user configuration.

FILE_CONTENTS = {repr(file_contents)}
"""
        )
    

@task
def build_binary(ctx: Context) -> None:
    with _change_to_build_binary():
        run(ctx, "pyoxidizer", "run", "--release")


@task
def build_go_wrapper(ctx: Context) -> None:
    with _change_to_build_go_wrapper():
        run(ctx, "go", "build", "-o", "action-server-unsigned")


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
def update_pyoxidizer_versions(ctx: Context):
    """
    Updates the dependencies for pyoxidizer given the versions in pyproject.toml.
    """
    import tomlkit

    pyproject: dict = tomlkit.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    deps = pyproject["tool"]["poetry"]["dependencies"]
    use_versions = []
    for dep_name, version in deps.items():
        if dep_name == "python":
            continue

        parts = version.split(".")
        if len(parts) >= 3:
            # Drop the minor for compatibility
            version = ".".join(parts[:-1])

        elif len(parts) == 1:
            # Just the major version is specified
            assert version.startswith("^")
            v = int(version[1:])
            version = f">={v},<{v+1}"

        version = version.replace("^", "~=")
        use_versions.append(f'"{dep_name}{version}",')
    use_versions = sorted(use_versions)

    blz_file = CURDIR / "build-binary" / "pyoxidizer.bzl"
    assert blz_file.exists()
    contents = blz_file.read_text().replace("\r\n", "\n").replace("\r", "\n")
    indent = "            "
    new_contents = _replace_deps(
        contents, indent + f"\n{indent}".join(use_versions) + f"\n{indent}"
    )
    if new_contents != contents:
        blz_file.write_text(new_contents)
        print("pyoxidizer.bzl updated.")
    else:
        print("pyoxidizer.bzl already up to date.")
