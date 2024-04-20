from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(scope="session")
def resources_dir():
    resources = Path(__file__).parent / "resources"
    assert resources.exists()
    return resources


@pytest.fixture(autouse=True)
def disable_truststore_injection(monkeypatch):
    """Disables truststore SSL injection during testing, so we'd avoid
    unnecessary warnings given the missing dependency."""

    monkeypatch.setenv("_RC_TEST_USE_TRUSTSTORE", "False")


@pytest.fixture(autouse=True)
def _fix_pythonpath() -> Iterator[None]:
    import sys

    if "actions" in sys.modules:
        # We have actions.py and actions/__init__.py in different tests, so, proactively
        # remove it.
        del sys.modules["actions"]

    from sema4ai.actions._collect_actions import clear_previously_collected_actions

    clear_previously_collected_actions()

    yield

    clear_previously_collected_actions()
    if "actions" in sys.modules:
        # We have actions.py and actions/__init__.py in different tests, so, proactively
        # remove it.
        del sys.modules["actions"]
