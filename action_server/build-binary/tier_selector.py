"""Build tier selection logic for dual-tier build system."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TierName(str, Enum):
    """Available build tiers."""
    
    COMMUNITY = "community"
    ENTERPRISE = "enterprise"


@dataclass
class BuildTier:
    """Represents a build tier with its properties."""
    
    name: TierName
    is_default: bool
    requires_auth: bool
    allowed_features: list[str]


class ConfigurationError(Exception):
    """Raised when tier configuration is invalid."""
    
    pass


# Define tier constants
COMMUNITY = BuildTier(
    name=TierName.COMMUNITY,
    is_default=True,
    requires_auth=False,
    allowed_features=[
        "action_ui",
        "logs_ui",
        "artifacts_ui",
        "open_components",
    ],
)

ENTERPRISE = BuildTier(
    name=TierName.ENTERPRISE,
    is_default=False,
    requires_auth=True,
    allowed_features=[
        "action_ui",
        "logs_ui",
        "artifacts_ui",
        "open_components",
        "design_system",
        "kb_ui",
        "themes",
        "analytics_ui",
        "sso_ui",
    ],
)


def select_tier(
    cli_flag: Optional[str] = None, env_var: Optional[str] = None
) -> BuildTier:
    """Select build tier based on CLI flag or environment variable.
    
    Precedence: CLI flag > environment variable > default (community)
    
    Args:
        cli_flag: Tier name from CLI argument (e.g., --tier=enterprise)
        env_var: Tier name from TIER environment variable
        
    Returns:
        BuildTier instance for the selected tier
        
    Raises:
        ConfigurationError: If tier name is invalid
    """
    # Determine tier name based on precedence
    tier_name = cli_flag or env_var
    
    # Default to community if no tier specified
    if tier_name is None:
        return COMMUNITY
    
    # Normalize tier name
    tier_name = tier_name.lower()
    
    # Validate and return tier
    if tier_name == TierName.COMMUNITY.value:
        return COMMUNITY
    elif tier_name == TierName.ENTERPRISE.value:
        return ENTERPRISE
    else:
        raise ConfigurationError(
            f"Invalid tier '{tier_name}'. Must be 'community' or 'enterprise'"
        )
