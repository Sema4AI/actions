from my_package import my_lib

from sema4ai.actions import action

from .my_lib import MyClass


@action
def my_action() -> str:
    """
    This is the docstring
    """
    return f"{MyClass} == {my_lib.MyClass.__name__}"
