"""Integration test: Tier logging validation (T027a).

Validates FR-009: Build logs explicitly display selected tier.

Test cases:
1. Community tier logging
2. Enterprise tier logging
3. Tier logged at build start
"""

import subprocess
import sys
from pathlib import Path


def test_community_tier_logging_explicit():
    """Test that community tier is explicitly logged when specified."""
    # Get the action_server directory
    action_server_dir = Path(__file__).parent.parent.parent
    
    # Run build-frontend with community tier
    result = subprocess.run(
        [sys.executable, "-m", "invoke", "build-frontend", "--tier=community"],
        cwd=action_server_dir,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minutes timeout
    )
    
    # Check that tier is logged
    output = result.stdout + result.stderr
    assert "Building with tier: community" in output or \
           "🔨 Building with tier: community" in output, \
           f"Tier not logged in output. Stdout: {result.stdout}, Stderr: {result.stderr}"
    
    # Verify it's early in the output (before npm install)
    lines = output.split('\n')
    tier_line_idx = None
    npm_line_idx = None
    
    for idx, line in enumerate(lines):
        if "Building with tier: community" in line or "🔨 Building with tier: community" in line:
            tier_line_idx = idx
        if "Installing dependencies" in line or "npm ci" in line:
            npm_line_idx = idx
    
    assert tier_line_idx is not None, "Tier logging line not found"
    
    # If npm was run, tier should be logged before it
    if npm_line_idx is not None:
        assert tier_line_idx < npm_line_idx, \
            "Tier should be logged before dependency installation"


def test_enterprise_tier_logging_explicit():
    """Test that enterprise tier is explicitly logged when specified."""
    # Get the action_server directory
    action_server_dir = Path(__file__).parent.parent.parent
    
    # Run build-frontend with enterprise tier
    result = subprocess.run(
        [sys.executable, "-m", "invoke", "build-frontend", "--tier=enterprise"],
        cwd=action_server_dir,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minutes timeout
    )
    
    # Check that tier is logged
    output = result.stdout + result.stderr
    assert "Building with tier: enterprise" in output or \
           "🔨 Building with tier: enterprise" in output, \
           f"Tier not logged in output. Stdout: {result.stdout}, Stderr: {result.stderr}"
    
    # Verify it's early in the output (before npm install)
    lines = output.split('\n')
    tier_line_idx = None
    npm_line_idx = None
    
    for idx, line in enumerate(lines):
        if "Building with tier: enterprise" in line or "🔨 Building with tier: enterprise" in line:
            tier_line_idx = idx
        if "Installing dependencies" in line or "npm ci" in line:
            npm_line_idx = idx
    
    assert tier_line_idx is not None, "Tier logging line not found"
    
    # If npm was run, tier should be logged before it
    if npm_line_idx is not None:
        assert tier_line_idx < npm_line_idx, \
            "Tier should be logged before dependency installation"


def test_community_tier_logging_default():
    """Test that community tier is logged when using default (no --tier flag)."""
    # Get the action_server directory
    action_server_dir = Path(__file__).parent.parent.parent
    
    # Run build-frontend without tier flag (should default to community)
    result = subprocess.run(
        [sys.executable, "-m", "invoke", "build-frontend"],
        cwd=action_server_dir,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minutes timeout
    )
    
    # Check that tier is logged
    output = result.stdout + result.stderr
    assert "Building with tier: community" in output or \
           "🔨 Building with tier: community" in output, \
           f"Tier not logged in output. Stdout: {result.stdout}, Stderr: {result.stderr}"


def test_tier_logging_in_json_output():
    """Test that tier is included in JSON output mode."""
    # Get the action_server directory
    action_server_dir = Path(__file__).parent.parent.parent
    
    # Run build-frontend with JSON output
    result = subprocess.run(
        [sys.executable, "-m", "invoke", "build-frontend", "--tier=community", "--json"],
        cwd=action_server_dir,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minutes timeout
    )
    
    # Parse JSON output
    import json
    try:
        json_output = json.loads(result.stdout)
        assert "tier" in json_output, "Tier not in JSON output"
        assert json_output["tier"] == "community", f"Expected tier 'community', got {json_output['tier']}"
    except json.JSONDecodeError as e:
        # If JSON parsing fails, check for build output before JSON
        # Sometimes there's logging before the JSON output
        lines = result.stdout.strip().split('\n')
        # Try the last line which should be the JSON
        try:
            json_output = json.loads(lines[-1])
            assert "tier" in json_output, "Tier not in JSON output"
            assert json_output["tier"] == "community", f"Expected tier 'community', got {json_output['tier']}"
        except (json.JSONDecodeError, IndexError):
            raise AssertionError(f"Could not parse JSON output: {result.stdout}") from e
