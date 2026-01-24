"""
Operating mode configuration for the Action Server.

Supports two modes:
- STANDARD: SQLite-based storage, embedded scheduler, single-process
- CONTROL_ROOM_LITE: Redis-backed job queue, distributed workers, horizontal scaling
"""

import logging
from enum import Enum
from typing import Optional

log = logging.getLogger(__name__)


class OperatingMode(Enum):
    """Operating mode for the Action Server."""

    STANDARD = "standard"
    CONTROL_ROOM_LITE = "control-room-lite"


class ModeConfig:
    """
    Runtime configuration based on operating mode.

    Standard mode: SQLite storage, embedded scheduler
    Control Room Lite: Redis queue, distributed workers
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
            redis_url: Redis URL (required for CONTROL_ROOM_LITE)
            redis_password: Redis password (optional)
        """
        self._mode = mode
        self._redis_url = redis_url
        self._redis_password = redis_password
        self._redis_client = None

        if mode == OperatingMode.CONTROL_ROOM_LITE:
            if not redis_url:
                raise ValueError(
                    "--redis-url is required for control-room-lite mode"
                )
            self._validate_redis_available()

    def _validate_redis_available(self) -> None:
        """Check that the redis package is available."""
        try:
            import redis  # noqa: F401
        except ImportError:
            raise ImportError(
                "Redis package required for control-room-lite mode. "
                "Install with: pip install sema4ai-action-server[control-room-lite]"
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
    def is_control_room_lite(self) -> bool:
        """Check if running in control-room-lite mode."""
        return self._mode == OperatingMode.CONTROL_ROOM_LITE

    @property
    def use_redis_queue(self) -> bool:
        """Check if Redis job queue should be used."""
        return self.is_control_room_lite

    @property
    def use_redis_pubsub(self) -> bool:
        """Check if Redis pub/sub should be used for events."""
        return self.is_control_room_lite

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


def initialize_mode(
    control_room_lite: bool = False,
    redis_url: Optional[str] = None,
    redis_password: Optional[str] = None,
) -> ModeConfig:
    """
    Initialize the operating mode.

    Args:
        control_room_lite: Enable control-room-lite mode
        redis_url: Redis URL for control-room-lite mode
        redis_password: Redis password

    Returns:
        The initialized ModeConfig
    """
    mode = (
        OperatingMode.CONTROL_ROOM_LITE
        if control_room_lite
        else OperatingMode.STANDARD
    )

    config = ModeConfig(
        mode=mode,
        redis_url=redis_url,
        redis_password=redis_password,
    )

    set_mode_config(config)

    log.info(f"Operating mode: {mode.value}")
    if config.is_control_room_lite:
        log.info(f"Redis URL: {redis_url}")

    return config
