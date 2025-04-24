import os
import sys

import pytest

from action_server_tests.fixtures import ActionServerClient, ActionServerProcess


@pytest.mark.integration_test
def test_version() -> None:
    from sema4ai.action_server import __version__

    from action_server_tests.fixtures import sema4ai_action_server_run

    result = sema4ai_action_server_run(["version"], returncode=0)
    assert result.stdout.strip() == __version__


@pytest.mark.integration_test
def test_download_rcc(tmpdir) -> None:
    from action_server_tests.fixtures import sema4ai_action_server_run

    rcc_location = tmpdir / ("rcc.exe" if sys.platform == "win32" else "rcc")
    sema4ai_action_server_run(["download-rcc", "--file", rcc_location], returncode=0)
    assert os.path.exists(rcc_location)


@pytest.mark.integration_test
def test_new(
    tmpdir, action_server_process: ActionServerProcess, client: ActionServerClient
) -> None:
    from sema4ai.action_server._selftest import check_new_template

    check_new_template(tmpdir, action_server_process, client)


@pytest.mark.integration_test
def test_new_list_templates(tmpdir) -> None:
    import json

    from sema4ai.action_server._selftest import sema4ai_action_server_run

    output = sema4ai_action_server_run(
        ["new", "list-templates"], returncode=0, cwd=tmpdir
    )

    assert "Minimal" in output.stderr
    assert "Basic" in output.stderr
    assert "Advanced" in output.stderr

    output = sema4ai_action_server_run(
        ["new", "list-templates", "--json"], returncode=0, cwd=tmpdir
    )

    templates: list[dict[str, str]] = json.loads(output.stdout)

    template_names = {template.get("name") for template in templates}
    assert template_names == {
        "advanced",
        "basic",
        "minimal",
        "data-access-query",
        "data-access-native",
    }


def fix_eol(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "args",
    [
        ["-h"],
        ["start", "-h"],
        ["migrate", "-h"],
        ["import", "-h"],
    ],
)
def test_help(args, str_regression, datadir):
    import re

    from action_server_tests.fixtures import sema4ai_action_server_run

    result = sema4ai_action_server_run(args, returncode=0)
    out = re.sub(r"\(\d+.\d+.\d+\)", "(<version>)", result.stdout)
    v2_expected = datadir / "test_help_v2.txt"
    found = v2_expected.read_text()
    if fix_eol(found) != fix_eol(out):
        str_regression.check(out)


@pytest.mark.integration_test
def test_migrate(database_v0):
    from sema4ai.action_server.migrations import MigrationStatus, db_migration_status

    from action_server_tests.fixtures import sema4ai_action_server_run

    db_path = database_v0
    assert db_migration_status(db_path) == MigrationStatus.NEEDS_MIGRATION
    sema4ai_action_server_run(
        [
            "migrate",
            "--datadir",
            str(db_path.parent),
            "--db-file",
            str(db_path.name),
        ],
        returncode=0,
    )

    assert db_migration_status(db_path) == MigrationStatus.UP_TO_DATE


def test_default_datadir(tmpdir):
    from pathlib import Path

    from sema4ai.action_server._cli_impl import _create_parser
    from sema4ai.action_server._settings import setup_settings

    use_dir = Path(tmpdir) / "foobar"
    curdir = Path(".").absolute()

    try:
        use_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(str(use_dir.absolute()))
        parser = _create_parser()
        base_args = parser.parse_args(["start"])

        with setup_settings(base_args) as settings:
            assert settings.datadir.name.startswith("foobar_")
    finally:
        os.chdir(str(curdir))


def test_datadir_user_specified(tmpdir):
    from pathlib import Path

    from sema4ai.action_server._cli_impl import _create_parser
    from sema4ai.action_server._settings import setup_settings

    use_dir = Path(tmpdir) / "foobar"

    parser = _create_parser()
    base_args = parser.parse_args(["start", "--datadir", str(use_dir)])

    with setup_settings(base_args) as settings:
        assert Path(settings.datadir) == use_dir


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "op", ["dry_run.backup", "dry_run.no_backup", "update.backup", "update.no_backup"]
)
def test_package_update(tmpdir, str_regression, op):
    from pathlib import Path

    from action_server_tests.fixtures import sema4ai_action_server_run

    tmp = Path(tmpdir)

    robot_yaml = tmp / "robot.yaml"
    robot_yaml.write_text(
        """
environmentConfigs:
  - environment_windows_amd64_freeze.yaml
  - environment_linux_amd64_freeze.yaml
  - environment_darwin_amd64_freeze.yaml
  - conda.yaml
"""
    )

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
"""
    )

    assert (
        "Command for package operation not specified."
        in sema4ai_action_server_run(["package"], returncode=1).stderr
    )

    if op == "dry_run.no_backup":
        result = sema4ai_action_server_run(
            ["package", "update", "--dry-run", "--no-backup"], returncode=0, cwd=tmp
        )
        assert (tmp / "robot.yaml").exists()
        assert (tmp / "conda.yaml").exists()
        assert not (tmp / "package.yaml").exists()

    elif op == "dry_run.backup":
        result = sema4ai_action_server_run(
            ["package", "update", "--dry-run"], returncode=0, cwd=tmp
        )
        assert (tmp / "robot.yaml").exists()
        assert (tmp / "conda.yaml").exists()
        assert not (tmp / "package.yaml").exists()

    elif op == "update.backup":
        result = sema4ai_action_server_run(["package", "update"], returncode=0, cwd=tmp)
        assert (tmp / "robot.yaml.bak").exists()
        assert (tmp / "conda.yaml.bak").exists()
        assert (tmp / "package.yaml").exists()

    elif op == "update.no_backup":
        result = sema4ai_action_server_run(
            ["package", "update", "--no-backup"], returncode=0, cwd=tmp
        )
        assert not (tmp / "robot.yaml.bak").exists()
        assert not (tmp / "conda.yaml.bak").exists()
        assert not (tmp / "robot.yaml").exists()
        assert not (tmp / "conda.yaml").exists()
        assert (tmp / "package.yaml").exists()

    str_regression.check(result.stdout)


@pytest.mark.integration_test
def test_oauth2_sema4ai_config(tmpdir) -> None:
    from sema4ai.action_server._selftest import sema4ai_action_server_run

    output = sema4ai_action_server_run(["oauth2"], returncode=1, cwd=tmpdir)

    assert "Command for oauth2 operation not specified." in output.stderr

    # Return code assertion happens inside the call.
    sema4ai_action_server_run(["oauth2", "sema4ai-config"], returncode=0, cwd=tmpdir)
