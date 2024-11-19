from pathlib import Path

import pytest

DATA_SERVER_CLI_VERSION = "0.0.4"


def get_default_data_server_cli_location() -> Path:
    import sys

    from sema4ai.action_server._download_rcc import get_default_rcc_location

    parent = get_default_rcc_location().parent

    if sys.platform == "win32":
        return parent / f"data-server-cli-{DATA_SERVER_CLI_VERSION}.exe"
    else:
        return parent / f"data-server-cli-{DATA_SERVER_CLI_VERSION}"


class DataServerCli:
    def __init__(self, data_server_cli_path: Path):
        self.data_server_cli_path = data_server_cli_path

    def start_data_server(self):
        from sema4ai.action_server._robo_utils.process import check_output_interactive

        cmdline = [str(self.data_server_cli_path), "-h"]
        output = check_output_interactive(cmdline)
        print(output.decode("utf-8"))

        cmdline = [str(self.data_server_cli_path), "install"]
        try:
            output = check_output_interactive(cmdline, on_stdout=print, on_stderr=print)
        except Exception as e:
            output = (
                e.output
            )  # Currently even if status was collected the returncode may be non-zero

        print(output.decode("utf-8"))

        cmdline = [str(self.data_server_cli_path), "launch"]
        output = check_output_interactive(cmdline)
        print(output.decode("utf-8"))


@pytest.fixture(scope="session")
def data_server_cli() -> DataServerCli:
    import sys

    from sema4ai_http import DownloadStatus, download_with_resume

    # urls are something as:
    # Mac - https://cdn.sema4.ai/data-server-cli/beta/v0.0.3/macos64/data-server-cli
    # Win - https://cdn.sema4.ai/data-server-cli/beta/v0.0.3/windows64/data-server-cli.exe
    # Linux - https://cdn.sema4.ai/data-server-cli/beta/v0.0.3/linux64/data-server-cli
    # Latest released version: https://cdn.sema4.ai/data-server-cli/beta/v0.0.3/version.txt

    if sys.platform == "win32":
        platform = "windows"
        executable_name = "data-server-cli.exe"
    elif sys.platform == "darwin":
        platform = "macos"
        executable_name = "data-server-cli"
    else:
        platform = "linux"
        executable_name = "data-server-cli"

    target = get_default_data_server_cli_location()
    target.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://cdn.sema4.ai/data-server-cli/beta/v{DATA_SERVER_CLI_VERSION}/{platform}64/{executable_name}"
    assert download_with_resume(url, target, make_executable=True).status in (
        DownloadStatus.DONE,
        DownloadStatus.ALREADY_EXISTS,
    )

    return DataServerCli(target)
