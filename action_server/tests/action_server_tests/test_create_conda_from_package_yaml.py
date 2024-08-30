import json
import shutil
import sys
from pathlib import Path

import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


@pytest.fixture
def wheel_path(tmpdir, datadir) -> Path:
    import subprocess

    create_wheel_dir = datadir / "create_wheel"
    # python3 setup.py bdist_wheel
    subprocess.run([sys.executable, "-m", "pip", "wheel", "."], cwd=create_wheel_dir)

    wheels_found = list(create_wheel_dir.glob("*.whl"))
    assert len(wheels_found) == 1, f"Expected one wheel. Found: {wheels_found}"
    return wheels_found[0]


def test_package_update(tmpdir, data_regression):
    import io

    import yaml

    from sema4ai.action_server.vendored_deps.action_package_handling import (
        update_package,
    )

    tmp = Path(tmpdir)
    conda_yaml = tmp / "conda.yaml"
    conda_yaml.write_text(
        """
channels:
  - conda-forge

dependencies:
  - python=3.10.12
  - pip=23.2.1
  - robocorp-truststore=0.8.0
  - foo>3
  - bar>=3
  - pip:
      - robocorp==1.4.0
      - robocorp-actions==0.0.7
      - playwright>1.1
      - pytz==2023.3
rccPostInstall:
  - python -m foobar
"""
    )
    stream = io.StringIO()
    update_package(tmp, dry_run=True, stream=stream)

    assert not (tmp / "package.yaml").exists()

    update_package(tmp, dry_run=False, backup=False, stream=stream)
    assert (tmp / "package.yaml").exists()
    with (tmp / "package.yaml").open() as stream:
        data_regression.check(yaml.safe_load(stream))
