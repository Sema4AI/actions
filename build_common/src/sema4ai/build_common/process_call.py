import subprocess
import sys
from typing import Sequence


def run(cmd: Sequence[str], cwd=None, shell=False, env: dict | None = None) -> None:
    import shlex

    print(cmd)
    print(
        "Calling: ",
        subprocess.list2cmdline(cmd) if sys.platform == "win32" else shlex.join(cmd),
    )
    subprocess.check_call(cmd, cwd=cwd, shell=shell, env=env)


def run_and_capture_output(
    cmd: Sequence[str], cwd=None, shell=False, env: dict | None = None
) -> tuple[str, str]:
    import shlex

    print(cmd)
    print(
        "Calling (capturing output): ",
        subprocess.list2cmdline(cmd) if sys.platform == "win32" else shlex.join(cmd),
    )
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=shell,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return result.stdout, result.stderr
