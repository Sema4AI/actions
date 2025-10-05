"""Unit tests for DependencySource resolution logic.

Tests T008: DependencySource resolution, fallback order, and error handling
"""

import socket
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from package_resolver import (
    DependencyError,
    DependencySource,
    SourceType,
    resolve,
)


class TestDependencySourceClass:
    """Test DependencySource dataclass attributes."""
    
    def test_dependency_source_registry_attributes(self):
        """Test registry source has correct attributes."""
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
            requires_auth=False,
        )
        
        assert source.source_type == SourceType.REGISTRY
        assert source.priority == 1
        assert source.url == "https://registry.npmjs.org"
        assert source.requires_auth is False
        
    def test_dependency_source_vendored_attributes(self):
        """Test vendored source has correct attributes."""
        local_path = Path("/tmp/vendored")
        source = DependencySource(
            source_type=SourceType.VENDORED,
            priority=2,
            local_path=local_path,
            requires_auth=False,
        )
        
        assert source.source_type == SourceType.VENDORED
        assert source.priority == 2
        assert source.local_path == local_path
        assert source.requires_auth is False
        
    def test_dependency_source_cdn_attributes(self):
        """Test CDN source has correct attributes."""
        source = DependencySource(
            source_type=SourceType.CDN,
            priority=3,
            url="https://cdn.example.com",
            requires_auth=False,
        )
        
        assert source.source_type == SourceType.CDN
        assert source.priority == 3
        assert source.url == "https://cdn.example.com"


class TestSourceTypeEnum:
    """Test SourceType enum values."""
    
    def test_source_type_enum_values(self):
        """Test SourceType has correct string values."""
        assert SourceType.REGISTRY.value == "registry"
        assert SourceType.VENDORED.value == "vendored"
        assert SourceType.CDN.value == "cdn"
        
    def test_source_type_enum_count(self):
        """Test SourceType has exactly 3 values."""
        assert len(SourceType) == 3


class TestRegistryAvailability:
    """Test registry source availability checking."""
    
    @patch('subprocess.run')
    def test_registry_available_returns_true(self, mock_run):
        """Test check_availability returns True when npm ping succeeds."""
        mock_run.return_value = Mock(returncode=0)
        
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
        )
        
        assert source.check_availability() is True
        mock_run.assert_called_once()
        
    @patch('subprocess.run')
    def test_registry_unavailable_returns_false(self, mock_run):
        """Test check_availability returns False when npm ping fails."""
        mock_run.return_value = Mock(returncode=1)
        
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
        )
        
        assert source.check_availability() is False
        
    @patch('subprocess.run')
    def test_registry_timeout_returns_false(self, mock_run):
        """Test check_availability returns False on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("npm ping", 5)
        
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
        )
        
        assert source.check_availability(timeout=5) is False
        
    @patch('subprocess.run')
    def test_registry_npm_not_found_returns_false(self, mock_run):
        """Test check_availability returns False when npm command not found."""
        mock_run.side_effect = FileNotFoundError("npm not found")
        
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
        )
        
        assert source.check_availability() is False
        
    @patch('subprocess.run')
    def test_registry_uses_custom_url(self, mock_run):
        """Test registry check uses custom URL if provided."""
        mock_run.return_value = Mock(returncode=0)
        
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://custom.registry.com",
        )
        
        source.check_availability()
        
        call_args = mock_run.call_args[0][0]
        assert "https://custom.registry.com" in call_args
        
    @patch('subprocess.run')
    def test_registry_timeout_parameter_used(self, mock_run):
        """Test timeout parameter is passed to subprocess.run."""
        mock_run.return_value = Mock(returncode=0)
        
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
        )
        
        source.check_availability(timeout=10)
        
        assert mock_run.call_args[1]['timeout'] == 10


class TestVendoredAvailability:
    """Test vendored source availability checking."""
    
    def test_vendored_available_when_manifest_exists(self, tmp_path):
        """Test check_availability returns True when manifest.json exists."""
        vendored_path = tmp_path / "vendored"
        vendored_path.mkdir()
        manifest = vendored_path / "manifest.json"
        manifest.write_text('{"packages": []}')
        
        source = DependencySource(
            source_type=SourceType.VENDORED,
            priority=2,
            local_path=vendored_path,
        )
        
        assert source.check_availability() is True
        
    def test_vendored_unavailable_when_manifest_missing(self, tmp_path):
        """Test check_availability returns False when manifest.json missing."""
        vendored_path = tmp_path / "vendored"
        vendored_path.mkdir()
        # No manifest.json created
        
        source = DependencySource(
            source_type=SourceType.VENDORED,
            priority=2,
            local_path=vendored_path,
        )
        
        assert source.check_availability() is False
        
    def test_vendored_unavailable_when_directory_missing(self, tmp_path):
        """Test check_availability returns False when directory doesn't exist."""
        vendored_path = tmp_path / "nonexistent"
        
        source = DependencySource(
            source_type=SourceType.VENDORED,
            priority=2,
            local_path=vendored_path,
        )
        
        assert source.check_availability() is False
        
    def test_vendored_requires_local_path(self):
        """Test vendored source returns False when local_path is None."""
        source = DependencySource(
            source_type=SourceType.VENDORED,
            priority=2,
            local_path=None,
        )
        
        assert source.check_availability() is False


class TestCDNAvailability:
    """Test CDN source availability checking."""
    
    @patch('socket.create_connection')
    def test_cdn_available_returns_true(self, mock_socket):
        """Test check_availability returns True when CDN is reachable."""
        mock_socket.return_value = MagicMock()
        
        source = DependencySource(
            source_type=SourceType.CDN,
            priority=3,
            url="https://cdn.example.com/packages",
        )
        
        assert source.check_availability() is True
        mock_socket.assert_called_once()
        
    @patch('socket.create_connection')
    def test_cdn_timeout_returns_false(self, mock_socket):
        """Test check_availability returns False on socket timeout."""
        mock_socket.side_effect = socket.timeout("Connection timed out")
        
        source = DependencySource(
            source_type=SourceType.CDN,
            priority=3,
            url="https://cdn.example.com",
        )
        
        assert source.check_availability(timeout=5) is False
        
    @patch('socket.create_connection')
    def test_cdn_socket_error_returns_false(self, mock_socket):
        """Test check_availability returns False on socket error."""
        mock_socket.side_effect = socket.error("Network unreachable")
        
        source = DependencySource(
            source_type=SourceType.CDN,
            priority=3,
            url="https://cdn.example.com",
        )
        
        assert source.check_availability() is False
        
    @patch('socket.create_connection')
    def test_cdn_os_error_returns_false(self, mock_socket):
        """Test check_availability returns False on OS error."""
        mock_socket.side_effect = OSError("Connection failed")
        
        source = DependencySource(
            source_type=SourceType.CDN,
            priority=3,
            url="https://cdn.example.com",
        )
        
        assert source.check_availability() is False
        
    def test_cdn_requires_url(self):
        """Test CDN source returns False when url is None."""
        source = DependencySource(
            source_type=SourceType.CDN,
            priority=3,
            url=None,
        )
        
        assert source.check_availability() is False
        
    @patch('socket.create_connection')
    def test_cdn_timeout_parameter_used(self, mock_socket):
        """Test timeout parameter is passed to socket connection."""
        mock_socket.return_value = MagicMock()
        
        source = DependencySource(
            source_type=SourceType.CDN,
            priority=3,
            url="https://cdn.example.com",
        )
        
        source.check_availability(timeout=10)
        
        # Check timeout was passed to create_connection
        call_args = mock_socket.call_args[0]
        assert mock_socket.call_args[1]['timeout'] == 10


class TestResolveCommunityTier:
    """Test resolve() for community tier."""
    
    @patch('subprocess.run')
    def test_community_uses_public_registry_only(self, mock_run, tmp_path):
        """Test community tier only tries public npm registry."""
        mock_run.return_value = Mock(returncode=0)
        
        source = resolve("community", tmp_path)
        
        assert source.source_type == SourceType.REGISTRY
        assert source.url == "https://registry.npmjs.org"
        assert source.requires_auth is False
        
    @patch('subprocess.run')
    def test_community_registry_unavailable_raises_error(self, mock_run, tmp_path):
        """Test DependencyError raised when community registry unavailable."""
        mock_run.return_value = Mock(returncode=1)
        
        with pytest.raises(DependencyError) as exc_info:
            resolve("community", tmp_path)
        
        assert "No dependency sources available" in str(exc_info.value)
        assert "community" in str(exc_info.value)


class TestResolveEnterpriseTier:
    """Test resolve() for enterprise tier."""
    
    @patch('subprocess.run')
    def test_enterprise_uses_private_registry_first(self, mock_run, tmp_path):
        """Test enterprise tier tries private registry first."""
        mock_run.return_value = Mock(returncode=0)
        
        source = resolve("enterprise", tmp_path)
        
        assert source.source_type == SourceType.REGISTRY
        assert source.url == "https://npm.pkg.github.com"
        assert source.requires_auth is True
        assert source.priority == 1
        
    @patch('subprocess.run')
    def test_enterprise_falls_back_to_vendored(self, mock_run, tmp_path):
        """Test enterprise falls back to vendored when registry unavailable."""
        # Registry unavailable
        mock_run.return_value = Mock(returncode=1)
        
        # Create vendored manifest
        vendored_path = tmp_path / "vendored"
        vendored_path.mkdir()
        manifest = vendored_path / "manifest.json"
        manifest.write_text('{"packages": []}')
        
        source = resolve("enterprise", tmp_path)
        
        assert source.source_type == SourceType.VENDORED
        assert source.priority == 2
        assert source.local_path == vendored_path
        
    @patch('socket.create_connection')
    @patch('subprocess.run')
    def test_enterprise_falls_back_to_cdn(self, mock_run, mock_socket, tmp_path):
        """Test enterprise falls back to CDN when registry and vendored unavailable."""
        # Registry unavailable
        mock_run.return_value = Mock(returncode=1)
        
        # Vendored unavailable (no manifest)
        
        # CDN available
        mock_socket.return_value = MagicMock()
        
        source = resolve("enterprise", tmp_path)
        
        assert source.source_type == SourceType.CDN
        assert source.priority == 3
        assert source.url == "https://cdn.sema4ai.com"
        
    @patch('socket.create_connection')
    @patch('subprocess.run')
    def test_enterprise_all_sources_fail_raises_error(self, mock_run, mock_socket, tmp_path):
        """Test DependencyError when all enterprise sources unavailable."""
        # All sources unavailable
        mock_run.return_value = Mock(returncode=1)
        mock_socket.side_effect = socket.timeout()
        
        with pytest.raises(DependencyError) as exc_info:
            resolve("enterprise", tmp_path)
        
        error_msg = str(exc_info.value)
        assert "No dependency sources available" in error_msg
        assert "enterprise" in error_msg
        assert "registry" in error_msg
        assert "vendored" in error_msg
        assert "cdn" in error_msg


class TestResolveFallbackOrder:
    """Test fallback order is respected."""
    
    @patch('socket.create_connection')
    @patch('subprocess.run')
    def test_fallback_respects_priority_order(self, mock_run, mock_socket, tmp_path):
        """Test sources are tried in priority order (1, 2, 3)."""
        # Registry (priority 1) fails
        mock_run.return_value = Mock(returncode=1)
        
        # Create vendored (priority 2) available
        vendored_path = tmp_path / "vendored"
        vendored_path.mkdir()
        manifest = vendored_path / "manifest.json"
        manifest.write_text('{"packages": []}')
        
        # CDN (priority 3) also available but should not be tried
        mock_socket.return_value = MagicMock()
        
        source = resolve("enterprise", tmp_path)
        
        # Should return vendored (priority 2), not CDN (priority 3)
        assert source.source_type == SourceType.VENDORED
        
    @patch('subprocess.run')
    def test_stops_at_first_available_source(self, mock_run, tmp_path):
        """Test resolution stops at first available source."""
        # Registry (priority 1) available
        mock_run.return_value = Mock(returncode=0)
        
        # Create vendored (priority 2) also available
        vendored_path = tmp_path / "vendored"
        vendored_path.mkdir()
        manifest = vendored_path / "manifest.json"
        manifest.write_text('{"packages": []}')
        
        source = resolve("enterprise", tmp_path)
        
        # Should return registry (priority 1), not vendored
        assert source.source_type == SourceType.REGISTRY


class TestDependencyError:
    """Test DependencyError exception."""
    
    def test_dependency_error_is_exception(self):
        """Test DependencyError is an Exception subclass."""
        assert issubclass(DependencyError, Exception)
        
    def test_dependency_error_can_be_raised(self):
        """Test DependencyError can be raised and caught."""
        with pytest.raises(DependencyError):
            raise DependencyError("Test error")
            
    def test_dependency_error_message(self):
        """Test DependencyError can carry custom message."""
        error = DependencyError("Custom error message")
        assert str(error) == "Custom error message"


class TestResolveEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_resolve_with_invalid_tier(self, tmp_path):
        """Test resolve with invalid tier name (should not crash)."""
        # Implementation doesn't validate tier name, defaults to enterprise logic
        # This documents current behavior
        with pytest.raises(DependencyError):
            # Invalid tier will try enterprise sources and fail
            resolve("invalid", tmp_path)
            
    @patch('subprocess.run')
    def test_resolve_with_empty_frontend_dir(self, mock_run):
        """Test resolve with empty Path."""
        mock_run.return_value = Mock(returncode=0)
        
        # Should succeed for community (doesn't need vendored path)
        source = resolve("community", Path(""))
        assert source.source_type == SourceType.REGISTRY


# Pytest fixtures
@pytest.fixture
def mock_registry_available():
    """Fixture to mock registry as available."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0)
        yield mock_run


@pytest.fixture
def mock_registry_unavailable():
    """Fixture to mock registry as unavailable."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=1)
        yield mock_run


@pytest.fixture
def vendored_available(tmp_path):
    """Fixture creating available vendored packages."""
    vendored_path = tmp_path / "vendored"
    vendored_path.mkdir()
    manifest = vendored_path / "manifest.json"
    manifest.write_text('{"packages": []}')
    return tmp_path


class TestFixtures:
    """Test that fixtures work correctly."""
    
    def test_registry_available_fixture(self, mock_registry_available):
        """Test mock_registry_available fixture."""
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
        )
        assert source.check_availability() is True
        
    def test_registry_unavailable_fixture(self, mock_registry_unavailable):
        """Test mock_registry_unavailable fixture."""
        source = DependencySource(
            source_type=SourceType.REGISTRY,
            priority=1,
            url="https://registry.npmjs.org",
        )
        assert source.check_availability() is False
        
    def test_vendored_available_fixture(self, vendored_available):
        """Test vendored_available fixture."""
        source = DependencySource(
            source_type=SourceType.VENDORED,
            priority=2,
            local_path=vendored_available / "vendored",
        )
        assert source.check_availability() is True
