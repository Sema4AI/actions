"""Package dependency resolution for dual-tier build system."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
import socket
import subprocess
import time


class SourceType(str, Enum):
    """Available dependency sources."""
    
    REGISTRY = "registry"
    VENDORED = "vendored"
    CDN = "cdn"


class DependencyError(Exception):
    """Raised when all dependency sources fail."""
    
    pass


@dataclass
class DependencySource:
    """Represents a dependency source with availability checking."""
    
    source_type: SourceType
    priority: int
    url: Optional[str] = None
    local_path: Optional[Path] = None
    requires_auth: bool = False
    
    def check_availability(self, timeout: int = 5) -> bool:
        """Check if this dependency source is available.
        
        Args:
            timeout: Network timeout in seconds
            
        Returns:
            True if source is available, False otherwise
        """
        if self.source_type == SourceType.REGISTRY:
            # Check npm registry availability with timeout
            try:
                result = subprocess.run(
                    ["npm", "ping", "--registry", self.url or "https://registry.npmjs.org"],
                    capture_output=True,
                    timeout=timeout,
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
                
        elif self.source_type == SourceType.VENDORED:
            # Check if vendored manifest exists
            if self.local_path:
                manifest_path = self.local_path / "manifest.json"
                return manifest_path.exists()
            return False
            
        elif self.source_type == SourceType.CDN:
            # Check CDN availability (simple URL check)
            if self.url:
                try:
                    # Parse hostname from URL
                    from urllib.parse import urlparse
                    parsed = urlparse(self.url)
                    host = parsed.hostname
                    if host:
                        socket.create_connection((host, 443), timeout=timeout)
                        return True
                except (socket.timeout, socket.error, OSError):
                    return False
            return False
            
        return False


def resolve(tier_name: str, frontend_dir: Path) -> DependencySource:
    """Resolve dependency source based on tier and availability.
    
    Community tier: registry only
    Enterprise tier: registry → vendored → cdn (fallback order)
    
    Args:
        tier_name: Build tier ("community" or "enterprise")
        frontend_dir: Path to frontend directory
        
    Returns:
        Available DependencySource
        
    Raises:
        DependencyError: If no sources are available
    """
    if tier_name == "community":
        # Community tier: public registry only
        sources = [
            DependencySource(
                source_type=SourceType.REGISTRY,
                priority=1,
                url="https://registry.npmjs.org",
                requires_auth=False,
            )
        ]
    else:
        # Enterprise tier: registry → vendored → cdn
        sources = [
            DependencySource(
                source_type=SourceType.REGISTRY,
                priority=1,
                url="https://npm.pkg.github.com",
                requires_auth=True,
            ),
            DependencySource(
                source_type=SourceType.VENDORED,
                priority=2,
                local_path=frontend_dir / "vendored",
                requires_auth=False,
            ),
            DependencySource(
                source_type=SourceType.CDN,
                priority=3,
                url="https://cdn.sema4ai.com",  # Example CDN
                requires_auth=False,
            ),
        ]
    
    # Try sources in priority order
    for source in sorted(sources, key=lambda s: s.priority):
        if source.check_availability():
            return source
    
    # All sources failed
    raise DependencyError(
        f"No dependency sources available for tier '{tier_name}'. "
        f"Tried: {', '.join(s.source_type.value for s in sources)}"
    )
