import time

from sema4ai.tasks import task, task_cache


@task_cache
def some_resource():
    yield "resource"
    while True:
        time.sleep(1)


@task
def neverending():
    some_resource()
