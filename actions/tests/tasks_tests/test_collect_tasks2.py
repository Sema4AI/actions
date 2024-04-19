import pytest


@pytest.fixture
def _fix_pythonpath(datadir):
    import sys

    p = str(datadir / "different_root")
    sys.path.append(p)
    yield

    sys.path.remove(p)


def test_colect_tasks_resolves_with_pythonpath(datadir, _fix_pythonpath):
    from sema4ai.actions._collect_actions import collect_actions
    from sema4ai.actions._customization._plugin_manager import PluginManager

    actions = tuple(
        collect_actions(PluginManager(), datadir / "different_root" / "actions")
    )
    assert len(actions) == 1, f"Found actions: {actions}"
