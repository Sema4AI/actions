from sema4ai.tasks import task


@task
def make_error():
    raise RuntimeError("something bad happened")
