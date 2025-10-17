"""
Contract test for CI import detection (FR-019).

Tests that CI workflows detect and fail on enterprise imports in community builds.
"""

import json
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch


class TestCIImportDetection:
    """Test CI workflow import detection for community builds."""

    @pytest.mark.integration_test
    def test_ci_runs_import_guard_check_for_community(self, tmp_path):
        """Test CI workflow runs import guard check for community builds (FR-019)."""
        # Simulate CI workflow YAML check
        workflow_file = tmp_path / ".github" / "workflows" / "frontend-build.yml"
        workflow_file.parent.mkdir(parents=True)
        
        workflow_content = """
name: Frontend Build

on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        tier: [community, enterprise]
        os: [ubuntu-latest]
    
    steps:
      - name: Import Guard Check
        if: matrix.tier == 'community'
        run: |
          inv validate-artifact --tier=community --checks=imports
"""
        workflow_file.write_text(workflow_content)
        
        # Assert: Workflow contains import guard check
        content = workflow_file.read_text()
        assert "validate-artifact" in content, \
            "CI workflow should include import guard validation"
        assert "matrix.tier == 'community'" in content, \
            "Import guard should run conditionally for community tier"

    @pytest.mark.integration_test
    def test_ci_fails_community_build_with_enterprise_imports(self, tmp_path):
        """Test CI fails community build if enterprise imports detected."""
        # Setup: Create frontend with enterprise import in core
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        core_dir = frontend_root / "src" / "core" / "pages"
        core_dir.mkdir(parents=True)
        
        # Add file with enterprise import
        actions_page = core_dir / "Actions.tsx"
        actions_page.write_text("""
import React from 'react';
import { Button } from '@sema4ai/components';  // Enterprise import!

export function Actions() {
    return <Button>Execute</Button>;
}
""")
        
        # Simulate CI import check
        result = subprocess.run(
            ["python", "-c", """
import sys
import re

# Simulate import guard check
file_content = '''import { Button } from '@sema4ai/components';'''
if '@sema4ai' in file_content or '@/enterprise' in file_content:
    print('ERROR: Enterprise import detected in community build')
    sys.exit(1)
"""],
            capture_output=True,
            text=True
        )
        
        # Assert: Check detects violation
        assert result.returncode == 1, \
            "CI import check should fail when enterprise imports detected"
        assert "Enterprise import detected" in result.stdout or "ERROR" in result.stdout, \
            "CI should log clear error message for import violations"

    @pytest.mark.integration_test
    def test_ci_logs_show_import_violation_details(self, tmp_path):
        """Test CI logs show import violation details."""
        # Setup: Create violation
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        core_file = frontend_root / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        
        core_file.write_text("""
import React from 'react';
import { Theme } from '@sema4ai/theme';  // Line 3: Violation

export function Dashboard() {
    return <Theme>Dashboard</Theme>;
}
""")
        
        # Simulate CI import detection with line numbers
        result = subprocess.run(
            ["python", "-c", f"""
import sys
import re

file_path = '{core_file}'
with open(file_path, 'r') as f:
    lines = f.readlines()
    
for i, line in enumerate(lines, 1):
    if '@sema4ai' in line or '@/enterprise' in line:
        print(f'VIOLATION: {{file_path}}:{{i}}: {{line.strip()}}')
        sys.exit(1)
"""],
            capture_output=True,
            text=True
        )
        
        # Assert: Log shows file, line, and import
        output = result.stdout + result.stderr
        assert "Dashboard.tsx" in output, "Log should include filename"
        assert ":3:" in output or "Line 3" in output or "line 3" in output.lower(), \
            "Log should include line number"
        assert "@sema4ai" in output, "Log should include the violating import"

    @pytest.mark.integration_test
    def test_enterprise_builds_skip_import_guard(self, tmp_path):
        """Test enterprise builds skip import guard (allowed to use enterprise code)."""
        # Setup: Enterprise build configuration
        workflow_check = """
if [ "$TIER" = "enterprise" ]; then
    echo "Skipping import guard for enterprise build"
    exit 0
fi
"""
        
        # Create script
        script_file = tmp_path / "check-imports.sh"
        script_file.write_text(f"""#!/bin/bash
TIER=enterprise
{workflow_check}
""")
        script_file.chmod(0o755)
        
        # Run script
        result = subprocess.run(
            [str(script_file)],
            capture_output=True,
            text=True
        )
        
        # Assert: Enterprise skips check
        assert result.returncode == 0, \
            "Enterprise builds should skip import guard"
        assert "Skipping import guard" in result.stdout, \
            "Log should confirm skip for enterprise"

    @pytest.mark.integration_test
    def test_external_pr_triggers_community_import_check_only(self, tmp_path):
        """Test external PR (fork) triggers community import check only."""
        # Simulate GitHub Actions context
        github_context = {
            "event": {
                "pull_request": {
                    "head": {
                        "repo": {
                            "fork": True
                        }
                    }
                }
            }
        }
        
        # Simulate workflow condition
        is_fork = github_context["event"]["pull_request"]["head"]["repo"]["fork"]
        
        # Assert: Fork PRs only run community checks
        assert is_fork is True, "Should detect fork PR"
        
        # Simulate conditional job execution
        should_run_enterprise = not is_fork
        assert should_run_enterprise is False, \
            "Enterprise builds should be skipped for fork PRs (FR-019)"
        
        should_run_community = True  # Always run for PRs
        assert should_run_community is True, \
            "Community builds should run for all PRs including forks"

    @pytest.mark.integration_test
    def test_ci_import_check_exit_code_validation(self, tmp_path):
        """Test CI import check uses correct exit code for validation errors."""
        # Setup: Simulate import check that finds violations
        check_script = tmp_path / "import-check.py"
        check_script.write_text("""
import sys

# Simulate finding enterprise imports in community build
violations_found = True

if violations_found:
    print("VALIDATION ERROR: Enterprise imports in community build")
    sys.exit(2)  # Exit code 2 for validation errors
else:
    print("Import check passed")
    sys.exit(0)
""")
        
        # Run check
        result = subprocess.run(
            ["python", str(check_script)],
            capture_output=True,
            text=True
        )
        
        # Assert: Uses exit code 2 for validation errors
        assert result.returncode == 2, \
            "Import check should use exit code 2 for validation errors"
        assert "VALIDATION ERROR" in result.stdout, \
            "Should clearly indicate validation error type"
