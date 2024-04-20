from sema4ai.actions import action

print("some message while collecting.")


def some_method():
    print("In some method")


@action
def main():
    """
    main method docstring
    """
    some_method()


def raise_an_error():
    raise ValueError("asd")


@action
def main_errors():
    raise_an_error()


@action
def task_with_args(my_input_arg: str, multiplier: int) -> str:
    return my_input_arg * multiplier
