import os
from pathlib import Path

import pytest

from sema4ai.common.package_exclude import ExclusionPatternError, PackageExcludeHandler


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")


def _normalize_relpath(path: str) -> str:
    normalized = path.replace(os.sep, "/")
    if os.altsep:
        normalized = normalized.replace(os.altsep, "/")
    return normalized


def test_collect_files_excluding_patterns(tmp_path: Path) -> None:
    _touch(tmp_path / "ignore" / "some.txt")
    _touch(tmp_path / "another" / "not_ok.txt")
    _touch(tmp_path / "another" / "ok.txt")
    _touch(tmp_path / "another" / "no.foo")
    _touch(tmp_path / "folder" / "dont_ignore")
    _touch(tmp_path / "folder" / "ignore_only_at_root")
    _touch(tmp_path / "hello_action.py")
    _touch(tmp_path / "package.yaml")
    _touch(tmp_path / "ignore_only_at_root")

    handler = PackageExcludeHandler()
    handler.fill_exclude_patterns(
        ["ignore/**", "not_ok.txt", "*.foo", "./ignore_only_at_root"]
    )

    found = {
        _normalize_relpath(relpath)
        for _, relpath in handler.collect_files_excluding_patterns(tmp_path)
    }

    assert found == {
        "another/ok.txt",
        "folder/dont_ignore",
        "folder/ignore_only_at_root",
        "hello_action.py",
        "package.yaml",
    }


def test_invalid_exclusion_patterns() -> None:
    handler = PackageExcludeHandler()

    with pytest.raises(ExclusionPatternError):
        handler.fill_exclude_patterns("not-a-list")

    with pytest.raises(ExclusionPatternError):
        handler.fill_exclude_patterns([123])


def test_filter_relative_paths_excluding_patterns() -> None:
    handler = PackageExcludeHandler()
    handler.fill_exclude_patterns(
        ["ignore/**", "not_ok.txt", "*.foo", "./ignore_only_at_root", "/root_only.txt"]
    )

    paths = [
        "ignore/some.txt",
        "another/not_ok.txt",
        "another/ok.txt",
        "another/no.foo",
        "folder/dont_ignore",
        "folder/ignore_only_at_root",
        "hello_action.py",
        "package.yaml",
        "ignore_only_at_root",
        "root_only.txt",
        "nested/root_only.txt",
        "win\\path\\no.foo",
    ]

    assert handler.filter_relative_paths_excluding_patterns(paths) == [
        "another/ok.txt",
        "folder/dont_ignore",
        "folder/ignore_only_at_root",
        "hello_action.py",
        "package.yaml",
        "nested/root_only.txt",
    ]
