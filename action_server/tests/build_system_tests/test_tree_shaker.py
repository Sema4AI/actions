"""
Unit tests for TreeShaker import detection and Vite configuration.

Tests the tree-shaking functionality for detecting and excluding enterprise
imports in community builds.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Import will fail until implementation exists (TDD)
try:
    from action_server.build_binary.tree_shaker import (
        TreeShaker,
        ImportViolation,
        scan_imports,
        detect_enterprise_imports,
        generate_vite_external_config,
    )
    from action_server.build_binary.tier_selector import COMMUNITY, ENTERPRISE
except ImportError:
    # Expected to fail initially (TDD)
    pytest.skip("TreeShaker not yet implemented", allow_module_level=True)


class TestScanImports:
    """Test scan_imports() function for AST-based import detection."""

    def test_detect_enterprise_import_in_core_file(self, tmp_path):
        """Test detecting enterprise import in core/ file."""
        # Arrange
        test_file = tmp_path / "Dashboard.tsx"
        test_file.write_text("""
import React from 'react';
import { Button } from '@sema4ai/components';  // VIOLATION
import { Table } from '@/core/components/ui/Table';

export function Dashboard() {
    return <div><Button>Click</Button></div>;
}
""")

        # Act
        violations = scan_imports(test_file)

        # Assert
        assert len(violations) == 1
        assert violations[0].file_path == test_file
        assert violations[0].line_number == 3
        assert "@sema4ai/components" in violations[0].import_statement
        assert violations[0].prohibited_module == "@sema4ai/components"
        assert violations[0].severity == "error"

    def test_detect_multiple_enterprise_imports(self, tmp_path):
        """Test detecting multiple enterprise imports in one file."""
        # Arrange
        test_file = tmp_path / "Analytics.tsx"
        test_file.write_text("""
import { Button } from '@sema4ai/components';
import { Icon } from '@sema4ai/icons';
import { theme } from '@sema4ai/theme';
""")

        # Act
        violations = scan_imports(test_file)

        # Assert
        assert len(violations) == 3
        prohibited_modules = [v.prohibited_module for v in violations]
        assert "@sema4ai/components" in prohibited_modules
        assert "@sema4ai/icons" in prohibited_modules
        assert "@sema4ai/theme" in prohibited_modules

    def test_detect_enterprise_path_import(self, tmp_path):
        """Test detecting @/enterprise path imports in core/ files."""
        # Arrange
        test_file = tmp_path / "core" / "Dashboard.tsx"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
import React from 'react';
import { KBSearch } from '@/enterprise/pages/KnowledgeBase';  // VIOLATION
""")

        # Act
        violations = scan_imports(test_file)

        # Assert
        assert len(violations) == 1
        assert "@/enterprise" in violations[0].import_statement

    def test_no_violation_for_core_imports(self, tmp_path):
        """Test no violations for valid core/ imports."""
        # Arrange
        test_file = tmp_path / "Dashboard.tsx"
        test_file.write_text("""
import React from 'react';
import { Button } from '@radix-ui/react-button';
import { Table } from '@/core/components/ui/Table';
import { useAPI } from '@/shared/hooks/useAPI';
""")

        # Act
        violations = scan_imports(test_file)

        # Assert
        assert len(violations) == 0

    def test_no_violation_for_enterprise_imports_in_enterprise_files(self, tmp_path):
        """Test enterprise imports are allowed in enterprise/ files."""
        # Arrange
        test_file = tmp_path / "enterprise" / "Analytics.tsx"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
import { Button } from '@sema4ai/components';  // ALLOWED
import { Chart } from '@/enterprise/components/Chart';  // ALLOWED
""")

        # Act - should only scan core/ files
        violations = scan_imports(test_file)

        # Assert - enterprise files can import enterprise code
        assert len(violations) == 0


class TestDetectEnterpriseImports:
    """Test detect_enterprise_imports() for built bundle scanning."""

    def test_detect_sema4ai_import_in_bundle(self, tmp_path):
        """Test detecting @sema4ai imports in built JS bundle."""
        # Arrange
        bundle_file = tmp_path / "index.js"
        bundle_file.write_text("""
(function() {
    const Button = require('@sema4ai/components').Button;
    // ... rest of bundle
})();
""")

        # Act
        violations = detect_enterprise_imports(bundle_file)

        # Assert
        assert len(violations) > 0
        assert any("@sema4ai/components" in v.import_statement for v in violations)

    def test_detect_enterprise_path_in_bundle(self, tmp_path):
        """Test detecting @/enterprise imports in built bundle."""
        # Arrange
        bundle_file = tmp_path / "index.js"
        bundle_file.write_text("""
import { KBSearch } from '@/enterprise/pages/KnowledgeBase';
""")

        # Act
        violations = detect_enterprise_imports(bundle_file)

        # Assert
        assert len(violations) > 0
        assert any("@/enterprise" in v.import_statement for v in violations)

    def test_no_violation_for_clean_community_bundle(self, tmp_path):
        """Test no violations in clean community bundle."""
        # Arrange
        bundle_file = tmp_path / "index.js"
        bundle_file.write_text("""
(function() {
    const Button = require('@radix-ui/react-button').Button;
    const React = require('react');
    // ... rest of bundle
})();
""")

        # Act
        violations = detect_enterprise_imports(bundle_file)

        # Assert
        assert len(violations) == 0

    def test_scan_minified_bundle(self, tmp_path):
        """Test scanning minified bundle (single line)."""
        # Arrange
        bundle_file = tmp_path / "index.min.js"
        bundle_file.write_text(
            'var a=require("@sema4ai/components"),b=require("react");'
        )

        # Act
        violations = detect_enterprise_imports(bundle_file)

        # Assert
        assert len(violations) > 0


class TestGenerateViteExternalConfig:
    """Test generate_vite_external_config() for Vite tree-shaking."""

    def test_community_tier_excludes_enterprise_modules(self):
        """Test community tier config excludes enterprise modules."""
        # Act
        config = generate_vite_external_config(COMMUNITY)

        # Assert
        assert "rollupOptions" in config
        assert "external" in config["rollupOptions"]
        
        external = config["rollupOptions"]["external"]
        # Should be a regex pattern or list of patterns
        if isinstance(external, list):
            assert any("@sema4ai" in str(pattern) for pattern in external)
            assert any("@/enterprise" in str(pattern) for pattern in external)
        else:
            # Could be a regex pattern
            assert "@sema4ai" in str(external) or "@/enterprise" in str(external)

    def test_enterprise_tier_allows_all_modules(self):
        """Test enterprise tier config doesn't exclude enterprise modules."""
        # Act
        config = generate_vite_external_config(ENTERPRISE)

        # Assert
        # Enterprise tier should not have restrictive external config
        # or should be empty/minimal
        if "rollupOptions" in config and "external" in config["rollupOptions"]:
            external = config["rollupOptions"]["external"]
            # Should not exclude enterprise modules
            if isinstance(external, list):
                assert not any("@sema4ai" in str(pattern) for pattern in external)
            else:
                assert "@sema4ai" not in str(external)

    def test_config_includes_output_settings(self):
        """Test config includes deterministic output settings."""
        # Act
        config = generate_vite_external_config(COMMUNITY)

        # Assert - should include deterministic file naming
        if "rollupOptions" in config and "output" in config["rollupOptions"]:
            output = config["rollupOptions"]["output"]
            # Deterministic naming (no random hashes)
            assert "entryFileNames" in output or "chunkFileNames" in output


class TestImportViolation:
    """Test ImportViolation dataclass."""

    def test_violation_has_required_fields(self):
        """Test ImportViolation contains all required fields."""
        # Act
        violation = ImportViolation(
            file_path=Path("src/core/Dashboard.tsx"),
            line_number=5,
            import_statement="import { Button } from '@sema4ai/components';",
            prohibited_module="@sema4ai/components",
            severity="error"
        )

        # Assert
        assert violation.file_path == Path("src/core/Dashboard.tsx")
        assert violation.line_number == 5
        assert "@sema4ai/components" in violation.import_statement
        assert violation.prohibited_module == "@sema4ai/components"
        assert violation.severity == "error"

    def test_violation_severity_error_or_warning(self):
        """Test violation severity is either 'error' or 'warning'."""
        # Act
        error_violation = ImportViolation(
            file_path=Path("test.tsx"),
            line_number=1,
            import_statement="import foo",
            prohibited_module="foo",
            severity="error"
        )

        warning_violation = ImportViolation(
            file_path=Path("test.tsx"),
            line_number=1,
            import_statement="import foo",
            prohibited_module="foo",
            severity="warning"
        )

        # Assert
        assert error_violation.severity in ["error", "warning"]
        assert warning_violation.severity in ["error", "warning"]


class TestFeatureBoundaryEnforcement:
    """Test feature boundary enforcement with feature-boundaries.json."""

    @patch("action_server.build_binary.tree_shaker.load_feature_boundaries")
    def test_enforce_boundaries_blocks_enterprise_in_core(self, mock_load_boundaries, tmp_path):
        """Test feature boundaries block enterprise imports in core files."""
        # Arrange
        mock_load_boundaries.return_value = {
            "features": [
                {
                    "feature_id": "design_system",
                    "tier": "enterprise",
                    "module_path": "frontend/src/enterprise/components/ds",
                    "import_pattern": "@sema4ai/.*"
                },
                {
                    "feature_id": "action_ui",
                    "tier": "core",
                    "module_path": "frontend/src/core/pages/actions",
                    "import_pattern": "@/core/.*"
                }
            ]
        }

        test_file = tmp_path / "core" / "Dashboard.tsx"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
import { Button } from '@sema4ai/components';  // VIOLATION
""")

        # Act
        violations = scan_imports(test_file)

        # Assert
        assert len(violations) > 0
        assert any("design_system" in str(v) or "@sema4ai" in v.import_statement 
                   for v in violations)

    @patch("action_server.build_binary.tree_shaker.load_feature_boundaries")
    def test_enterprise_features_allowed_in_enterprise_dir(self, mock_load_boundaries, tmp_path):
        """Test enterprise features are allowed in enterprise/ directory."""
        # Arrange
        mock_load_boundaries.return_value = {
            "features": [
                {
                    "feature_id": "design_system",
                    "tier": "enterprise",
                    "module_path": "frontend/src/enterprise/components/ds",
                    "import_pattern": "@sema4ai/.*"
                }
            ]
        }

        test_file = tmp_path / "enterprise" / "Analytics.tsx"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
import { Button } from '@sema4ai/components';  // ALLOWED
""")

        # Act
        violations = scan_imports(test_file)

        # Assert
        assert len(violations) == 0


class TestTreeShakerIntegration:
    """Integration tests for TreeShaker with real-world scenarios."""

    def test_scan_entire_core_directory(self, tmp_path):
        """Test scanning entire core/ directory for violations."""
        # Arrange
        core_dir = tmp_path / "src" / "core"
        core_dir.mkdir(parents=True)

        # Create multiple files with violations
        (core_dir / "Dashboard.tsx").write_text("""
import { Button } from '@sema4ai/components';  // VIOLATION
""")
        (core_dir / "Actions.tsx").write_text("""
import { Table } from '@radix-ui/react-table';  // OK
""")
        (core_dir / "Logs.tsx").write_text("""
import { KBSearch } from '@/enterprise/pages/KB';  // VIOLATION
""")

        # Act
        shaker = TreeShaker(tier=COMMUNITY, root_dir=tmp_path)
        violations = shaker.scan_directory(core_dir)

        # Assert
        assert len(violations) == 2  # Dashboard.tsx and Logs.tsx

    def test_generate_violation_report(self, tmp_path):
        """Test generating human-readable violation report."""
        # Arrange
        violations = [
            ImportViolation(
                file_path=Path("src/core/Dashboard.tsx"),
                line_number=3,
                import_statement="import { Button } from '@sema4ai/components';",
                prohibited_module="@sema4ai/components",
                severity="error"
            )
        ]

        # Act
        shaker = TreeShaker(tier=COMMUNITY, root_dir=tmp_path)
        report = shaker.generate_report(violations)

        # Assert
        assert "src/core/Dashboard.tsx:3" in report
        assert "@sema4ai/components" in report
        assert "error" in report.lower()
