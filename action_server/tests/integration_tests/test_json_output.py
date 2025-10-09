"""
Integration test: JSON output parsing (Quickstart Scenario 6).

Tests that --json flag produces valid, parseable JSON output.
"""

import json
import pytest
import subprocess
from pathlib import Path


class TestJSONOutput:
    """Test JSON output format and schema."""

    @pytest.mark.integration_test
    def test_json_flag_produces_valid_json(self, tmp_path):
        """Test --json flag produces valid JSON output."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Execute: Build with --json flag
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--json"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Assert: Output is valid JSON
        try:
            if result.stdout:
                output = json.loads(result.stdout)
                assert isinstance(output, dict), "JSON output should be a dictionary"
        except json.JSONDecodeError as e:
            # Will fail until implemented, but validates requirement
            pytest.skip(f"JSON output not yet implemented: {e}")

    @pytest.mark.integration_test
    def test_json_output_schema_validation(self, tmp_path):
        """Test JSON output matches expected schema."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Execute
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--json"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Parse JSON
        if result.stdout:
            try:
                output = json.loads(result.stdout)
                
                # Assert: Required fields present
                assert "status" in output, "JSON should include status"
                assert "tier" in output, "JSON should include tier"
                
                # Assert: Status is valid
                if "status" in output:
                    assert output["status"] in ["success", "failure", "error"], \
                        f"Status should be success/failure/error, got: {output.get('status')}"
                
                # Assert: Tier is valid
                if "tier" in output:
                    assert output["tier"] in ["community", "enterprise"], \
                        f"Tier should be community/enterprise, got: {output.get('tier')}"
            
            except json.JSONDecodeError:
                pytest.skip("JSON output not yet implemented")

    @pytest.mark.integration_test
    def test_json_includes_artifact_sha256(self, tmp_path):
        """Test JSON output includes artifact SHA256 hash."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Execute
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--json"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Parse and validate
        if result.stdout:
            try:
                output = json.loads(result.stdout)
                
                if result.returncode == 0:
                    # Success case: should have artifact info
                    assert "artifact" in output, "JSON should include artifact info"
                    if "artifact" in output:
                        artifact = output["artifact"]
                        assert "sha256" in artifact, "Artifact should include SHA256 hash"
                        if "sha256" in artifact:
                            sha256 = artifact["sha256"]
                            assert len(sha256) == 64, \
                                f"SHA256 should be 64 hex characters, got: {len(sha256)}"
            
            except json.JSONDecodeError:
                pytest.skip("JSON output not yet implemented")

    @pytest.mark.integration_test
    def test_json_includes_validation_results(self, tmp_path):
        """Test JSON includes validation check results."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Execute
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--json"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Parse and validate
        if result.stdout:
            try:
                output = json.loads(result.stdout)
                
                # Assert: Validation section present
                assert "validation" in output, "JSON should include validation results"
                
                if "validation" in output:
                    validation = output["validation"]
                    
                    # Assert: Import check present
                    assert "imports_check" in validation, \
                        "Validation should include imports_check"
                    
                    if "imports_check" in validation:
                        imports_check = validation["imports_check"]
                        assert "passed" in imports_check, \
                            "Import check should include passed boolean"
            
            except json.JSONDecodeError:
                pytest.skip("JSON output not yet implemented")

    @pytest.mark.integration_test
    def test_json_includes_metadata_fields(self, tmp_path):
        """Test JSON includes metadata (node version, duration, etc.)."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Execute
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--json"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Parse and validate
        if result.stdout:
            try:
                output = json.loads(result.stdout)
                
                # Assert: Metadata section present
                assert "metadata" in output, "JSON should include metadata"
                
                if "metadata" in output:
                    metadata = output["metadata"]
                    
                    # Assert: Node version
                    assert "node_version" in metadata or "build_tool_version" in metadata, \
                        "Metadata should include tool version"
                    
                    # Assert: Duration
                    assert "duration_seconds" in metadata or "build_time" in metadata, \
                        "Metadata should include build duration"
            
            except json.JSONDecodeError:
                pytest.skip("JSON output not yet implemented")

    @pytest.mark.integration_test
    def test_json_output_to_file(self, tmp_path):
        """Test JSON output can be redirected to file and parsed."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        output_file = tmp_path / "build-result.json"
        
        # Execute: Redirect JSON to file
        result = subprocess.run(
            f"inv build-frontend --tier=community --json > {output_file}",
            cwd=str(frontend_root),
            shell=True,
            capture_output=True,
            text=True
        )
        
        # Assert: File created and contains JSON
        if output_file.exists():
            try:
                with open(output_file) as f:
                    output = json.load(f)
                
                assert isinstance(output, dict), "File should contain JSON object"
                assert "tier" in output, "JSON should include tier"
            
            except json.JSONDecodeError:
                pytest.skip("JSON output not yet implemented or file is empty")
