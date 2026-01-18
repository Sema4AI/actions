"""
Community tunnel providers for --expose functionality.

This module provides open-source alternatives for exposing the action server
to the internet. It supports multiple tunnel providers with automatic fallback:

1. localhost.run - SSH-based, zero dependencies, HTTPS included
2. bore - Rust binary, simple TCP tunneling
3. Cloudflare Tunnel - Production-grade, requires setup

Usage:
    tunnel = TunnelManager()
    url = await tunnel.start(port=8080)
    # ... use url ...
    await tunnel.stop()
"""

import asyncio
import logging
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

log = logging.getLogger(__name__)


class TunnelProvider(str, Enum):
    """Available tunnel providers."""

    LOCALHOST_RUN = "localhost.run"
    BORE = "bore"
    CLOUDFLARE = "cloudflare"
    AUTO = "auto"  # Auto-detect best available


@dataclass
class TunnelInfo:
    """Information about an active tunnel."""

    provider: TunnelProvider
    public_url: str
    local_port: int
    process: Optional[subprocess.Popen] = None
    task: Optional[asyncio.Task] = None


class BaseTunnelProvider(ABC):
    """Base class for tunnel providers."""

    @property
    @abstractmethod
    def name(self) -> TunnelProvider:
        """Return the provider name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the system."""
        pass

    @abstractmethod
    async def start(self, port: int) -> TunnelInfo:
        """Start the tunnel and return the public URL."""
        pass

    @abstractmethod
    async def stop(self, tunnel: TunnelInfo) -> None:
        """Stop the tunnel."""
        pass


class LocalhostRunProvider(BaseTunnelProvider):
    """
    localhost.run tunnel provider.

    Uses SSH to create a tunnel - no additional software needed.
    Provides HTTPS URLs automatically.

    Usage: ssh -R 80:localhost:{port} nokey@localhost.run
    """

    @property
    def name(self) -> TunnelProvider:
        return TunnelProvider.LOCALHOST_RUN

    def is_available(self) -> bool:
        """Check if SSH is available."""
        return shutil.which("ssh") is not None

    async def start(self, port: int) -> TunnelInfo:
        """Start localhost.run tunnel via SSH."""
        log.info("Starting localhost.run tunnel...")

        process = subprocess.Popen(
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ServerAliveInterval=30",
                "-o",
                "ServerAliveCountMax=3",
                "-R",
                f"80:localhost:{port}",
                "nokey@localhost.run",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Parse output to get the URL
        public_url = await self._wait_for_url(process)

        return TunnelInfo(
            provider=self.name,
            public_url=public_url,
            local_port=port,
            process=process,
        )

    async def _wait_for_url(
        self, process: subprocess.Popen, timeout: float = 30.0
    ) -> str:
        """Wait for localhost.run to output the public URL."""
        import asyncio

        url_pattern = re.compile(
            r"https?://[a-zA-Z0-9-]+\.lhr\.life[^\s]*|https?://[a-zA-Z0-9]+\.localhost\.run[^\s]*"
        )

        start_time = asyncio.get_event_loop().time()

        while True:
            if process.poll() is not None:
                raise RuntimeError(
                    f"localhost.run process exited with code {process.returncode}"
                )

            if asyncio.get_event_loop().time() - start_time > timeout:
                process.terminate()
                raise TimeoutError("Timed out waiting for localhost.run URL")

            # Read line with timeout
            line = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )

            if line:
                log.debug(f"localhost.run: {line.strip()}")
                match = url_pattern.search(line)
                if match:
                    return match.group(0).rstrip(",").rstrip()

            await asyncio.sleep(0.1)

    async def stop(self, tunnel: TunnelInfo) -> None:
        """Stop the SSH tunnel."""
        if tunnel.process:
            tunnel.process.terminate()
            try:
                tunnel.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.process.kill()


class BoreProvider(BaseTunnelProvider):
    """
    bore tunnel provider.

    Uses the bore binary to create TCP tunnels.
    Simple and lightweight (~500KB Rust binary).

    Note: bore.pub doesn't provide HTTPS, just HTTP over the tunnel port.

    Usage: bore local {port} --to bore.pub
    """

    def __init__(self, server: str = "bore.pub"):
        self.server = server

    @property
    def name(self) -> TunnelProvider:
        return TunnelProvider.BORE

    def is_available(self) -> bool:
        """Check if bore binary is available."""
        return shutil.which("bore") is not None

    async def start(self, port: int) -> TunnelInfo:
        """Start bore tunnel."""
        log.info(f"Starting bore tunnel to {self.server}...")

        process = subprocess.Popen(
            ["bore", "local", str(port), "--to", self.server],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Parse output to get the URL
        public_url = await self._wait_for_url(process)

        return TunnelInfo(
            provider=self.name,
            public_url=public_url,
            local_port=port,
            process=process,
        )

    async def _wait_for_url(
        self, process: subprocess.Popen, timeout: float = 30.0
    ) -> str:
        """Wait for bore to output the public URL."""
        # bore outputs: "listening at bore.pub:12345"
        url_pattern = re.compile(rf"{re.escape(self.server)}:(\d+)")

        start_time = asyncio.get_event_loop().time()

        while True:
            if process.poll() is not None:
                raise RuntimeError(
                    f"bore process exited with code {process.returncode}"
                )

            if asyncio.get_event_loop().time() - start_time > timeout:
                process.terminate()
                raise TimeoutError("Timed out waiting for bore URL")

            line = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )

            if line:
                log.debug(f"bore: {line.strip()}")
                match = url_pattern.search(line)
                if match:
                    return f"http://{self.server}:{match.group(1)}"

            await asyncio.sleep(0.1)

    async def stop(self, tunnel: TunnelInfo) -> None:
        """Stop the bore tunnel."""
        if tunnel.process:
            tunnel.process.terminate()
            try:
                tunnel.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.process.kill()


class CloudflareProvider(BaseTunnelProvider):
    """
    Cloudflare Tunnel provider.

    Uses cloudflared to create production-grade tunnels.
    Requires either:
    1. Pre-configured tunnel (CLOUDFLARE_TUNNEL_TOKEN env var)
    2. Quick tunnel mode (no config, temporary URL)

    Usage: cloudflared tunnel --url http://localhost:{port}
    """

    @property
    def name(self) -> TunnelProvider:
        return TunnelProvider.CLOUDFLARE

    def is_available(self) -> bool:
        """Check if cloudflared is available."""
        return shutil.which("cloudflared") is not None

    async def start(self, port: int) -> TunnelInfo:
        """Start Cloudflare tunnel."""
        log.info("Starting Cloudflare tunnel...")

        # Check for pre-configured tunnel token
        tunnel_token = os.environ.get("CLOUDFLARE_TUNNEL_TOKEN")

        if tunnel_token:
            # Use pre-configured tunnel
            process = subprocess.Popen(
                ["cloudflared", "tunnel", "run", "--token", tunnel_token],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            # For pre-configured tunnels, the URL is known from config
            # User should set CLOUDFLARE_TUNNEL_URL env var
            public_url = os.environ.get("CLOUDFLARE_TUNNEL_URL", "")
            if not public_url:
                log.warning("CLOUDFLARE_TUNNEL_URL not set, tunnel URL unknown")
        else:
            # Use quick tunnel (temporary URL)
            process = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            public_url = await self._wait_for_url(process)

        return TunnelInfo(
            provider=self.name,
            public_url=public_url,
            local_port=port,
            process=process,
        )

    async def _wait_for_url(
        self, process: subprocess.Popen, timeout: float = 60.0
    ) -> str:
        """Wait for cloudflared to output the public URL."""
        # cloudflared outputs URLs like: https://random-words.trycloudflare.com
        url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

        start_time = asyncio.get_event_loop().time()

        while True:
            if process.poll() is not None:
                raise RuntimeError(
                    f"cloudflared process exited with code {process.returncode}"
                )

            if asyncio.get_event_loop().time() - start_time > timeout:
                process.terminate()
                raise TimeoutError("Timed out waiting for Cloudflare URL")

            line = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )

            if line:
                log.debug(f"cloudflared: {line.strip()}")
                match = url_pattern.search(line)
                if match:
                    return match.group(0)

            await asyncio.sleep(0.1)

    async def stop(self, tunnel: TunnelInfo) -> None:
        """Stop the Cloudflare tunnel."""
        if tunnel.process:
            tunnel.process.terminate()
            try:
                tunnel.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.process.kill()


class TunnelManager:
    """
    Manages tunnel lifecycle with automatic provider selection and fallback.

    Usage:
        manager = TunnelManager()
        tunnel = await manager.start(port=8080)
        print(f"Public URL: {tunnel.public_url}")
        # ... use the tunnel ...
        await manager.stop()
    """

    def __init__(self, preferred_provider: TunnelProvider = TunnelProvider.AUTO):
        self.preferred_provider = preferred_provider
        self.active_tunnel: Optional[TunnelInfo] = None
        self._providers = [
            LocalhostRunProvider(),
            BoreProvider(),
            CloudflareProvider(),
        ]

    def get_available_providers(self) -> list[BaseTunnelProvider]:
        """Return list of available providers on this system."""
        return [p for p in self._providers if p.is_available()]

    def _get_provider(
        self, provider_type: TunnelProvider
    ) -> Optional[BaseTunnelProvider]:
        """Get a specific provider by type."""
        for p in self._providers:
            if p.name == provider_type:
                return p
        return None

    async def start(
        self, port: int, provider: Optional[TunnelProvider] = None
    ) -> TunnelInfo:
        """
        Start a tunnel to expose the given port.

        Args:
            port: Local port to expose
            provider: Specific provider to use, or None for auto-detection

        Returns:
            TunnelInfo with the public URL and connection details

        Raises:
            RuntimeError: If no tunnel provider is available or all fail
        """
        provider_to_use = provider or self.preferred_provider

        if provider_to_use != TunnelProvider.AUTO:
            # Use specific provider
            p = self._get_provider(provider_to_use)
            if p is None or not p.is_available():
                raise RuntimeError(f"Provider {provider_to_use.value} is not available")

            self.active_tunnel = await p.start(port)
            return self.active_tunnel

        # Auto-detect: try providers in order
        available = self.get_available_providers()
        if not available:
            raise RuntimeError(
                "No tunnel providers available. Install one of:\n"
                "  - SSH (for localhost.run) - usually pre-installed\n"
                "  - bore: https://github.com/ekzhang/bore\n"
                "  - cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            )

        errors = []
        for provider in available:
            try:
                log.info(f"Trying {provider.name.value}...")
                self.active_tunnel = await provider.start(port)
                log.info(f"Successfully started tunnel with {provider.name.value}")
                return self.active_tunnel
            except Exception as e:
                log.warning(f"Failed to start {provider.name.value}: {e}")
                errors.append((provider.name.value, str(e)))

        error_msg = "\n".join([f"  - {name}: {err}" for name, err in errors])
        raise RuntimeError(f"All tunnel providers failed:\n{error_msg}")

    async def stop(self) -> None:
        """Stop the active tunnel."""
        if self.active_tunnel:
            provider = self._get_provider(self.active_tunnel.provider)
            if provider:
                await provider.stop(self.active_tunnel)
            self.active_tunnel = None

    @property
    def public_url(self) -> Optional[str]:
        """Get the public URL of the active tunnel."""
        return self.active_tunnel.public_url if self.active_tunnel else None

    @property
    def is_active(self) -> bool:
        """Check if a tunnel is currently active."""
        return self.active_tunnel is not None


# Convenience function for simple usage
async def expose_port(
    port: int, provider: TunnelProvider = TunnelProvider.AUTO
) -> TunnelInfo:
    """
    Simple function to expose a port.

    Args:
        port: Local port to expose
        provider: Tunnel provider to use (default: auto-detect)

    Returns:
        TunnelInfo with connection details
    """
    manager = TunnelManager(preferred_provider=provider)
    return await manager.start(port)
