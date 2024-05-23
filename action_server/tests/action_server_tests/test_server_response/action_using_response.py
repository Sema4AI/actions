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
def raise_action_error_action() -> Response[SomeData]:
    raise ActionError("Action error")


@action
def raise_action_error_action_not_response() -> str:
    raise ActionError("Action error")


@action
def raise_action_error_other_not_response() -> str:
    raise RuntimeError("Some unknown error")


@action
def bad_schema() -> Response[str]:
    return 1  # type: ignore
