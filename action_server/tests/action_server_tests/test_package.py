import json
import os
import re
import zipfile
from pathlib import Path

from action_server_tests.fixtures import fix_metadata


def check_regexp_in_lines(text, regexp):
    """Checks if the given regexp is found in any line of the text.

    Args:
      text: The text to search in.
      regexp: The regular expression to search for.

    Returns:
      True if the regexp is found in any line, False otherwise.
    """

    compiled_regexp = re.compile(regexp)
    for line in text.splitlines():
        if compiled_regexp.search(line) is not None:
            return
    raise RuntimeError(f"Did not find regexp: {regexp} in text:\n{text}")


def test_package_zip(datadir):
    from sema4ai.action_server._selftest import robocorp_action_server_run

    output = robocorp_action_server_run(
        [
            "package",
            "build",
            "--input-dir",
            str(Path(datadir, "pack1")),
            "--output-dir",
            str(datadir),
            "--datadir",
            str(datadir / "data"),
            "--json",
            # "-v",
        ],
        returncode=0,
        cwd=datadir / "pack1",
    )
    zip_name = "pack1-name.zip"
    escaped = re.escape(zip_name)
    check_regexp_in_lines(output.stderr, f"Created(.*){escaped}")

    target_zip = datadir / zip_name
    assert os.path.exists(target_zip)
    assert json.loads(output.stdout) == {"package_path": str(target_zip)}

    with zipfile.ZipFile(target_zip, "r") as zip_file:
        file_names = set(zip_file.namelist())
        file_names = set(x for x in file_names if "__pycache__" not in x)

    assert file_names == {
        "another/ok.txt",
        "folder/dont_ignore",
        "hello_action.py",
        "package.yaml",
        "folder/ignore_only_at_root",
        "__action_server_metadata__.json",
    }

    assert not (datadir / "pack1" / "__action_server_metadata__.json").exists()

    # Extract it
    extract_to = datadir / "extracted"

    def extract():
        import json

        from sema4ai.action_server import __version__

        robocorp_action_server_run(
            [
                "package",
                "extract",
                "--override",
                "--output-dir",
                str(extract_to),
                str(target_zip),
            ],
            returncode=0,
            cwd=datadir,
        )
        files = set(f.name for f in extract_to.glob("*") if "__pycache__" not in f.name)
        assert files == {
            "another",
            "folder",
            "hello_action.py",
            "package.yaml",
            "__action_server_metadata__.json",
        }

        metadata = extract_to / "__action_server_metadata__.json"
        contents = json.loads(metadata.read_text())
        assert contents["openapi.json"]
        assert contents["openapi.json"]["info"]["version"] == __version__

    extract()
    # Just remove the package.yaml and see if it's restored.
    os.remove(extract_to / "package.yaml")
    extract()


def test_package_zip_no_actions(datadir):
    from sema4ai.action_server._selftest import robocorp_action_server_run

    output = robocorp_action_server_run(
        [
            "package",
            "build",
            "--output-dir",
            str(datadir),
            "--datadir",
            str(datadir / "data"),
        ],
        returncode=1,
        cwd=datadir / "pack2",
    )
    assert "No actions found" in output.stderr


def test_package_metadata(datadir, data_regression):
    import json

    from sema4ai.action_server._selftest import robocorp_action_server_run

    output = robocorp_action_server_run(
        [
            "package",
            "metadata",
            "--input-dir",
            str(Path(datadir, "pack1")),
            "--datadir",
            str(datadir / "data"),
        ],
        returncode=0,
        cwd=datadir / "pack1",
    )
    data_regression.check(fix_metadata(json.loads(output.stdout)))


def test_package_metadata_oauth2_secrets(datadir, data_regression):
    import json

    from sema4ai.action_server._selftest import robocorp_action_server_run

    output = robocorp_action_server_run(
        [
            "package",
            "metadata",
            "--datadir",
            str(datadir / "data"),
        ],
        returncode=0,
        cwd=datadir / "pack_oauth2_secrets",
    )
    data_regression.check(fix_metadata(json.loads(output.stdout)))


def test_package_metadata_secrets(datadir, data_regression):
    import json

    from sema4ai.action_server._selftest import robocorp_action_server_run

    output = robocorp_action_server_run(
        [
            "package",
            "metadata",
            "--datadir",
            str(datadir / "data"),
        ],
        returncode=0,
        cwd=datadir / "pack_secrets",
    )
    data_regression.check(fix_metadata(json.loads(output.stdout)))


def test_package_metadata_api(datadir, data_regression):
    from sema4ai.action_server import api

    action_package_dir = Path(datadir / "pack_secrets")
    found = api.package_metadata(action_package_dir, datadir=Path(datadir / "data"))
    data_regression.check(fix_metadata(found))
    data_regression.check(found)


def test_package_upload(datadir, data_regression):
    import json

    from sema4ai.action_server._selftest import robocorp_action_server_run

    # Build the action package first
    output = robocorp_action_server_run(
        [
            "package",
            "build",
            "--output-dir",
            str(datadir),
            "--datadir",
            str(datadir / "data"),
        ],
        returncode=0,
        cwd=datadir / "pack1",
    )
    zip_name = "pack1-name.zip"
    zip_path = Path(datadir, zip_name)
    assert os.path.exists(zip_path)

    output = robocorp_action_server_run(
        [
            "package",
            "upload",
            "--package-path",
            str(zip_path),
            "--organization-id",
            "6e49f3b9-9d25-4904-b22d-3b5e672f4d7b",
            "--access-credentials",
            os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS"),
            "--hostname",
            os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev"),
            "--json",
        ],
        returncode=0,
    )

    output = json.loads(output.stdout)
    regression_check = {
        "error": output["error"],
        "name": output["name"],
        "status": output["status"],
    }
    data_regression.check(regression_check)


def test_package_status(data_regression):
    import json

    from sema4ai.action_server._selftest import robocorp_action_server_run

    output = robocorp_action_server_run(
        [
            "package",
            "status",
            "--package-id",
            "21a4a0ea-7ada-4754-8a62-ed9d17dedb1d",
            "--organization-id",
            "6e49f3b9-9d25-4904-b22d-3b5e672f4d7b",
            "--access-credentials",
            os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS"),
            "--hostname",
            os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev"),
            "--json",
        ],
        returncode=0,
    )

    output = json.loads(output.stdout)

    # assert output["status"] in ["pending", "validating", "completed"]

    regression_check = {
        "changes": output["changes"],
        "error": output["error"],
        "id": output["id"],
        "name": output["name"],
        "url": output["url"],
        "status": output["status"],
    }

    data_regression.check(regression_check)


def test_package_set_changelog(data_regression):
    import json

    from sema4ai.action_server._selftest import robocorp_action_server_run

    output = robocorp_action_server_run(
        [
            "package",
            "set-changelog",
            "--package-id",
            "fdd0e9da-0508-499b-8020-0dd7c94b0a8c",
            "--organization-id",
            "6e49f3b9-9d25-4904-b22d-3b5e672f4d7b",
            "--change-log",
            "Testing",
            "--access-credentials",
            os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS"),
            "--hostname",
            os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev"),
            "--json",
        ],
        returncode=0,
    )

    output = json.loads(output.stdout)
    regression_check = {
        "changes": output["changes"],
        "error": output["error"],
        "id": output["id"],
        "name": output["name"],
        "url": output["url"],
    }
    data_regression.check(regression_check)
