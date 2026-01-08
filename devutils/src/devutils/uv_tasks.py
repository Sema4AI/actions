"""
Common UV task implementations.

These functions provide shared functionality for UV-based task runners across
projects. They are designed to be called from project-specific uv_tasks.py files.

This module has no dependencies on invoke or poetry - it uses subprocess directly.
"""

import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import List, Optional

# Repository root (devutils is at repo_root/devutils/src/devutils/)
REPO_ROOT = Path(__file__).parent.parent.parent.parent


def _run_cmd(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command with optional directory and environment."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=capture_output, text=True)
    if check and result.returncode != 0:
        if capture_output:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result


def get_tag(tag_prefix: str) -> str:
    """Get the last tagged version for a given prefix.

    Args:
        tag_prefix: The tag prefix to match (i.e.: "sema4ai-action-server")

    Returns:
        The full tag string (e.g., 'sema4ai-action-server-3.0.0')
    """
    cmd = f"git describe --tags --abbrev=0 --match {tag_prefix}-[0-9]*"
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    return proc.stdout.strip()


def get_all_tags(tag_prefix: str) -> List[str]:
    """Get all tags matching a prefix."""
    cmd = "git tag"
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    tags = proc.stdout.strip().splitlines()
    regex = re.compile(rf"{tag_prefix}-[\d.]+$")
    return [tag for tag in tags if regex.match(tag)]


def to_identifier(value: str) -> str:
    """Convert a string to a valid Python identifier."""
    value = re.sub(r"[^\w\s_]", "", value.lower())
    value = re.sub(r"[_\s]+", "_", value).strip("_")
    return value


# =============================================================================
# Documentation
# =============================================================================

def run_docs(
    root: Path,
    package_name: str,
    output_path: Path,
    repository_url: str = "https://github.com/sema4ai/actions/tree/master/",
    check: bool = False,
    validate: bool = False,
) -> None:
    """Build API documentation using lazydocs.

    Args:
        root: Project root directory
        package_name: Python package name (e.g., "sema4ai.action_server")
        output_path: Path to output documentation
        repository_url: Base URL for source links
        check: If True, check for uncommitted doc changes
        validate: If True, only validate docs
    """
    if validate:
        _run_cmd(["lazydocs", "--validate", package_name], cwd=root)
        return

    if not output_path.exists():
        print("Docs output path does not exist. Skipping...")
        return

    # Clear existing docs
    for path in output_path.iterdir():
        path.unlink()

    _run_cmd(
        [
            "lazydocs",
            "--no-watermark",
            "--remove-package-prefix",
            f"--src-base-url={repository_url}",
            "--overview-file=README.md",
            f"--output-path={output_path}",
            package_name,
        ],
        cwd=root,
    )

    if check:
        result = subprocess.run(
            ["git", "--no-pager", "diff", "--name-only", "--", "docs/api"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        changed_files = result.stdout.strip().splitlines()
        if changed_files:
            diff_result = subprocess.run(
                ["git", "--no-pager", "diff", "--", "docs/api"],
                capture_output=True,
                text=True,
                cwd=root,
            )
            raise RuntimeError(
                f"There are uncommitted docs changes. Changes: {diff_result.stdout}"
            )


def run_doctest(root: Path, source_directories: tuple = ("src", "tests")) -> None:
    """Statically verify documentation examples.

    Extracts Python code blocks from .py and .md files and validates them with mypy.
    """
    pattern = re.compile(r"^\s*```python([\s\S]*?)\s*```", re.MULTILINE)
    files = [
        (root / "src").rglob("*.py"),
        (root / "docs" / "guides").rglob("*.md"),
    ]

    output = ""
    for path in chain(*files):
        dirname = to_identifier(path.parent.name)
        filename = to_identifier(path.name)

        content = path.read_text()
        matches = re.findall(pattern, content)
        if not matches:
            continue

        print(f"Found examples in: {path}")
        output += f"\n# {path.name}\n"
        for index, match in enumerate(matches):
            code = textwrap.indent(textwrap.dedent(match), "    ")
            output += f"\ndef codeblock_{dirname}_{filename}_{index}() -> None:"
            output += code
            output += "\n"

    if not output:
        print("No example blocks found")
        return

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as tmp:
        print(f"Validating project: {root.name}")
        for lineno, line in enumerate(output.splitlines(), 1):
            print(f"{lineno:3}: {line}")

        tmp.write(output)
        tmp.close()
        _run_cmd(["mypy", "--strict", tmp.name], cwd=root)


# =============================================================================
# Version Management
# =============================================================================

def update_changelog_file(file: Path, version: str) -> None:
    """Update the changelog file with the new version and changes."""
    if not file.exists():
        print(f"No CHANGELOG file found, skipping update.\nExpected path: {file}")
        return

    with open(file, "r+") as stream:
        content = stream.read()

        new_version = f"## {version} - {datetime.today().strftime('%Y-%m-%d')}"
        changelog_start_match = re.search(r"# Changelog", content)
        if not changelog_start_match:
            print(
                f"Did not find # Changelog in the changelog:\n{file}\n"
                f"Please update Changelog before proceeding."
            )
            sys.exit(1)

        changelog_start = changelog_start_match.end()

        unreleased_match = re.search(r"## Unreleased", content, flags=re.IGNORECASE)
        double_newline = "\n\n"

        new_content = content[:changelog_start] + double_newline + "## Unreleased"
        if unreleased_match:
            released_content = content.replace(unreleased_match.group(), new_version)
            new_content += released_content[changelog_start:]
        else:
            new_content += double_newline + new_version + content[changelog_start:]

        stream.seek(0)
        stream.write(new_content)
        print("Changed: ", file)

        if not unreleased_match:
            print(
                f"\nDid not find ## Unreleased in the changelog:\n{file}\n"
                f"Please update Changelog before proceeding.\n"
                f"It was updated to have the proper sessions already..."
            )
            sys.exit(1)


def run_set_version(root: Path, package_name: str, version: str) -> None:
    """Set a new version for the project in all the needed files.

    Updates version in:
    - pyproject.toml
    - package __init__.py
    - CHANGELOG.md
    """
    valid_version_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    if not valid_version_pattern.match(version):
        print(f"Invalid version: {version}. Must be in the format major.minor.hotfix")
        sys.exit(1)

    version_patterns = (
        re.compile(r"(version\s*=\s*)\"\d+\.\d+\.\d+"),
        re.compile(r"(__version__\s*=\s*)\"\d+\.\d+\.\d+"),
        re.compile(r"(\"version\"\s*:\s*)\"\d+\.\d+\.\d+"),
    )

    def update_version(version: str, filepath: Path) -> None:
        with open(filepath, "r") as stream:
            before = stream.read()

        after = before
        for pattern in version_patterns:
            after = re.sub(pattern, r'\1"%s' % (version,), after)

        if before != after:
            print("Changed: ", filepath)
            with open(filepath, "w") as stream:
                stream.write(after)

    # Update version in current project pyproject.toml
    update_version(version, root / "pyproject.toml")

    # Update version in current project __init__.py
    package_path = package_name.split(".")
    init_file = root / "src" / Path(*package_path) / "__init__.py"
    update_version(version, init_file)

    # Update changelog
    update_changelog_file(root / "docs" / "CHANGELOG.md", version)


def run_check_tag_version(tag_prefix: str, module_version: str) -> None:
    """Check if the current tag matches the module version.

    Exits with 0 if versions match, 1 otherwise.
    """
    tag = get_tag(tag_prefix)
    version = tag[tag.rfind("-") + 1:]

    if module_version == version:
        sys.stderr.write(f"Version matches ({version}) (exit(0))\n")
        sys.exit(0)
    else:
        sys.stderr.write(
            f"Version does not match ({tag_prefix}: {module_version} !="
            f" repo tag: {version}).\nTags:{get_all_tags(tag_prefix)}\n(exit(1))\n"
        )
        sys.exit(1)


def run_make_release(root: Path, tag_prefix: str, module_version: str) -> None:
    """Create a release tag.

    Args:
        root: Project root directory
        tag_prefix: Tag prefix (e.g., "sema4ai-action-server")
        module_version: Current module version
    """
    import semver

    # Check we're on master
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    branch = result.stdout.strip()
    if branch != "master":
        sys.stderr.write(f"Not on master branch: {branch}\n")
        sys.exit(1)

    previous_tag = get_tag(tag_prefix)
    previous_version = previous_tag.split("-")[-1] if previous_tag else ""

    if not previous_version:
        print(f"No previous release for {tag_prefix}")
    elif previous_version == "beta":
        print(f"Previous release was beta for {tag_prefix}")
    elif semver.compare(module_version, previous_version) <= 0:
        sys.stderr.write(
            f"Current version older/same than previous:"
            f" {module_version} <= {previous_version}\n"
        )
        sys.exit(1)

    current_tag = f"{tag_prefix}-{module_version}"
    _run_cmd(
        [
            "git", "tag", "-a", current_tag,
            "-m", f"Release {module_version} for {tag_prefix}",
        ],
        cwd=root,
    )

    print(f"Pushing tag: {current_tag}")
    _run_cmd(["git", "push", "origin", current_tag], cwd=root)


def run_publish(root: Path) -> None:
    """Publish to PyPI using uv."""
    _run_cmd(["uv", "publish"], cwd=root)
