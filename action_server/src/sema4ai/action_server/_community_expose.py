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
import platform
import re
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Bore version to download
BORE_VERSION = "0.5.2"

# Cloudflared version to download
CLOUDFLARED_VERSION = "2024.12.2"


def get_default_bore_location() -> Path:
    """Get the default location for the bore binary.

    Downloads to package bin/ directory (same location as RCC).
    """
    CURDIR = Path(__file__).parent.absolute()
    if sys.platform == "win32":
        bore_path = CURDIR / "bin" / f"bore-{BORE_VERSION}.exe"
    else:
        bore_path = CURDIR / "bin" / f"bore-{BORE_VERSION}"
    return bore_path


def download_bore(target: Optional[str] = None, force: bool = False) -> Path:
    """
    Downloads bore binary if not available.

    Bore releases: https://github.com/ekzhang/bore/releases
    """
    if target:
        bore_path = Path(target)
    else:
        bore_path = get_default_bore_location()

    if not force and bore_path.exists():
        return bore_path

    log.info(f"bore not available at: {bore_path}. Downloading.")
    bore_path.parent.mkdir(parents=True, exist_ok=True)

    machine = platform.machine().lower()

    # Map platform to bore release asset names
    # Assets: bore-v0.5.2-x86_64-unknown-linux-musl.tar.gz
    #         bore-v0.5.2-x86_64-apple-darwin.tar.gz
    #         bore-v0.5.2-aarch64-apple-darwin.tar.gz
    #         bore-v0.5.2-x86_64-pc-windows-msvc.zip
    if sys.platform == "win32":
        asset_name = f"bore-v{BORE_VERSION}-x86_64-pc-windows-msvc.zip"
        is_zip = True
    elif sys.platform == "darwin":
        if machine in ("arm64", "aarch64"):
            asset_name = f"bore-v{BORE_VERSION}-aarch64-apple-darwin.tar.gz"
        else:
            asset_name = f"bore-v{BORE_VERSION}-x86_64-apple-darwin.tar.gz"
        is_zip = False
    else:  # Linux
        asset_name = f"bore-v{BORE_VERSION}-x86_64-unknown-linux-musl.tar.gz"
        is_zip = False

    bore_url = f"https://github.com/ekzhang/bore/releases/download/v{BORE_VERSION}/{asset_name}"

    try:
        import sema4ai_http
        from sema4ai.common.system_mutex import timed_acquire_mutex

        timeout = 120.0
        with timed_acquire_mutex(
            "action_server_bore_download", timeout=timeout, raise_error_on_timeout=True
        ):
            if not force and bore_path.exists():
                return bore_path

            # Download to temp file
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                archive_path = Path(tmpdir) / asset_name

                log.info(f"Downloading bore from {bore_url}")
                status = sema4ai_http.download_with_resume(
                    bore_url,
                    archive_path,
                    make_executable=False,
                    overwrite_existing=True,
                )

                if status.status in (
                    sema4ai_http.DownloadStatus.HTTP_ERROR,
                    sema4ai_http.DownloadStatus.PARTIAL,
                ):
                    raise RuntimeError(f"Failed to download bore: {status.status}")

                # Extract the binary
                if is_zip:
                    import zipfile

                    with zipfile.ZipFile(archive_path, "r") as zf:
                        # Find bore executable in archive
                        for name in zf.namelist():
                            if name.endswith("bore.exe") or name == "bore":
                                zf.extract(name, tmpdir)
                                extracted = Path(tmpdir) / name
                                shutil.move(str(extracted), str(bore_path))
                                break
                else:
                    import tarfile

                    with tarfile.open(archive_path, "r:gz") as tf:
                        for member in tf.getmembers():
                            if member.name.endswith("bore") or member.name == "bore":
                                tf.extract(member, tmpdir)
                                extracted = Path(tmpdir) / member.name
                                shutil.move(str(extracted), str(bore_path))
                                break

                # Make executable on Unix
                if sys.platform != "win32":
                    os.chmod(bore_path, 0o755)

                log.info(f"bore downloaded successfully to {bore_path}")

    except ImportError:
        # Fallback without sema4ai_http - use urllib
        import tarfile
        import tempfile
        import urllib.request
        import zipfile

        log.info(f"Downloading bore from {bore_url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / asset_name
            urllib.request.urlretrieve(bore_url, archive_path)

            if is_zip:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    for name in zf.namelist():
                        if name.endswith("bore.exe") or name == "bore":
                            zf.extract(name, tmpdir)
                            extracted = Path(tmpdir) / name
                            shutil.move(str(extracted), str(bore_path))
                            break
            else:
                with tarfile.open(archive_path, "r:gz") as tf:
                    for member in tf.getmembers():
                        if member.name.endswith("bore") or member.name == "bore":
                            tf.extract(member, tmpdir)
                            extracted = Path(tmpdir) / member.name
                            shutil.move(str(extracted), str(bore_path))
                            break

            if sys.platform != "win32":
                os.chmod(bore_path, 0o755)

            log.info(f"bore downloaded successfully to {bore_path}")

    return bore_path


def get_default_cloudflared_location() -> Path:
    """Get the default location for the cloudflared binary.

    Downloads to package bin/ directory (same location as RCC).
    """
    CURDIR = Path(__file__).parent.absolute()
    if sys.platform == "win32":
        cf_path = CURDIR / "bin" / f"cloudflared-{CLOUDFLARED_VERSION}.exe"
    else:
        cf_path = CURDIR / "bin" / f"cloudflared-{CLOUDFLARED_VERSION}"
    return cf_path


def download_cloudflared(target: Optional[str] = None, force: bool = False) -> Path:
    """
    Downloads cloudflared binary if not available.

    Cloudflared releases: https://github.com/cloudflare/cloudflared/releases
    """
    if target:
        cf_path = Path(target)
    else:
        cf_path = get_default_cloudflared_location()

    if not force and cf_path.exists():
        return cf_path

    log.info(f"cloudflared not available at: {cf_path}. Downloading.")
    cf_path.parent.mkdir(parents=True, exist_ok=True)

    machine = platform.machine().lower()

    # Map platform to cloudflared release asset names
    # https://github.com/cloudflare/cloudflared/releases
    if sys.platform == "win32":
        asset_name = "cloudflared-windows-amd64.exe"
        direct_binary = True
    elif sys.platform == "darwin":
        if machine in ("arm64", "aarch64"):
            asset_name = "cloudflared-darwin-arm64.tgz"
        else:
            asset_name = "cloudflared-darwin-amd64.tgz"
        direct_binary = False
    else:  # Linux
        if machine in ("arm64", "aarch64"):
            asset_name = "cloudflared-linux-arm64"
        else:
            asset_name = "cloudflared-linux-amd64"
        direct_binary = True

    cf_url = f"https://github.com/cloudflare/cloudflared/releases/download/{CLOUDFLARED_VERSION}/{asset_name}"

    try:
        import sema4ai_http
        from sema4ai.common.system_mutex import timed_acquire_mutex

        timeout = 120.0
        with timed_acquire_mutex(
            "action_server_cloudflared_download",
            timeout=timeout,
            raise_error_on_timeout=True,
        ):
            if not force and cf_path.exists():
                return cf_path

            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                if direct_binary:
                    # Direct binary download
                    log.info(f"Downloading cloudflared from {cf_url}")
                    status = sema4ai_http.download_with_resume(
                        cf_url, cf_path, make_executable=True, overwrite_existing=True
                    )
                    if status.status in (
                        sema4ai_http.DownloadStatus.HTTP_ERROR,
                        sema4ai_http.DownloadStatus.PARTIAL,
                    ):
                        raise RuntimeError(
                            f"Failed to download cloudflared: {status.status}"
                        )
                else:
                    # Tarball download (macOS)
                    archive_path = Path(tmpdir) / asset_name
                    log.info(f"Downloading cloudflared from {cf_url}")
                    status = sema4ai_http.download_with_resume(
                        cf_url,
                        archive_path,
                        make_executable=False,
                        overwrite_existing=True,
                    )
                    if status.status in (
                        sema4ai_http.DownloadStatus.HTTP_ERROR,
                        sema4ai_http.DownloadStatus.PARTIAL,
                    ):
                        raise RuntimeError(
                            f"Failed to download cloudflared: {status.status}"
                        )

                    import tarfile

                    with tarfile.open(archive_path, "r:gz") as tf:
                        for member in tf.getmembers():
                            if "cloudflared" in member.name:
                                tf.extract(member, tmpdir)
                                extracted = Path(tmpdir) / member.name
                                shutil.move(str(extracted), str(cf_path))
                                break

                if sys.platform != "win32":
                    os.chmod(cf_path, 0o755)

                log.info(f"cloudflared downloaded successfully to {cf_path}")

    except ImportError:
        # Fallback without sema4ai_http
        import tempfile
        import urllib.request

        log.info(f"Downloading cloudflared from {cf_url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            if direct_binary:
                urllib.request.urlretrieve(cf_url, cf_path)
            else:
                import tarfile

                archive_path = Path(tmpdir) / asset_name
                urllib.request.urlretrieve(cf_url, archive_path)

                with tarfile.open(archive_path, "r:gz") as tf:
                    for member in tf.getmembers():
                        if "cloudflared" in member.name:
                            tf.extract(member, tmpdir)
                            extracted = Path(tmpdir) / member.name
                            shutil.move(str(extracted), str(cf_path))
                            break

            if sys.platform != "win32":
                os.chmod(cf_path, 0o755)

            log.info(f"cloudflared downloaded successfully to {cf_path}")

    return cf_path


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

        # localhost.run uses .lhr.life domain for tunnel URLs
        # Exclude admin.localhost.run which is their website
        url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.lhr\.life")

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
                None,
                process.stdout.readline,  # type: ignore[union-attr]
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
    Will auto-download if not available.

    Note: bore.pub doesn't provide HTTPS, just HTTP over the tunnel port.

    Usage: bore local {port} --to bore.pub
    """

    def __init__(self, server: str = "bore.pub"):
        self.server = server
        self._bore_path: Optional[str] = None

    @property
    def name(self) -> TunnelProvider:
        return TunnelProvider.BORE

    def _get_bore_path(self) -> Optional[str]:
        """Get bore binary path, downloading if necessary."""
        # First check if bore is in PATH
        system_bore = shutil.which("bore")
        if system_bore:
            return system_bore

        # Try to download bore
        try:
            bore_path = download_bore()
            if bore_path.exists():
                return str(bore_path)
        except Exception as e:
            log.warning(f"Failed to download bore: {e}")

        return None

    def is_available(self) -> bool:
        """Check if bore binary is available (will download if needed)."""
        self._bore_path = self._get_bore_path()
        return self._bore_path is not None

    async def start(self, port: int) -> TunnelInfo:
        """Start bore tunnel."""
        if not self._bore_path:
            self._bore_path = self._get_bore_path()
        if not self._bore_path:
            raise RuntimeError("bore binary not available")

        log.info(f"Starting bore tunnel to {self.server}...")

        process = subprocess.Popen(
            [self._bore_path, "local", str(port), "--to", self.server],
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
                None,
                process.stdout.readline,  # type: ignore[union-attr]
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
    Will auto-download cloudflared if not available.
    Requires either:
    1. Pre-configured tunnel (CLOUDFLARE_TUNNEL_TOKEN env var)
    2. Quick tunnel mode (no config, temporary URL)

    Usage: cloudflared tunnel --url http://localhost:{port}
    """

    def __init__(self):
        self._cloudflared_path: Optional[str] = None

    @property
    def name(self) -> TunnelProvider:
        return TunnelProvider.CLOUDFLARE

    def _get_cloudflared_path(self) -> Optional[str]:
        """Get cloudflared binary path, downloading if necessary."""
        # First check if cloudflared is in PATH
        system_cf = shutil.which("cloudflared")
        if system_cf:
            return system_cf

        # Try to download cloudflared
        try:
            cf_path = download_cloudflared()
            if cf_path.exists():
                return str(cf_path)
        except Exception as e:
            log.warning(f"Failed to download cloudflared: {e}")

        return None

    def is_available(self) -> bool:
        """Check if cloudflared is available (will download if needed)."""
        self._cloudflared_path = self._get_cloudflared_path()
        return self._cloudflared_path is not None

    async def start(self, port: int) -> TunnelInfo:
        """Start Cloudflare tunnel."""
        if not self._cloudflared_path:
            self._cloudflared_path = self._get_cloudflared_path()
        if not self._cloudflared_path:
            raise RuntimeError("cloudflared binary not available")

        log.info("Starting Cloudflare tunnel...")

        # Check for pre-configured tunnel token
        tunnel_token = os.environ.get("CLOUDFLARE_TUNNEL_TOKEN")

        if tunnel_token:
            # Use pre-configured tunnel
            process = subprocess.Popen(
                [self._cloudflared_path, "tunnel", "run", "--token", tunnel_token],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr separately
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
                [self._cloudflared_path, "tunnel", "--url", f"http://localhost:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr separately for error reporting
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
        import time

        # Match cloudflared quick tunnel URLs like https://random-words.trycloudflare.com
        # Exclude www.cloudflare.com which appears in privacy policy messages
        url_pattern = re.compile(
            r"https://(?!www\.)[a-zA-Z0-9-]+\.trycloudflare\.com"
        )

        start_time = time.time()
        last_progress_log = start_time
        collected_output: list[str] = []
        collected_errors: list[str] = []

        while True:
            current_time = time.time()
            elapsed = current_time - start_time

            # Check if process has exited
            if process.poll() is not None:
                # Capture any remaining output for debugging
                try:
                    stdout_rest, stderr_rest = process.communicate(timeout=1)
                    if stdout_rest:
                        collected_output.append(stdout_rest)
                    if stderr_rest:
                        collected_errors.append(stderr_rest)
                except Exception:
                    pass

                error_output = "\n".join(collected_errors) if collected_errors else "None"
                stdout_output = "\n".join(collected_output) if collected_output else "None"

                raise RuntimeError(
                    f"cloudflared exited with code {process.returncode}.\n"
                    f"stdout: {stdout_output}\n"
                    f"stderr: {error_output}"
                )

            # Timeout check
            if elapsed > timeout:
                process.terminate()
                raise TimeoutError(
                    f"Timed out waiting for Cloudflare URL after {timeout}s. "
                    "Check your network connection or try a different tunnel provider."
                )

            # Log progress every 10 seconds
            if current_time - last_progress_log > 10:
                log.info(f"Still waiting for Cloudflare tunnel URL... ({int(elapsed)}s elapsed)")
                last_progress_log = current_time

            # cloudflared outputs the tunnel URL to stderr, not stdout!
            # Check both streams for the URL pattern
            import select

            streams_to_check = []
            if process.stdout:
                streams_to_check.append((process.stdout, "stdout", collected_output))
            if process.stderr:
                streams_to_check.append((process.stderr, "stderr", collected_errors))

            for stream, stream_name, collected in streams_to_check:
                try:
                    readable, _, _ = select.select([stream], [], [], 0.1)
                    if readable:
                        line = stream.readline()
                        if line:
                            line_str = line.strip()
                            collected.append(line_str)
                            log.debug(f"cloudflared {stream_name}: {line_str}")
                            # Check for URL in this line - URL appears in stderr!
                            match = url_pattern.search(line_str)
                            if match:
                                log.info(f"Found tunnel URL in {stream_name}")
                                return match.group(0)
                except (ValueError, OSError):
                    # select may fail on Windows or closed file
                    pass

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

        errors: list[tuple[str, str]] = []
        for provider in available:  # type: ignore[assignment]
            try:
                log.info(f"Trying {provider.name.value}...")  # type: ignore[union-attr]
                self.active_tunnel = await provider.start(port)  # type: ignore[union-attr]
                log.info(f"Successfully started tunnel with {provider.name.value}")  # type: ignore[union-attr]
                return self.active_tunnel
            except Exception as e:
                log.warning(f"Failed to start {provider.name.value}: {e}")  # type: ignore[union-attr]
                errors.append((provider.name.value, str(e)))  # type: ignore[union-attr]

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
