import logging
import platform
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Note: also referenced in action_server/build.py
# Using joshyorko/rcc open-source version
RCC_VERSION = "18.16.0"


def get_default_rcc_location() -> Path:
    CURDIR = Path(__file__).parent.absolute()
    if sys.platform == "win32":
        rcc_path = CURDIR / "bin" / f"rcc-{RCC_VERSION}.exe"
    else:
        rcc_path = CURDIR / "bin" / f"rcc-{RCC_VERSION}"
    return rcc_path


def download_rcc(
    target: Optional[str] = None,
    force=False,
) -> Path:
    """
    Downloads RCC in the place where the action server expects it.
    """
    import os

    from sema4ai.common.system_mutex import timed_acquire_mutex

    if target:
        rcc_path = Path(target)
    else:
        rcc_path = get_default_rcc_location()

    if not force:
        if rcc_path.exists():
            return rcc_path

        log.info(f"RCC not available at: {rcc_path}. Downloading.")

    rcc_path.parent.mkdir(parents=True, exist_ok=True)

    machine = platform.machine()
    is_64 = not machine or "64" in machine

    # Using joshyorko/rcc GitHub releases
    # Asset names: rcc-windows64.exe, rcc-darwin64, rcc-linux64
    if sys.platform == "win32":
        if is_64:
            asset_name = "rcc-windows64.exe"
        else:
            raise RuntimeError("Unsupported platform (windows 32 bits)")

    elif sys.platform == "darwin":
        if machine == "arm64":
            asset_name = "rcc-darwin64"
        else:
            raise RuntimeError("Unsupported platform (macos x86_64)")

    else:
        if is_64:
            asset_name = "rcc-linux64"
        else:
            raise RuntimeError("Unsupported platform (linux 32 bits)")

    # GitHub releases URL format
    rcc_url = f"https://github.com/joshyorko/rcc/releases/download/v{RCC_VERSION}/{asset_name}"

    timeout = 300.0

    if "SEMA4AI_ACTION_SERVER_RCC_DOWNLOAD_TIMEOUT" in os.environ:
        # Users can override timeout by setting the environment variable.
        timeout = float(os.environ["SEMA4AI_ACTION_SERVER_RCC_DOWNLOAD_TIMEOUT"])

    with timed_acquire_mutex(
        "action_server_rcc_download", timeout=timeout, raise_error_on_timeout=True
    ):
        if not force and rcc_path.exists():
            # It was downloaded by some other process while we were waiting for the mutex.
            return rcc_path

        import sema4ai_http

        status = sema4ai_http.download_with_resume(
            rcc_url, rcc_path, make_executable=True, overwrite_existing=True
        )
        if status.status in (
            sema4ai_http.DownloadStatus.HTTP_ERROR,
            sema4ai_http.DownloadStatus.PARTIAL,
        ):
            raise RuntimeError(f"Failed to download RCC: {status.status}")

    return rcc_path


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log.info("Logging setup")

    ret = download_rcc(
        target="/Users/fabioz/Desktop/sema4aiws/actions/action_server/src/sema4ai/action_server/bin/rcc-17.28.4",
        force=True,
    )
    log.info("Downloaded: %s", ret)
