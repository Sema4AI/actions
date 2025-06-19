from pathlib import Path

import pytest

from sema4ai.actions._collect_actions import FindActionPaths


def create_test_structure(tmpdir):
    """Create a test directory structure."""
    temp_dir = Path(tmpdir)

    # Create some Python files
    (temp_dir / "test1.py").write_text("# test file 1")
    (temp_dir / "test2.py").write_text("# test file 2")

    # Create a subdirectory with Python files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "test3.py").write_text("# test file 3")

    # Create skip directories
    for skip_dir in ["__pycache__", ".git", "node_modules", ".venv"]:
        skip_path = temp_dir / skip_dir
        skip_path.mkdir()
        (skip_path / "should_not_find.py").write_text("# should not be found")

    # Create nested structure
    nested = temp_dir / "nested" / "deep"
    nested.mkdir(parents=True)
    (nested / "test4.py").write_text("# test file 4")

    return ["test1.py", "test2.py", "subdir/test3.py", "nested/deep/test4.py"]


@pytest.fixture
def library_roots(tmpdir):
    """Create a library roots directory under tmpdir for testing."""
    temp_dir = Path(tmpdir)
    lib_root = temp_dir / "site-packages"
    lib_root.mkdir()
    return [str(lib_root)]


def test_finds_all_python_files_with_default_pattern(tmpdir, library_roots):
    """Test that FindActionPaths finds all Python files with default pattern."""
    temp_dir = Path(tmpdir)
    expected_files = create_test_structure(tmpdir)

    finder = FindActionPaths(temp_dir, ["*"], library_roots)
    found_files = [str(f.relative_to(temp_dir)).replace("\\", "/") for f in finder]

    assert len(found_files) == 4
    for expected in expected_files:
        assert expected in found_files


def test_respects_glob_patterns(tmpdir, library_roots):
    """Test that FindActionPaths respects glob patterns."""
    temp_dir = Path(tmpdir)
    create_test_structure(tmpdir)

    # Test specific pattern
    finder = FindActionPaths(temp_dir, ["test1.py"], library_roots)
    found_files = [f.name for f in finder]

    assert found_files == ["test1.py"]


def test_handles_multiple_glob_patterns(tmpdir, library_roots):
    """Test that FindActionPaths handles multiple glob patterns."""
    temp_dir = Path(tmpdir)
    create_test_structure(tmpdir)

    finder = FindActionPaths(temp_dir, ["test1.py", "test2.py"], library_roots)
    found_files = sorted([f.name for f in finder])

    assert found_files == ["test1.py", "test2.py"]


def test_skips_common_directories(tmpdir, library_roots):
    """Test that FindActionPaths skips common directories."""
    temp_dir = Path(tmpdir)
    create_test_structure(tmpdir)

    finder = FindActionPaths(temp_dir, ["*"], library_roots)
    found_files = [f.name for f in finder]

    # Should not find files in skip directories
    assert "should_not_find.py" not in found_files


def test_avoids_library_roots(tmpdir, library_roots):
    """Test that FindActionPaths avoids library roots."""
    temp_dir = Path(tmpdir)

    # Create a structure that mimics a library root
    lib_root = Path(library_roots[0])
    (lib_root / "some_lib.py").write_text("# library file")

    # Create a regular file outside library root
    (temp_dir / "regular.py").write_text("# regular file")

    finder = FindActionPaths(temp_dir, ["*.py"], [str(lib_root)])
    found_files = [f.name for f in finder]

    # Should only find the regular file, not the library file
    assert found_files == ["regular.py"]
    assert "some_lib.py" not in found_files


def test_handles_nonexistent_paths(tmpdir, library_roots):
    """Test that FindActionPaths handles nonexistent paths gracefully."""
    temp_dir = Path(tmpdir)
    nonexistent_path = temp_dir / "nonexistent"

    finder = FindActionPaths(nonexistent_path, ["*.py"], library_roots)
    found_files = list(finder)

    assert found_files == []


def test_handles_permission_errors(tmpdir, library_roots):
    """Test that FindActionPaths handles permission errors gracefully."""
    temp_dir = Path(tmpdir)
    create_test_structure(tmpdir)

    # Create a directory that might cause permission issues
    restricted_dir = temp_dir / "restricted"
    restricted_dir.mkdir()
    (restricted_dir / "test.py").write_text("# test")

    # Mock os.access to simulate permission error
    original_iterdir = Path.iterdir

    def mock_iterdir(self):
        if self == restricted_dir:
            raise PermissionError("Permission denied")
        return original_iterdir(self)

    Path.iterdir = mock_iterdir

    try:
        finder = FindActionPaths(temp_dir, ["*.py"], library_roots)
        found_files = [f.name for f in finder]

        # Should still find other files, just skip the restricted directory
        assert len(found_files) >= 3  # At least the original files
    finally:
        Path.iterdir = original_iterdir


def test_sorts_output_consistently(tmpdir, library_roots):
    """Test that FindActionPaths provides consistent ordering."""
    temp_dir = Path(tmpdir)
    create_test_structure(tmpdir)

    finder1 = FindActionPaths(temp_dir, ["*.py"], library_roots)
    files1 = [str(f.relative_to(temp_dir)) for f in finder1]

    finder2 = FindActionPaths(temp_dir, ["*.py"], library_roots)
    files2 = [str(f.relative_to(temp_dir)) for f in finder2]

    assert files1 == files2


def test_handles_empty_directory(tmpdir, library_roots):
    """Test that FindActionPaths handles empty directories."""
    temp_dir = Path(tmpdir)
    finder = FindActionPaths(temp_dir, ["*.py"], library_roots)
    found_files = list(finder)

    assert found_files == []


def test_handles_non_python_files(tmpdir, library_roots):
    """Test that FindActionPaths only returns Python files."""
    temp_dir = Path(tmpdir)

    # Create non-Python files
    (temp_dir / "test.txt").write_text("text file")
    (temp_dir / "test.py").write_text("# python file")
    (temp_dir / "test.js").write_text("// javascript file")

    finder = FindActionPaths(temp_dir, ["*"], library_roots)
    found_files = [f.name for f in finder]

    assert found_files == ["test.py"]
    assert "test.txt" not in found_files
    assert "test.js" not in found_files


def test_respects_depth_limitation(tmpdir, library_roots):
    """Test that FindActionPaths respects the 3-level depth limitation."""
    temp_dir = Path(tmpdir)

    # Create a deep directory structure (4 levels)
    deep_path = temp_dir / "level1" / "level2" / "level3" / "level4"
    deep_path.mkdir(parents=True)

    # Create Python files at different levels
    (temp_dir / "root.py").write_text("# root level")
    (temp_dir / "level1" / "level1.py").write_text("# level 1")
    (temp_dir / "level1" / "level2" / "level2.py").write_text("# level 2")
    (temp_dir / "level1" / "level2" / "level3" / "level3.py").write_text("# level 3")
    (temp_dir / "level1" / "level2" / "level3" / "level4" / "level4.py").write_text(
        "# level 4"
    )

    finder = FindActionPaths(temp_dir, ["*.py"], library_roots)
    found_files = [f.name for f in finder]

    # Should find files up to level 3 (depth 3), but not level 4
    # Depth 0: root.py
    # Depth 1: level1.py
    # Depth 2: level2.py
    # Depth 3: level3.py
    # Depth 4: level4.py (should be excluded)
    expected_files = ["root.py", "level1.py", "level2.py", "level3.py"]
    assert sorted(found_files) == sorted(expected_files)
    assert "level4.py" not in found_files
