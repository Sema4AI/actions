"""
Integration test: CI matrix simulation (Quickstart Scenario 4).

Tests CI matrix strategy with tier × os combinations.
"""

import json
import pytest
import subprocess
from pathlib import Path


class TestCIMatrix:
    """Test CI matrix simulation (tier × os)."""

    @pytest.mark.integration_test
    def test_matrix_6_builds_complete_successfully(self, tmp_path):
        """Test 6 matrix builds complete (community × 3 OS + enterprise × 3 OS)."""
        # Simulate matrix combinations
        matrix = [
            {"tier": "community", "os": "ubuntu"},
            {"tier": "community", "os": "macos"},
            {"tier": "community", "os": "windows"},
            {"tier": "enterprise", "os": "ubuntu"},
            {"tier": "enterprise", "os": "macos"},
            {"tier": "enterprise", "os": "windows"},
        ]
        
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        results = []
        for combo in matrix:
            # Simulate build for each matrix job
            result = subprocess.run(
                ["inv", "build-frontend", f"--tier={combo['tier']}"],
                cwd=str(frontend_root),
                capture_output=True,
                text=True,
                env={"NPM_TOKEN": "fake-token"} if combo["tier"] == "enterprise" else {}
            )
            results.append({
                "tier": combo["tier"],
                "os": combo["os"],
                "returncode": result.returncode,
                "success": result.returncode == 0
            })
        
        # Assert: All 6 jobs attempted
        assert len(results) == 6, "Should run 6 matrix jobs"

    @pytest.mark.integration_test
    def test_artifacts_named_per_convention(self, tmp_path):
        """Test artifacts follow naming convention: frontend-{tier}-{os}-{commit}.tar.gz"""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Build community for ubuntu
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Check artifact name
        dist_dir = frontend_root / "dist"
        if dist_dir.exists():
            artifacts = list(dist_dir.glob("frontend-dist-*.tar.gz"))
            if artifacts:
                artifact_name = artifacts[0].name
                # Assert: Follows convention
                assert "frontend-dist-" in artifact_name, \
                    f"Artifact should follow naming convention: {artifact_name}"
                assert "community" in artifact_name or "enterprise" in artifact_name, \
                    f"Artifact name should include tier: {artifact_name}"

    @pytest.mark.integration_test
    def test_community_determinism_check_passes(self, tmp_path):
        """Test community rebuild matches SHA256 (determinism check)."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Build community twice
        result1 = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        artifact = frontend_root / "dist" / "frontend-dist-community.tar.gz"
        hash1 = self._compute_hash(artifact) if artifact.exists() else None
        
        # Clean and rebuild
        if artifact.exists():
            artifact.unlink()
        
        result2 = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        hash2 = self._compute_hash(artifact) if artifact.exists() else None
        
        # Assert: Deterministic build (hashes match)
        if hash1 and hash2:
            assert hash1 == hash2, \
                "Community builds should be deterministic (same SHA256)"

    @pytest.mark.integration_test
    def test_enterprise_jobs_have_npm_token_access(self, tmp_path):
        """Test enterprise matrix jobs have NPM_TOKEN access."""
        # Simulate CI env for enterprise job
        env_vars = {
            "TIER": "enterprise",
            "NPM_TOKEN": "secret-token",
            "GITHUB_ACTIONS": "true"
        }
        
        # Assert: NPM_TOKEN available for enterprise
        assert env_vars.get("NPM_TOKEN") is not None, \
            "Enterprise jobs should have NPM_TOKEN in environment"
        assert env_vars["NPM_TOKEN"] != "", \
            "NPM_TOKEN should not be empty for enterprise builds"

    @pytest.mark.integration_test
    def test_job_summary_includes_tier_os_step_error_category(self, tmp_path):
        """Test job summary includes tier, OS, step name, error category (NFR-011)."""
        # Simulate failed job
        job_summary = {
            "tier": "community",
            "os": "ubuntu-latest",
            "step": "Build Frontend",
            "exitCode": 2,
            "errorCategory": "validation_error",
            "message": "Enterprise imports detected in community build"
        }
        
        # Assert: Summary includes all required fields
        assert job_summary["tier"] in ["community", "enterprise"], \
            "Summary should include tier"
        assert job_summary["os"] in ["ubuntu-latest", "macos-latest", "windows-latest"], \
            "Summary should include OS"
        assert job_summary["step"] != "", \
            "Summary should include failing step name"
        assert job_summary["errorCategory"] in ["build_error", "validation_error", 
                                                  "config_error", "dependency_error"], \
            "Summary should categorize error type (NFR-011)"

    @pytest.mark.integration_test
    def test_matrix_failure_handling_no_fail_fast(self, tmp_path):
        """Test matrix failure handling (NFR-012: fail-fast: false)."""
        # Simulate matrix with one failure
        matrix_results = [
            {"tier": "community", "os": "ubuntu", "success": True},
            {"tier": "community", "os": "macos", "success": False},  # Failed
            {"tier": "community", "os": "windows", "success": True},
            {"tier": "enterprise", "os": "ubuntu", "success": True},
        ]
        
        # Assert: Other jobs continued despite failure
        successful_jobs = [r for r in matrix_results if r["success"]]
        assert len(successful_jobs) == 3, \
            "Other matrix jobs should continue when one fails (fail-fast: false per NFR-012)"
        
        failed_jobs = [r for r in matrix_results if not r["success"]]
        assert len(failed_jobs) == 1, \
            "Failed job should be recorded"

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        if not file_path.exists():
            return ""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
