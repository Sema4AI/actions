import itertools

import pytest

from sema4ai.actions import session_cache
from sema4ai.actions._hooks import (
    after_all_actions_run,
    after_action_run,
    before_all_actions_run,
    before_action_run,
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


def test_session_cache_yield():
    assert len(after_all_actions_run) == 0

    counter = itertools.count()

    calls = []

    @session_cache
    def my_function():
        calls.append("before")
        yield next(counter)
        calls.append("after")

    assert len(after_all_actions_run) == 0
    initial = my_function()
    assert len(after_all_actions_run) == 1
    assert calls == ["before"]

    assert my_function() == initial
    assert my_function() == initial

    # Emulate framework finishing the run of all tasks.
    after_all_actions_run()
    assert calls == ["before", "after"]

    assert len(after_all_actions_run) == 0

    assert my_function() != initial
    assert calls == ["before", "after", "before"]
    assert len(after_all_actions_run) == 1
    after_all_actions_run()
    assert calls == ["before", "after", "before", "after"]
    assert len(after_all_actions_run) == 0


def test_session_cache_return():
    assert len(after_all_actions_run) == 0

    counter = itertools.count()

    @session_cache
    def my_function():
        return next(counter)

    assert len(after_all_actions_run) == 0
    initial = my_function()
    assert len(after_all_actions_run) == 1

    assert my_function() == initial
    assert my_function() == initial

    # Emulate framework finishing the run of all tasks.
    after_all_actions_run()
    assert len(after_all_actions_run) == 0

    assert my_function() != initial
    assert len(after_all_actions_run) == 1
    after_all_actions_run()
    assert len(after_all_actions_run) == 0


def test_integrated(datadir, str_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["run", "-a", "task1", "-a", "task2", "--console-colors=plain"],
        returncode=0,
        cwd=str(datadir),
    )
    str_regression.check_until_header(result.stdout.decode("utf-8"))
