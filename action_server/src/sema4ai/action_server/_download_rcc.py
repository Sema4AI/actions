import logging
import platform
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Note: also referenced in action_server/build.py
RCC_VERSION = "19.0.2"


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

    if sys.platform == "win32":
        if is_64:
            relative_path = "/windows64/rcc.exe"
        else:
            raise RuntimeError("Unsupported platform (windows 32 bits)")

    elif sys.platform == "darwin":
        if machine == "arm64":
            relative_path = "/macos-arm64/rcc"
        else:
            relative_path = "/macos64/rcc"

    else:
        if is_64:
            relative_path = "/linux64/rcc"
        else:
            relative_path = "/linux32/rcc"

    prefix = f"https://cdn.sema4.ai/rcc/releases/v{RCC_VERSION}"
    rcc_url = prefix + relative_path

    import sema4ai_http

    status = sema4ai_http.download_with_resume(rcc_url, rcc_path, make_executable=True)
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
