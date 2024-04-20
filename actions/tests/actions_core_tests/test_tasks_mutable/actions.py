from sema4ai.actions import action, teardown


@teardown
def make_pass(task):
    task.status = "PASS"


@action
def raises_error():
    raise RuntimeError("Something went wrong")


@action
def division_error():
    _ = 1 / 0
