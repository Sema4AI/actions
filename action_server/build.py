import os
import platform
import sys
from pathlib import Path
from typing import Optional

# No real build, just download RCC at this point.

# Note: referenced here and in sema4ai.action_server._download_rcc
RCC_VERSION = "17.28.4"

RCC_URLS = {
    "Windows": f"https://cdn.sema4.ai/rcc/releases/v{RCC_VERSION}/windows64/rcc.exe",
    "Darwin": f"https://cdn.sema4.ai/rcc/releases/v{RCC_VERSION}/macos64/rcc",
    "Linux": f"https://cdn.sema4.ai/rcc/releases/v{RCC_VERSION}/linux64/rcc",
}

CURDIR = Path(__file__).parent.absolute()


def _download_rcc(system: Optional[str] = None, target: Optional[str] = None):
    """
    Downloads RCC in the place where the action server expects it.
    """
    import stat
    import urllib.request

    if target:
        rcc_path = Path(target)
    else:
        if sys.platform == "win32":
            rcc_path = (
                CURDIR
                / "src"
                / "sema4ai"
                / "action_server"
                / "bin"
                / f"rcc-{RCC_VERSION}.exe"
            )
        else:
            rcc_path = (
                CURDIR
                / "src"
                / "sema4ai"
                / "action_server"
                / "bin"
                / f"rcc-{RCC_VERSION}"
            )

    rcc_url = RCC_URLS[system or platform.system()]

    print(f"Downloading '{rcc_url}' to '{rcc_path}'")

    # Cloudflare seems to be blocking "User-Agent: Python-urllib/3.9".
    # Use a different one as that must be sorted out.
    response = urllib.request.urlopen(
        urllib.request.Request(rcc_url, headers={"User-Agent": "Mozilla"})
    )

    with open(rcc_path, "wb") as stream:
        stream.write(response.read())

    st = os.stat(rcc_path)
    os.chmod(rcc_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return rcc_path


def build(*args, **kwarg):
    if os.environ.get("ACTION_SERVER_SKIP_DOWNLOAD_IN_BUILD", "").lower().strip() in (
        "1",
        "true",
    ):
        return

    _download_rcc()


if __name__ == "__main__":
    build()
