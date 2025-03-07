import logging
import os
import sys
from pathlib import Path

from sema4ai.common.process import ProcessRunResult

log = logging.getLogger(__name__)


class BaseTool:
    mutex_name: str
    base_url: str
    executable_name: str
    version_command: tuple[str, ...] = ("--version",)
    available_in_mac_os_arm64: bool = True

    macos_arm_64_download_path: str = "macos-arm64"
    macos_download_path: str = "macos64"
    win64_download_path: str = "windows64"
    linux64_download_path: str = "linux64"

    # May be set in the subclass or instance to configure the platform to download the tool for.
    force_sys_platform: str | None = None
    # May be set in the subclass or instance to configure the machine architecture to download the tool for.
    force_machine: str | None = None
    # May be set in the subclass or instance to configure the run check to be done when verifying the tool.
    make_run_check: bool = True

    @classmethod
    def get_default_executable(cls, *, version: str, download: bool = False) -> Path:
        """
        This should be the preferred way to get the executable.

        i.e.:

        action_server_executable = ActionServerTool.get_executable_path(
            version="0.1.0", download=True
        )

        Then the `action_server_executable` will be a Path to the executable and will be
        downloaded if `download` is True (otherwise it will be checked if the executable
        exists and is executable).
        """
        from sema4ai.common.locations import get_default_executable_path

        target_location = get_default_executable_path(
            name=cls.executable_name, version=version
        )

        if download:
            target_location.parent.mkdir(parents=True, exist_ok=True)
            action_server_tool = cls(
                target_location=str(target_location),
                tool_version=version,
            )

            action_server_tool.download()

        return target_location

    def __init__(self, target_location: str, tool_version: str):
        self._target_location = target_location
        self._tool_version = tool_version

    def download(self) -> None:
        _download_tool(self, self._target_location, self._tool_version)

    def verify(self) -> bool:
        return _verify_tool_downloaded_ok(
            self,
            self._target_location,
            force=True,
            make_run_check=self.make_run_check,
            version=self._tool_version,
        )

    def _get_release_artifact_relative_path(self, executable_name: str) -> str:
        """
        Helper function for getting the release artifact relative path as defined in S3 bucket.

        Args:
            sys_platform: Platform for which the release artifact is being retrieved.
            executable_name: Name of the executable we want to get the path for.
        """
        import platform

        sys_platform = self.force_sys_platform or sys.platform
        machine = self.force_machine or platform.machine()
        is_64 = not machine or "64" in machine

        if sys_platform == "win32":
            if is_64:
                return f"{self.win64_download_path}/{executable_name}.exe"
            else:
                raise RuntimeError("32-bit windows is no longer supported")

        elif sys_platform == "darwin":
            if machine == "arm64" and self.available_in_mac_os_arm64:
                # Backwards compatibility (older version defined macos arm64 in "arm_64_download_path")
                macos_arm64_path = getattr(self, "arm_64_download_path", None)
                if not macos_arm64_path:
                    macos_arm64_path = self.macos_arm_64_download_path
                return f"{macos_arm64_path}/{executable_name}"
            else:
                return f"{self.macos_download_path}/{executable_name}"

        else:
            if is_64:
                return f"{self.linux64_download_path}/{executable_name}"
            else:
                raise RuntimeError("32-bit linux is no longer supported")


def _get_tool_version(tool: BaseTool, location: str) -> ProcessRunResult:
    from sema4ai.common.process import launch_and_return_future

    version_command = tool.version_command

    cwd = "."
    env: dict[str, str] = {}
    future = launch_and_return_future(
        (location,) + version_command, environ=env, cwd=cwd
    )
    return future.result()


def _verify_tool_downloaded_ok(
    tool: BaseTool, location: str, force: bool, make_run_check: bool, version: str
) -> bool:
    """
    Args:
        version: If `make_run_check` is True, the version is matched against the
            downloaded version (and if it doesn't match `False` will be returned).

    Returns:
        True if everything is ok and False otherwise.
    """
    if location in _checked_downloaded_tools and not force:
        if os.path.isfile(location):
            return True  # Already checked: just do simpler check.

    import time

    if not os.path.isfile(location):
        log.info(f"Tool {location} does not exist.")
        return False

    if not os.access(location, os.X_OK):
        log.info(f"Tool {location} is not executable.")
        return False

    # Actually execute it to make sure it works (in windows right after downloading
    # it may not be ready, so, retry a few times).
    if not make_run_check:
        _checked_downloaded_tools.add(location)
        return True
    else:
        times = 5
        timeout = 1
        for _ in range(times):
            version_result = _get_tool_version(tool, location)
            if version_result.returncode == 0:
                if (
                    version_result.stdout
                    and version_result.stdout.strip() == version.strip()
                ):
                    _checked_downloaded_tools.add(location)
                    return True
                else:
                    log.info(
                        f"The currently downloaded version of {location} ({version_result.stdout!r}) "
                        f"does not match the required version for the vscode extension: {version}"
                    )
                    return False
            time.sleep(timeout / times)
        log.info(
            f"Tool {location} failed to execute. Details:\nstderr={version_result.stderr}\nstdout={version_result.stdout}"
        )

        return False


# Entries should be the location of the tools
_checked_downloaded_tools: set[str] = set()


def _download_tool(
    tool: BaseTool,
    location: str,
    tool_version: str,
    force: bool = False,
) -> None:
    """
    Downloads the given Sema4.ai tool to the specified location. Note that it doesn't overwrite it if it
    already exists (unless force == True).

    Args:
        tool: The type of the tool to download. Available tools are specified with Tool enum.
        location: The location to store the tool executable in the filesystem.
        tool_version: version of the tool to download.
        force: Whether we should overwrite an existing installation. Defaults to False.
    """

    from pathlib import Path

    from sema4ai_http import download_with_resume

    from sema4ai.common.system_mutex import timed_acquire_mutex

    if not force:
        if _verify_tool_downloaded_ok(
            tool,
            location,
            force=force,
            make_run_check=tool.make_run_check,
            version=tool_version,
        ):
            return

    with timed_acquire_mutex(tool.mutex_name, timeout=300):
        # If other call was already in progress, we need to check it again,
        # as to not overwrite it when force was equal to False.
        if not force:
            if _verify_tool_downloaded_ok(
                tool,
                location,
                force=force,
                make_run_check=tool.make_run_check,
                version=tool_version,
            ):
                return

        executable_name = tool.executable_name

        relative_path = tool._get_release_artifact_relative_path(executable_name)

        url = f"{tool.base_url}/{tool_version}/{relative_path}"

        try:
            download_with_resume(
                url,
                Path(location),
                make_executable=True,
            )
        except Exception:
            raise RuntimeError(
                f"There was an error downloading {tool.executable_name!r} to {location} from: {url!r}!"
            )

        if not _verify_tool_downloaded_ok(
            tool,
            location,
            force=True,
            make_run_check=tool.make_run_check,
            version=tool_version,
        ):
            raise Exception(
                f"After downloading {tool!r} the verification failed (location: {location})!"
            )


class ActionServerTool(BaseTool):
    mutex_name = "sema4ai-get-action-server"
    base_url = "https://cdn.sema4.ai/action-server/releases"
    executable_name = "action-server"

    # Version command for the action-server tool is different from the other tools.
    version_command = ("version",)

    def __init__(self, target_location: str, tool_version: str):
        super().__init__(target_location, tool_version)


class AgentCliTool(BaseTool):
    mutex_name = "sema4ai-get-agent-cli"
    base_url = "https://cdn.sema4.ai/agent-cli/releases"
    executable_name = "agent-cli"
    available_in_mac_os_arm64 = False

    def __init__(self, target_location: str, tool_version: str):
        super().__init__(target_location, tool_version)


class RccTool(BaseTool):
    mutex_name = "sema4ai-get-rcc"
    base_url = "https://cdn.sema4.ai/rcc/releases"
    executable_name = "rcc"

    def __init__(self, target_location: str, tool_version: str):
        super().__init__(target_location, tool_version)


class DataServerTool(BaseTool):
    mutex_name = "sema4ai-get-data-server"
    base_url = "https://cdn.sema4.ai/data-server-cli/beta"
    executable_name = "data-server-cli"

    # Different naming for arm64 on macos for the data-server-cli tool
    macos_arm_64_download_path = "macos_arm64"

    def __init__(self, target_location: str, tool_version: str):
        super().__init__(target_location, tool_version)


__all__ = ["BaseTool", "ActionServerTool", "AgentCliTool", "RccTool", "DataServerTool"]
