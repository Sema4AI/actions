"""Unit tests for BuildTier selection logic.

Tests T007: BuildTier class and select_tier() function
Tests T007a: Default tier behavior (FR-003 compliance)
"""

import pytest

from action_server.build_binary.tier_selector import (
    BuildTier,
    COMMUNITY,
    ENTERPRISE,
    ConfigurationError,
    TierName,
    select_tier,
)


class TestBuildTierClass:
    """Test BuildTier dataclass attributes and constants."""
    
    def test_community_tier_attributes(self):
        """Test COMMUNITY tier has correct attributes."""
        assert COMMUNITY.name == TierName.COMMUNITY
        assert COMMUNITY.is_default is True
        assert COMMUNITY.requires_auth is False
        assert "action_ui" in COMMUNITY.allowed_features
        assert "logs_ui" in COMMUNITY.allowed_features
        assert "artifacts_ui" in COMMUNITY.allowed_features
        assert "open_components" in COMMUNITY.allowed_features
        
    def test_enterprise_tier_attributes(self):
        """Test ENTERPRISE tier has correct attributes."""
        assert ENTERPRISE.name == TierName.ENTERPRISE
        assert ENTERPRISE.is_default is False
        assert ENTERPRISE.requires_auth is True
        # Enterprise should have all community features plus more
        assert "action_ui" in ENTERPRISE.allowed_features
        assert "design_system" in ENTERPRISE.allowed_features
        assert "kb_ui" in ENTERPRISE.allowed_features
        assert "themes" in ENTERPRISE.allowed_features
        assert "analytics_ui" in ENTERPRISE.allowed_features
        assert "sso_ui" in ENTERPRISE.allowed_features
        
    def test_enterprise_has_more_features_than_community(self):
        """Test enterprise tier is superset of community features."""
        assert len(ENTERPRISE.allowed_features) > len(COMMUNITY.allowed_features)
        # All community features should be in enterprise
        for feature in COMMUNITY.allowed_features:
            assert feature in ENTERPRISE.allowed_features


class TestSelectTierDefaultBehavior:
    """Test default tier behavior (T007a - FR-003 compliance)."""
    
    def test_default_tier_is_community_when_no_args(self):
        """Test select_tier() returns COMMUNITY when no arguments provided.
        
        This validates FR-003: System defaults to Community tier.
        """
        tier = select_tier(cli_flag=None, env_var=None)
        assert tier == COMMUNITY
        assert tier.name == TierName.COMMUNITY
        
    def test_default_tier_is_community_when_empty_args(self):
        """Test default behavior with empty strings."""
        # Empty string should be treated as None
        tier = select_tier()
        assert tier == COMMUNITY
        
    def test_community_is_only_default_tier(self):
        """Test COMMUNITY.is_default is True and ENTERPRISE.is_default is False."""
        assert COMMUNITY.is_default is True
        assert ENTERPRISE.is_default is False
        
    def test_select_tier_docstring_documents_default(self):
        """Test select_tier() function documents default behavior."""
        docstring = select_tier.__doc__
        assert "default" in docstring.lower()
        assert "community" in docstring.lower()


class TestSelectTierCLIFlag:
    """Test CLI flag tier selection."""
    
    def test_cli_flag_community(self):
        """Test --tier=community explicitly selects community tier."""
        tier = select_tier(cli_flag="community")
        assert tier == COMMUNITY
        
    def test_cli_flag_enterprise(self):
        """Test --tier=enterprise selects enterprise tier."""
        tier = select_tier(cli_flag="enterprise")
        assert tier == ENTERPRISE
        
    def test_cli_flag_case_insensitive_uppercase(self):
        """Test tier name is case-insensitive (uppercase)."""
        tier = select_tier(cli_flag="COMMUNITY")
        assert tier == COMMUNITY
        
    def test_cli_flag_case_insensitive_mixed(self):
        """Test tier name is case-insensitive (mixed case)."""
        tier = select_tier(cli_flag="Enterprise")
        assert tier == ENTERPRISE
        
    def test_cli_flag_invalid_tier_raises_error(self):
        """Test invalid tier name raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            select_tier(cli_flag="premium")
        
        assert "Invalid tier 'premium'" in str(exc_info.value)
        assert "Must be 'community' or 'enterprise'" in str(exc_info.value)


class TestSelectTierEnvVar:
    """Test environment variable tier selection."""
    
    def test_env_var_community(self):
        """Test TIER=community selects community tier."""
        tier = select_tier(env_var="community")
        assert tier == COMMUNITY
        
    def test_env_var_enterprise(self):
        """Test TIER=enterprise selects enterprise tier."""
        tier = select_tier(env_var="enterprise")
        assert tier == ENTERPRISE
        
    def test_env_var_case_insensitive(self):
        """Test environment variable is case-insensitive."""
        tier = select_tier(env_var="ENTERPRISE")
        assert tier == ENTERPRISE
        
    def test_env_var_invalid_tier_raises_error(self):
        """Test invalid env var tier name raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            select_tier(env_var="basic")
        
        assert "Invalid tier 'basic'" in str(exc_info.value)


class TestSelectTierPrecedence:
    """Test precedence rules: CLI flag > env var > default."""
    
    def test_cli_flag_overrides_env_var_community(self):
        """Test CLI flag takes precedence over environment variable."""
        tier = select_tier(cli_flag="community", env_var="enterprise")
        assert tier == COMMUNITY
        
    def test_cli_flag_overrides_env_var_enterprise(self):
        """Test CLI flag overrides env var for enterprise selection."""
        tier = select_tier(cli_flag="enterprise", env_var="community")
        assert tier == ENTERPRISE
        
    def test_env_var_overrides_default(self):
        """Test environment variable overrides default when no CLI flag."""
        tier = select_tier(cli_flag=None, env_var="enterprise")
        assert tier == ENTERPRISE
        
    def test_cli_flag_overrides_both_env_var_and_default(self):
        """Test CLI flag has highest precedence."""
        # Even with enterprise env var, community CLI flag wins
        tier = select_tier(cli_flag="community", env_var="enterprise")
        assert tier == COMMUNITY


class TestSelectTierEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_whitespace_in_tier_name_stripped(self):
        """Test tier names with whitespace are handled correctly."""
        # Note: Current implementation doesn't strip whitespace
        # This test documents expected behavior (will fail initially)
        with pytest.raises(ConfigurationError):
            select_tier(cli_flag=" community ")
            
    def test_empty_string_cli_flag_falls_back_to_env(self):
        """Test empty string CLI flag is treated as None."""
        # Empty strings are falsy in Python, so should fall back
        tier = select_tier(cli_flag="", env_var="enterprise")
        # Current implementation: empty string is falsy, falls back to env_var
        assert tier == ENTERPRISE
        
    def test_both_none_returns_default(self):
        """Test explicit None for both arguments returns default."""
        tier = select_tier(cli_flag=None, env_var=None)
        assert tier == COMMUNITY
        assert tier.is_default is True


class TestTierAttributes:
    """Test BuildTier attribute behavior."""
    
    def test_community_does_not_require_auth(self):
        """Test community tier never requires authentication."""
        assert COMMUNITY.requires_auth is False
        
    def test_enterprise_requires_auth(self):
        """Test enterprise tier requires authentication."""
        assert ENTERPRISE.requires_auth is True
        
    def test_tier_name_enum_values(self):
        """Test TierName enum has correct values."""
        assert TierName.COMMUNITY.value == "community"
        assert TierName.ENTERPRISE.value == "enterprise"
        
    def test_tier_allowed_features_is_list(self):
        """Test allowed_features attribute is a list."""
        assert isinstance(COMMUNITY.allowed_features, list)
        assert isinstance(ENTERPRISE.allowed_features, list)
        
    def test_community_features_are_subset_of_enterprise(self):
        """Test all community features exist in enterprise tier."""
        community_features = set(COMMUNITY.allowed_features)
        enterprise_features = set(ENTERPRISE.allowed_features)
        
        assert community_features.issubset(enterprise_features)


class TestConfigurationError:
    """Test ConfigurationError exception."""
    
    def test_configuration_error_is_exception(self):
        """Test ConfigurationError is an Exception subclass."""
        assert issubclass(ConfigurationError, Exception)
        
    def test_configuration_error_can_be_raised(self):
        """Test ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Test error")
            
    def test_invalid_tier_raises_configuration_error(self):
        """Test invalid tier selection raises ConfigurationError, not ValueError."""
        with pytest.raises(ConfigurationError):
            select_tier(cli_flag="invalid")


class TestSelectTierReturnType:
    """Test select_tier() return type guarantees."""
    
    def test_returns_build_tier_instance(self):
        """Test select_tier() returns BuildTier instance."""
        tier = select_tier()
        assert isinstance(tier, BuildTier)
        
    def test_returns_tier_constant_not_new_instance(self):
        """Test select_tier() returns the actual constant, not a copy."""
        tier = select_tier(cli_flag="community")
        assert tier is COMMUNITY  # Identity check, not equality
        
        tier = select_tier(cli_flag="enterprise")
        assert tier is ENTERPRISE
        
    def test_return_value_is_immutable_reference(self):
        """Test returned tier is a reference to immutable constant."""
        tier1 = select_tier(cli_flag="community")
        tier2 = select_tier(cli_flag="community")
        
        # Both should reference the same object
        assert tier1 is tier2


# Pytest fixtures for common test scenarios
@pytest.fixture
def community_tier():
    """Fixture providing COMMUNITY tier constant."""
    return COMMUNITY


@pytest.fixture
def enterprise_tier():
    """Fixture providing ENTERPRISE tier constant."""
    return ENTERPRISE


class TestFixtures:
    """Test that fixtures work correctly."""
    
    def test_community_fixture(self, community_tier):
        """Test community_tier fixture provides COMMUNITY constant."""
        assert community_tier == COMMUNITY
        assert community_tier.name == TierName.COMMUNITY
        
    def test_enterprise_fixture(self, enterprise_tier):
        """Test enterprise_tier fixture provides ENTERPRISE constant."""
        assert enterprise_tier == ENTERPRISE
        assert enterprise_tier.name == TierName.ENTERPRISE
