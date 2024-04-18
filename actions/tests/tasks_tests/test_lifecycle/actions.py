import itertools

from sema4ai.actions import action, action_cache

_counter = itertools.count()


@action_cache
def new_obj():
    return next(_counter)


@action
def task1():
    assert new_obj() == 0
    assert new_obj() == 0


@action
def task2():
    assert new_obj() == 1
    assert new_obj() == 1
