from sema4ai.actions import Request, action
from sema4ai.actions._secret import Secret


@action
def my_action(arg: str, private_info: Secret, request: Request) -> str:
    """
    Does something
    """
    assert "x-action-context" in request.headers
    return "Ok"
