import os

from sema4ai.tasks import task


@task
def main_task():
    from tempfile import gettempdir

    os.chdir(gettempdir())
