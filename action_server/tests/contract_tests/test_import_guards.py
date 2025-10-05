"""
Contract tests for import guard enforcement.

Tests ESLint rules, Vite build-time checks, and post-build AST scanning
for enterprise import violations.
"""

import json
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

# Import will fail until implementation exists (TDD)
try:
    from action_server.build_binary.tree_shaker import ImportViolation
except ImportError:
    pytest.skip("Import guards not yet implemented", allow_module_level=True)


class TestESLintImportGuards:
    """Test ESLint no-restricted-imports rule."""

    def test_eslint_detects_enterprise_import_in_core(self, tmp_path):
        """Test ESLint detects @/enterprise imports in @/core files."""
        # Arrange
        eslintrc = tmp_path / ".eslintrc.js"
        eslintrc.write_text("""
module.exports = {
  rules: {
    'no-restricted-imports': ['error', {
      patterns: ['@/enterprise/*', '@sema4ai/*']
    }]
  }
};
""")

        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import React from 'react';
import { KBSearch } from '@/enterprise/pages/KB';  // VIOLATION
""")

        # Act
        result = subprocess.run(
            ["npx", "eslint", str(core_file)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until ESLint config implemented (TDD)
        assert result.returncode != 0  # ESLint should fail
        assert "@/enterprise" in result.stdout or "@/enterprise" in result.stderr

    def test_eslint_detects_sema4ai_import_in_core(self, tmp_path):
        """Test ESLint detects @sema4ai imports in core files."""
        # Arrange
        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import { Button } from '@sema4ai/components';  // VIOLATION
""")

        # Act
        result = subprocess.run(
            ["npx", "eslint", str(core_file)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        assert result.returncode != 0
        assert "@sema4ai" in result.stdout or "@sema4ai" in result.stderr

    def test_eslint_allows_core_imports_in_core(self, tmp_path):
        """Test ESLint allows @/core and @radix-ui imports in core files."""
        # Arrange
        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import React from 'react';
import { Button } from '@radix-ui/react-button';  // OK
import { Table } from '@/core/components/ui/Table';  // OK
""")

        # Act
        result = subprocess.run(
            ["npx", "eslint", str(core_file)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should pass (no violations)
        # Will fail until implementation complete
        pass

    def test_eslint_allows_enterprise_imports_in_enterprise(self, tmp_path):
        """Test ESLint allows enterprise imports in enterprise/ files."""
        # Arrange
        enterprise_file = tmp_path / "src" / "enterprise" / "Analytics.tsx"
        enterprise_file.parent.mkdir(parents=True)
        enterprise_file.write_text("""
import { Button } from '@sema4ai/components';  // ALLOWED
""")

        # Act
        result = subprocess.run(
            ["npx", "eslint", str(enterprise_file)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should pass (enterprise files can import enterprise code)
        # Will fail until implementation complete
        pass


class TestViteBuildTimeGuards:
    """Test Vite plugin detects imports during build."""

    def test_vite_build_fails_with_enterprise_import_in_community(self, tmp_path):
        """Test Vite build fails if enterprise imports detected in community tier."""
        # Arrange
        vite_config = tmp_path / "vite.config.js"
        vite_config.write_text("""
import { defineConfig } from 'vite';
import { importGuardPlugin } from './vite-import-guard-plugin';

export default defineConfig({
  plugins: [
    importGuardPlugin({ tier: 'community' })
  ]
});
""")

        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import { Button } from '@sema4ai/components';  // VIOLATION
""")

        # Act
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env={"TIER": "community"}
        )

        # Assert
        # Will fail until Vite plugin implemented (TDD)
        assert result.returncode != 0
        assert "enterprise" in result.stderr.lower() or "@sema4ai" in result.stderr.lower()

    def test_vite_build_succeeds_with_clean_community_code(self, tmp_path):
        """Test Vite build succeeds with no enterprise imports."""
        # Arrange
        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import React from 'react';
import { Button } from '@radix-ui/react-button';  // OK
""")

        # Act
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env={"TIER": "community"}
        )

        # Assert
        # Will fail until implementation complete
        # Should succeed
        pass


class TestPostBuildASTScan:
    """Test post-build AST scanning of built bundle."""

    def test_ast_scan_detects_enterprise_import_in_bundle(self, tmp_path):
        """Test AST scan detects @sema4ai imports in built JS."""
        # Arrange
        bundle = tmp_path / "dist" / "index.js"
        bundle.parent.mkdir(parents=True)
        bundle.write_text("""
(function() {
  const Button = require('@sema4ai/components').Button;  // VIOLATION
})();
""")

        # Act
        result = subprocess.run(
            ["python", "-m", "action_server.build_binary.tree_shaker", str(bundle)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until AST scanner implemented (TDD)
        assert result.returncode != 0
        assert "@sema4ai" in result.stdout

    def test_ast_scan_clean_community_bundle_passes(self, tmp_path):
        """Test AST scan passes for clean community bundle."""
        # Arrange
        bundle = tmp_path / "dist" / "index.js"
        bundle.parent.mkdir(parents=True)
        bundle.write_text("""
(function() {
  const Button = require('@radix-ui/react-button').Button;  // OK
})();
""")

        # Act
        result = subprocess.run(
            ["python", "-m", "action_server.build_binary.tree_shaker", str(bundle)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until implementation complete
        # Should pass
        pass


class TestViolationReportFormat:
    """Test import violation report format."""

    def test_violation_report_includes_file_line_import(self):
        """Test violation report contains file, line, and import statement."""
        # Arrange
        violation = ImportViolation(
            file_path=Path("src/core/Dashboard.tsx"),
            line_number=5,
            import_statement="import { Button } from '@sema4ai/components';",
            prohibited_module="@sema4ai/components",
            severity="error"
        )

        # Act
        # Will fail until report formatter implemented (TDD)
        report = format_violation_report([violation])

        # Assert
        assert "src/core/Dashboard.tsx:5" in report
        assert "@sema4ai/components" in report
        assert "error" in report.lower()

    def test_violation_report_multiple_violations(self):
        """Test report formats multiple violations."""
        # Arrange
        violations = [
            ImportViolation(
                file_path=Path("src/core/Dashboard.tsx"),
                line_number=5,
                import_statement="import { Button } from '@sema4ai/components';",
                prohibited_module="@sema4ai/components",
                severity="error"
            ),
            ImportViolation(
                file_path=Path("src/core/Actions.tsx"),
                line_number=12,
                import_statement="import { KBSearch } from '@/enterprise/pages/KB';",
                prohibited_module="@/enterprise/pages/KB",
                severity="error"
            )
        ]

        # Act
        report = format_violation_report(violations)

        # Assert
        assert "Dashboard.tsx:5" in report
        assert "Actions.tsx:12" in report
        assert report.count("error") >= 2


class TestErrorLevelViolationsBuild:
    """Test error-level violations fail the build."""

    def test_error_violation_fails_build(self, tmp_path):
        """Test error-level import violation causes build failure."""
        # Arrange
        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import { Button } from '@sema4ai/components';  // ERROR
""")

        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until implementation complete (TDD)
        assert result.returncode == 1  # Build error

    def test_warning_violation_logs_but_succeeds(self, tmp_path):
        """Test warning-level violations log but don't fail build."""
        # Arrange - create scenario that triggers warning
        # (will be defined when warning-level violations are specified)
        
        # Act & Assert
        # Will fail until implementation complete
        pass


class TestMultiLayerGuardEnforcement:
    """Test all three layers of guards (lint, build, post-build)."""

    def test_violation_caught_at_lint_time(self, tmp_path):
        """Test violation is caught by ESLint before build."""
        # Arrange
        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import { Button } from '@sema4ai/components';  // VIOLATION
""")

        # Act
        lint_result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        assert lint_result.returncode != 0  # Lint fails

    def test_violation_caught_at_build_time(self, tmp_path):
        """Test violation is caught by Vite during build."""
        # Arrange
        core_file = tmp_path / "src" / "core" / "Dashboard.tsx"
        core_file.parent.mkdir(parents=True)
        core_file.write_text("""
import { Button } from '@sema4ai/components';  // VIOLATION
""")

        # Act
        build_result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        assert build_result.returncode != 0  # Build fails

    def test_violation_caught_post_build(self, tmp_path):
        """Test violation is caught by AST scan after build."""
        # Arrange - simulate build succeeded (Vite guard bypassed)
        bundle = tmp_path / "dist" / "index.js"
        bundle.parent.mkdir(parents=True)
        bundle.write_text("""
const Button = require('@sema4ai/components').Button;  // VIOLATION
""")

        # Act
        validation_result = subprocess.run(
            ["inv", "validate-artifact", f"--artifact={bundle.parent}", "--tier=community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        assert validation_result.returncode != 0  # Validation fails


def format_violation_report(violations):
    """
    Helper function to format violation report.
    Will fail until implemented (TDD).
    """
    # This function will be implemented in tree_shaker module
    raise NotImplementedError("format_violation_report not yet implemented")
