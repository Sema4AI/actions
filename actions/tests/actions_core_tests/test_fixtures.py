from collections.abc import Iterable

import pytest

from sema4ai.actions import setup as actions_setup
from sema4ai.actions import teardown as actions_teardown
from sema4ai.actions._hooks import (
    after_action_run,
    after_all_actions_run,
    before_action_run,
    before_all_actions_run,
)


def _clear_callbacks():
    before_action_run._callbacks = ()
    before_all_actions_run._callbacks = ()
    after_action_run._callbacks = ()
    after_all_actions_run._callbacks = ()


@pytest.fixture(autouse=True)
def clear_callbacks():
    _clear_callbacks()
    yield
    _clear_callbacks()


def test_setup_default():
    assert len(before_action_run) == 0
    assert len(before_all_actions_run) == 0

    is_called = False

    @actions_setup
    def fixture(task):
        assert task == "placeholder"
        nonlocal is_called
        is_called = True

    assert not is_called
    assert len(before_action_run) == 1
    assert len(before_all_actions_run) == 0

    before_action_run("placeholder")
    assert is_called


def test_setup_all():
    assert len(before_action_run) == 0
    assert len(before_all_actions_run) == 0

    is_called = False

    @actions_setup(scope="session")
    def fixture(tasks):
        assert isinstance(tasks, Iterable)
        nonlocal is_called
        is_called = True

    assert not is_called
    assert len(before_action_run) == 0
    assert len(before_all_actions_run) == 1

    before_all_actions_run([])
    assert is_called


def test_setup_task():
    assert len(before_action_run) == 0
    assert len(before_all_actions_run) == 0

    is_called = False

    @actions_setup(scope="action")
    def fixture(task):
        assert task == "placeholder"
        nonlocal is_called
        is_called = True

    assert not is_called
    assert len(before_action_run) == 1
    assert len(before_all_actions_run) == 0

    before_action_run("placeholder")
    assert is_called


def test_teardown_default():
    assert len(after_action_run) == 0
    assert len(after_all_actions_run) == 0

    is_called = False

    @actions_teardown
    def fixture(task):
        assert task == "placeholder"
        nonlocal is_called
        is_called = True

    assert not is_called
    assert len(after_action_run) == 1
    assert len(after_all_actions_run) == 0

    after_action_run("placeholder")
    assert is_called


def test_teardown_all():
    assert len(after_action_run) == 0
    assert len(after_all_actions_run) == 0

    is_called = False

    @actions_teardown(scope="session")
    def fixture(tasks):
        assert isinstance(tasks, Iterable)
        nonlocal is_called
        is_called = True

    assert not is_called
    assert len(after_action_run) == 0
    assert len(after_all_actions_run) == 1

    after_all_actions_run([])
    assert is_called


def test_teardown_task():
    assert len(after_action_run) == 0
    assert len(after_all_actions_run) == 0

    is_called = False

    @actions_teardown(scope="action")
    def fixture(task):
        assert task == "placeholder"
        nonlocal is_called
        is_called = True

    assert not is_called
    assert len(after_action_run) == 1
    assert len(after_all_actions_run) == 0

    after_action_run("placeholder")
    assert is_called


def test_raises():
    @actions_setup
    def raises_setup(_):
        raise RuntimeError("Oopsie")

    @actions_teardown
    def raises_teardown(_):
        raise RuntimeError("Oopsie #2")

    assert len(before_action_run) == 1
    assert len(after_action_run) == 1

    with pytest.raises(RuntimeError):
        before_action_run(None)

    after_action_run(None)


def test_setup_generator():
    assert len(before_action_run) == 0
    assert len(after_action_run) == 0

    is_called = False

    @actions_setup
    def fixture_gen(task):
        assert task == "task"
        yield
        nonlocal is_called
        is_called = True

    assert not is_called
    assert len(before_action_run) == 1
    assert len(after_action_run) == 0

    before_action_run("task")

    assert not is_called
    assert len(before_action_run) == 1
    assert len(after_action_run) == 1

    after_action_run("task")

    assert is_called
    assert len(before_action_run) == 1
    assert len(after_action_run) == 0
