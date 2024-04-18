from sema4ai.actions import action


@action
def make_error():
    raise RuntimeError("something bad happened")
