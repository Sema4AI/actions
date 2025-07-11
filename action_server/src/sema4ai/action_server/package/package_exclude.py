import fnmatch
import glob
import os
from pathlib import Path
from typing import Any, Iterator


class PackageExcludeHandler:
    """
    Handles the exclude patterns for the package.
    """

    def __init__(self) -> None:
        self.exclude_patterns: list[str] = []

    def fill_exclude_patterns(self, exclude_list: Any) -> None:
        """
        Args:
            exclude_list: List of strings with exclude patterns.
                Note that we accept "Any" because the validation is done
                in this function (as it usually comes from the package.yaml file
                and thus is untrusted at this point).
        """
        from sema4ai.action_server._errors_action_server import (
            ActionServerValidationError,
        )

        if exclude_list:
            if not isinstance(exclude_list, list):
                raise ActionServerValidationError(
                    "Expected 'packaging.exclude' section in package.yaml to be a list[str]."
                )

            for pat in exclude_list:
                if not isinstance(pat, str):
                    raise ActionServerValidationError(
                        f"Expected 'packaging.exclude' section in package.yaml to be a list[str]. Found item: {pat} ({type(pat)}) in list."
                    )

                if pat.startswith("./"):
                    # If the user did './b/c', we have to start the match from
                    # the current path.
                    pat = pat[2:]
                elif pat.startswith("/"):
                    # If the user did '/b/c', we have to start the match from
                    # the root.
                    pat = pat[1:]
                elif not pat.startswith("**"):
                    # If the user did not anchor the pattern, make it available to
                    # be matched anywhere (i.e.: *.pyc must match .pyc files anywhere).
                    pat = f"**/{pat}"

                self.exclude_patterns.append(pat)

    def collect_files_excluding_patterns(
        self, root_dir: Path
    ) -> Iterator[tuple[Path, str]]:
        """
        Collects all files within a directory, excluding those that match any of the
        specified exclusion patterns.
        """
        return _collect_files_excluding_patterns(root_dir, self.exclude_patterns)


def _check_matches(patterns, paths):
    if not patterns and not paths:
        # Matched to the end.
        return True

    if (not patterns and paths) or (patterns and not paths):
        return False

    pattern = patterns[0]
    path = paths[0]

    if not glob.has_magic(pattern):
        if pattern != path:
            return False

    elif pattern == "**":
        if len(patterns) == 1:
            return True  # if ** is the last one it matches anything to the right.

        for i in range(len(paths)):
            # Recursively check the remaining patterns as the
            # current pattern could match any number of paths.
            if _check_matches(patterns[1:], paths[i:]):
                return True

    elif not fnmatch.fnmatch(path, pattern):
        # Current part doesn't match.
        return False

    return _check_matches(patterns[1:], paths[1:])


def _glob_matches_path(path, pattern, sep=os.sep, altsep=os.altsep):
    if altsep:
        pattern = pattern.replace(altsep, sep)
        path = path.replace(altsep, sep)

    patterns = pattern.split(sep)
    paths = path.split(sep)
    if paths:
        if paths[0] == "":
            paths = paths[1:]
    if patterns:
        if patterns[0] == "":
            patterns = patterns[1:]

    return _check_matches(patterns, paths)


def _collect_files_excluding_patterns(
    root_dir: Path, exclusion_patterns: list[str]
) -> Iterator[tuple[Path, str]]:
    """
    Collects all files within a directory, excluding those that match any of the
    specified exclusion patterns.

    Args:
        root_dir (str): The root directory to traverse.
        exclusion_patterns (list): A list of fnmatch patterns to exclude.

    Returns:
        An iterator over the full paths and the relative paths (str) found.
    """

    for path in root_dir.rglob("*"):  # Use rglob for recursive iteration
        if path.is_file():
            relative_path_str = str(path.relative_to(root_dir))

            add = True
            for pattern in exclusion_patterns:
                if _glob_matches_path(relative_path_str, pattern):
                    add = False
                    break

            if add:
                yield path, relative_path_str
