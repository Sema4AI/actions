import time

from sema4ai.actions import action, action_cache


@action_cache
def some_resource():
    yield "resource"
    while True:
        time.sleep(1)


@action
def neverending():
    some_resource()
