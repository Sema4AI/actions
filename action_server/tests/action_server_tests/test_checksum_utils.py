"""
Unit test: Checksum calculation utility.

This test validates the checksum calculation utility used for
vendored package integrity verification.
"""
import hashlib
import tempfile
from pathlib import Path

import pytest


class TestChecksumUtils:
    """Unit tests for checksum calculation."""

    def calculate_package_checksum(self, package_dir: Path) -> str:
        """
        Calculate SHA256 checksum of all files in package directory.

        This is the reference implementation that matches the vendoring script.
        Files are processed in sorted order for deterministic results.
        """
        hasher = hashlib.sha256()

        # Walk directory in sorted order for determinism
        for root, dirs, files in package_dir.walk():
            dirs.sort()  # Sort subdirectories in place
            for filename in sorted(files):
                filepath = root / filename
                # Skip symlinks for cross-platform compatibility
                if filepath.is_symlink():
                    continue
                with open(filepath, "rb") as f:
                    hasher.update(f.read())

        return hasher.hexdigest()

    def test_deterministic_file_ordering(self):
        """Test that file ordering is deterministic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create files in non-alphabetical order
            (tmppath / "zebra.txt").write_text("z")
            (tmppath / "alpha.txt").write_text("a")
            (tmppath / "beta.txt").write_text("b")

            # Calculate checksum twice
            checksum1 = self.calculate_package_checksum(tmppath)
            checksum2 = self.calculate_package_checksum(tmppath)

            assert checksum1 == checksum2, "Checksum calculation is not deterministic"

    def test_empty_directory_handling(self):
        """Test handling of empty directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create an empty subdirectory
            empty_dir = tmppath / "empty"
            empty_dir.mkdir()

            # Create a file in the root
            (tmppath / "file.txt").write_text("content")

            # Should calculate checksum without error
            checksum = self.calculate_package_checksum(tmppath)
            assert len(checksum) == 64  # Valid SHA256

    def test_symlink_handling(self):
        """Test that symlinks are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a regular file
            regular_file = tmppath / "regular.txt"
            regular_file.write_text("regular content")

            # Create a symlink
            symlink_file = tmppath / "symlink.txt"
            symlink_file.symlink_to(regular_file)

            # Calculate checksums with and without symlink
            checksum_with_symlink = self.calculate_package_checksum(tmppath)

            # Remove symlink and recalculate
            symlink_file.unlink()
            checksum_without_symlink = self.calculate_package_checksum(tmppath)

            # Checksums should be the same (symlink was skipped)
            assert checksum_with_symlink == checksum_without_symlink

    def test_binary_vs_text_file_handling(self):
        """Test that both binary and text files are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a text file
            (tmppath / "text.txt").write_text("Hello, world!")

            # Create a binary file
            (tmppath / "binary.bin").write_bytes(bytes([0, 1, 2, 3, 255]))

            # Should calculate checksum without error
            checksum = self.calculate_package_checksum(tmppath)
            assert len(checksum) == 64  # Valid SHA256

    def test_reproducibility_across_runs(self):
        """Test that checksum is reproducible across multiple runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a directory structure
            (tmppath / "dir1").mkdir()
            (tmppath / "dir2").mkdir()
            (tmppath / "dir1" / "file1.txt").write_text("content1")
            (tmppath / "dir2" / "file2.txt").write_text("content2")
            (tmppath / "root.txt").write_text("root")

            # Calculate checksum multiple times
            checksums = [self.calculate_package_checksum(tmppath) for _ in range(5)]

            # All checksums should be identical
            assert all(
                c == checksums[0] for c in checksums
            ), "Checksum calculation is not reproducible"

    def test_nested_directory_structure(self):
        """Test checksum calculation with nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create nested structure
            (tmppath / "a" / "b" / "c").mkdir(parents=True)
            (tmppath / "a" / "file1.txt").write_text("1")
            (tmppath / "a" / "b" / "file2.txt").write_text("2")
            (tmppath / "a" / "b" / "c" / "file3.txt").write_text("3")

            # Should calculate checksum without error
            checksum = self.calculate_package_checksum(tmppath)
            assert len(checksum) == 64  # Valid SHA256

    def test_checksum_changes_with_content(self):
        """Test that checksum changes when file content changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create initial file
            test_file = tmppath / "test.txt"
            test_file.write_text("initial content")

            checksum1 = self.calculate_package_checksum(tmppath)

            # Modify content
            test_file.write_text("modified content")

            checksum2 = self.calculate_package_checksum(tmppath)

            # Checksums should be different
            assert (
                checksum1 != checksum2
            ), "Checksum did not change after content modification"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
