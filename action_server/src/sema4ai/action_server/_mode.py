"""
Operating mode configuration for the Action Server.

Supports two modes:
- STANDARD: SQLite-based storage, embedded scheduler, single-process
- DISTRIBUTED: Redis-backed job queue, distributed workers, horizontal scaling

Mode is automatically determined by Redis availability:
- If redis_url is provided and Redis is reachable → DISTRIBUTED mode
- If redis_url is provided but Redis is unreachable → Falls back to STANDARD with warning
- If no redis_url → STANDARD mode
"""

import logging
from enum import Enum
from typing import Optional

from termcolor import colored

log = logging.getLogger(__name__)


class OperatingMode(Enum):
    """Operating mode for the Action Server."""

    STANDARD = "standard"
    DISTRIBUTED = "distributed"

    # Legacy alias for backwards compatibility
    CONTROL_ROOM_LITE = "distributed"


class ModeConfig:
    """
    Runtime configuration based on operating mode.

    Standard mode: SQLite storage, embedded scheduler
    Distributed mode: Redis queue, distributed workers
    """

    def __init__(
        self,
        mode: OperatingMode = OperatingMode.STANDARD,
        redis_url: Optional[str] = None,
        redis_password: Optional[str] = None,
    ):
        """
        Initialize mode configuration.

        Args:
            mode: Operating mode
            redis_url: Redis URL (required for DISTRIBUTED mode)
            redis_password: Redis password (optional)
        """
        self._mode = mode
        self._redis_url = redis_url
        self._redis_password = redis_password
        self._redis_client = None

        if mode == OperatingMode.DISTRIBUTED:
            if not redis_url:
                raise ValueError(
                    "--redis-url is required for distributed mode"
                )
            self._validate_redis_available()

    def _validate_redis_available(self) -> None:
        """Check that the redis package is available."""
        try:
            import redis  # noqa: F401
        except ImportError:
            raise ImportError(
                "Redis package required for distributed mode. "
                "Install with: pip install sema4ai-action-server[distributed]"
            )

    @property
    def mode(self) -> OperatingMode:
        """Get the operating mode."""
        return self._mode

    @property
    def is_standard(self) -> bool:
        """Check if running in standard mode."""
        return self._mode == OperatingMode.STANDARD

    @property
    def is_distributed(self) -> bool:
        """Check if running in distributed mode."""
        return self._mode == OperatingMode.DISTRIBUTED

    @property
    def is_control_room_lite(self) -> bool:
        """Legacy alias for is_distributed."""
        return self.is_distributed

    @property
    def use_redis_queue(self) -> bool:
        """Check if Redis job queue should be used."""
        return self.is_distributed

    @property
    def use_redis_pubsub(self) -> bool:
        """Check if Redis pub/sub should be used for events."""
        return self.is_distributed

    @property
    def redis_url(self) -> Optional[str]:
        """Get the Redis URL."""
        return self._redis_url

    @property
    def redis_password(self) -> Optional[str]:
        """Get the Redis password."""
        return self._redis_password

    async def get_redis_client(self):
        """
        Get an async Redis client.

        Returns a cached client instance.
        """
        if not self.is_control_room_lite:
            raise RuntimeError("Redis not available in standard mode")

        if self._redis_client is None:
            import redis.asyncio as aioredis

            self._redis_client = aioredis.from_url(
                self._redis_url,
                password=self._redis_password,
                encoding="utf-8",
                decode_responses=True,
            )

        return self._redis_client

    async def close_redis_client(self) -> None:
        """Close the Redis client connection."""
        if self._redis_client is not None:
            await self._redis_client.close()
            self._redis_client = None

    async def test_redis_connection(self) -> tuple[bool, str]:
        """
        Test the Redis connection.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_control_room_lite:
            return False, "Not in control-room-lite mode"

        try:
            client = await self.get_redis_client()
            await client.ping()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)


# Global mode configuration
_global_mode_config: Optional[ModeConfig] = None


def get_mode_config() -> ModeConfig:
    """
    Get the global mode configuration.

    Returns a default standard mode config if not initialized.
    """
    global _global_mode_config
    if _global_mode_config is None:
        _global_mode_config = ModeConfig()
    return _global_mode_config


def set_mode_config(config: ModeConfig) -> None:
    """Set the global mode configuration."""
    global _global_mode_config
    _global_mode_config = config


def _test_redis_connection(redis_url: str, redis_password: Optional[str]) -> bool:
    """
    Test if Redis is reachable.

    Args:
        redis_url: Redis URL to test
        redis_password: Redis password

    Returns:
        True if Redis is reachable, False otherwise
    """
    try:
        import redis

        # Parse URL and create client
        client = redis.from_url(
            redis_url,
            password=redis_password,
            socket_connect_timeout=5,  # 5 second timeout
        )
        # Try to ping Redis
        client.ping()
        client.close()
        return True
    except ImportError:
        log.warning(
            "Redis package not installed. "
            "Install with: pip install sema4ai-action-server[distributed]"
        )
        return False
    except Exception as e:
        log.warning(f"Redis at {redis_url} unreachable: {e}")
        return False


def initialize_mode(
    redis_url: Optional[str] = None,
    redis_password: Optional[str] = None,
    # Legacy parameter for backwards compatibility
    control_room_lite: bool = False,
) -> ModeConfig:
    """
    Initialize the operating mode.

    Mode is automatically determined by Redis availability:
    - If redis_url is provided and Redis is reachable → DISTRIBUTED mode
    - If redis_url is provided but Redis is unreachable → Falls back to STANDARD with warning
    - If no redis_url → STANDARD mode

    Args:
        redis_url: Redis URL for distributed mode
        redis_password: Redis password
        control_room_lite: Legacy parameter, ignored (mode auto-detected from redis_url)

    Returns:
        The initialized ModeConfig
    """
    # Determine mode based on Redis URL availability and connectivity
    if redis_url:
        if _test_redis_connection(redis_url, redis_password):
            mode = OperatingMode.DISTRIBUTED
            log.info(
                colored(
                    f"Operating mode: {mode.value} (Redis: {redis_url})",
                    "green",
                    attrs=["bold"],
                )
            )
        else:
            # Graceful fallback to standard mode
            mode = OperatingMode.STANDARD
            log.warning(
                colored(
                    f"Redis at {redis_url} unreachable, falling back to standard mode",
                    "yellow",
                )
            )
            # Clear redis_url since we're not using it
            redis_url = None
    else:
        mode = OperatingMode.STANDARD
        log.info(f"Operating mode: {mode.value}")

    config = ModeConfig(
        mode=mode,
        redis_url=redis_url,
        redis_password=redis_password,
    )

    set_mode_config(config)

    return config
