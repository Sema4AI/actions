import json
import os

import pytest


def _fix_file(entry):
    entry["file"] = os.path.basename(entry["file"])


@pytest.mark.parametrize(
    "glob_pattern",
    [
        None,
        "my_module*.py",
        "*.py",
        "**/*.py",  # ** is accepted, but not really required (it's always an rglob).
        "another_module.py",
        "my_action.py|another_module.py",
    ],
)
def test_collect_tasks_glob(datadir, data_regression, glob_pattern):
    from devutils.fixtures import sema4ai_actions_run

    cmdline = ["list", str(datadir), "--skip-lint"]
    if glob_pattern:
        cmdline.extend(("--glob", glob_pattern))

    result = sema4ai_actions_run(cmdline, returncode=0, cwd=datadir)
    found = json.loads(result.stdout)
    for entry in found:
        _fix_file(entry)
    found = sorted(found, key=lambda obj: obj["name"])
    data_regression.check(found)


def test_run_tasks_glob(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    cmdline = [
        "run",
        str(datadir),
        "--glob",
        "my_action.py|another_module.py",
        "--console-colors=plain",
    ]

    result = sema4ai_actions_run(cmdline, returncode=1, cwd=datadir)
    output = result.stdout.decode("utf-8")
    assert "Expected a single action to be run." in output


def test_run_tasks_glob_multiple_matches(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    cmdline = [
        "run",
        str(datadir),
        "--glob",
        "*.py|**/*.py",
        "--console-colors=plain",
    ]

    result = sema4ai_actions_run(cmdline, returncode=1, cwd=datadir)
    output = result.stdout.decode("utf-8")
    assert "Expected a single action to be run." in output
