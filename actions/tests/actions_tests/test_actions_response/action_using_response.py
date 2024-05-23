from pydantic import BaseModel

from sema4ai.actions import ActionError, Response, action


class SomeData(BaseModel):
    show: bool = True


@action
def return_response_ok_action() -> Response[SomeData]:
    return Response(result=SomeData(show=False))


@action
def return_response_error_action() -> Response[SomeData]:
    return Response(error="Something bad happened")


@action
def raise_other_error_action() -> Response[SomeData]:
    raise RuntimeError("Other error")


@action
def rase_action_error_action() -> Response[SomeData]:
    raise ActionError("Action error")
