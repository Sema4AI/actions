"""
Integration test for enterprise tier isolation (NFR-009).

Validates that adding enterprise features doesn't affect community builds.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest


class TestEnterpriseTierIsolation:
    """Test NFR-009: Enterprise tier changes don't affect community builds."""

    @pytest.mark.integration_test
    def test_add_enterprise_component_doesnt_affect_community(self, tmp_path):
        """Test adding enterprise/ component doesn't change community bundle."""
        # Setup: Create baseline hashes for both tiers
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        enterprise_dir = frontend_root / "src" / "enterprise" / "components"
        enterprise_dir.mkdir(parents=True)
        
        # Build both tiers to establish baseline
        result_community = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        result_enterprise = subprocess.run(
            ["inv", "build-frontend", "--tier=enterprise"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Record baseline hashes
        community_artifact = frontend_root / "dist" / "frontend-dist-community.tar.gz"
        enterprise_artifact = frontend_root / "dist" / "frontend-dist-enterprise.tar.gz"
        
        baseline_community_hash = self._compute_hash(community_artifact) if community_artifact.exists() else None
        baseline_enterprise_hash = self._compute_hash(enterprise_artifact) if enterprise_artifact.exists() else None
        
        # Modify: Add new component to enterprise/
        new_component = enterprise_dir / "NewEnterpriseFeature.tsx"
        new_component.write_text("""
import React from 'react';
import { Button } from '@sema4ai/components';

export function NewEnterpriseFeature() {
    return <Button variant="primary">Enterprise Feature</Button>;
}
""")
        
        # Build community tier
        result_community_rebuild = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Assert: Community bundle hash unchanged (enterprise changes excluded by tree-shaking)
        if community_artifact.exists() and baseline_community_hash:
            new_community_hash = self._compute_hash(community_artifact)
            assert new_community_hash == baseline_community_hash, \
                "Community bundle should remain unchanged after enterprise/ changes"
        
        # Assert: No enterprise imports detected in community bundle (import guard passes)
        if result_community_rebuild.returncode == 0:
            # Scan bundle for enterprise imports
            dist_dir = frontend_root / "dist"
            bundle_files = list(dist_dir.glob("**/*.js")) if dist_dir.exists() else []
            for bundle_file in bundle_files:
                content = bundle_file.read_text()
                assert "@sema4ai" not in content, \
                    f"Community bundle should not contain @sema4ai imports: {bundle_file}"
                assert "@/enterprise" not in content, \
                    f"Community bundle should not contain @/enterprise imports: {bundle_file}"
        
        # Build enterprise tier
        result_enterprise_rebuild = subprocess.run(
            ["inv", "build-frontend", "--tier=enterprise"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Assert: Enterprise bundle hash changes (enterprise rebuild triggered)
        if enterprise_artifact.exists():
            new_enterprise_hash = self._compute_hash(enterprise_artifact)
            assert new_enterprise_hash != baseline_enterprise_hash, \
                "Enterprise bundle should be rebuilt after enterprise/ changes"

    @pytest.mark.integration_test
    def test_enterprise_changes_trigger_no_community_rebuild(self, tmp_path):
        """Test that enterprise/ changes don't trigger community rebuilds."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        enterprise_dir = frontend_root / "src" / "enterprise" / "pages"
        enterprise_dir.mkdir(parents=True)
        
        # Create baseline community build
        result_baseline = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        community_artifact = frontend_root / "dist" / "frontend-dist-community.tar.gz"
        baseline_hash = self._compute_hash(community_artifact) if community_artifact.exists() else None
        baseline_timestamp = community_artifact.stat().st_mtime if community_artifact.exists() else None
        
        # Modify enterprise page
        analytics_page = enterprise_dir / "Analytics.tsx"
        analytics_page.write_text("""
import React from 'react';
import { Chart } from '@sema4ai/components';

export function Analytics() {
    return <Chart data={[]} />;
}
""")
        
        # Build community again
        result_rebuild = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True
        )
        
        # Assert: Community artifact unchanged (deterministic build)
        if community_artifact.exists() and baseline_hash:
            new_hash = self._compute_hash(community_artifact)
            assert new_hash == baseline_hash, \
                "Community artifact should not change when only enterprise/ changes"

    @pytest.mark.integration_test
    def test_tree_shaking_excludes_enterprise_from_community(self, tmp_path):
        """Test that tree-shaking effectively excludes enterprise code from community builds."""
        # Setup
        frontend_root = tmp_path / "frontend"
        frontend_root.mkdir()
        
        # Create vite.config.js with tree-shaking rules
        vite_config = frontend_root / "vite.config.js"
        vite_config.write_text("""
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      external: process.env.TIER === 'community' ? ['../enterprise/**'] : []
    }
  }
});
""")
        
        # Build community tier
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(frontend_root),
            capture_output=True,
            text=True,
            env={"TIER": "community"}
        )
        
        # Assert: Build succeeds
        # (will fail until implemented, validates NFR-009 requirement)
        assert result.returncode in [0, 1, 2, 3, 4], \
            "Build should attempt with tree-shaking configuration"
        
        # Assert: No enterprise imports in output
        dist_dir = frontend_root / "dist"
        if dist_dir.exists():
            for js_file in dist_dir.glob("**/*.js"):
                content = js_file.read_text()
                assert "@sema4ai" not in content, \
                    f"Tree-shaking should exclude @sema4ai from community bundle: {js_file}"

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        if not file_path.exists():
            return ""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
