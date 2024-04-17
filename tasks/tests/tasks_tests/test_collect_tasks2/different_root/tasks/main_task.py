from sema4ai.tasks import task

from . import module  # noqa


@task
def something():
    print("worked")
