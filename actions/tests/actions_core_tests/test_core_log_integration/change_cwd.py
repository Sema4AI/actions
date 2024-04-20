import os

from sema4ai.actions import action


@action
def main_task():
    from tempfile import gettempdir

    os.chdir(gettempdir())
