"""
A bare-bone AI Action template

Please check out the base guidance on AI Actions in our main repository readme:
https://github.com/sema4ai/actions/blob/master/README.md

"""

from sema4ai.actions import action


@action
def greet() -> str:
    """
    An empty AI Action Template.

    Returns:
        Simple "Hello world" message.
    """
    return "Hello world!\n"
