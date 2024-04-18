from typing import Annotated, Tuple, Union

from pydantic import BaseModel, Field

from sema4ai.actions import action


@action
def return_tuple(a: str, b: int, c: str = "") -> Tuple[str, int]:
    assert isinstance(a, str)
    assert isinstance(b, int)
    return a, b


@action
def something_else(f: list) -> None:
    # We can't actually handle this at this point...
    assert isinstance(f, list)


@action
def bool_true(b: bool) -> None:
    assert isinstance(b, bool)
    assert b


@action
def bool_false(b: bool) -> None:
    assert isinstance(b, bool)
    assert not b


@action
def accept_str(s) -> None:
    assert isinstance(s, str)


@action
def unicode_ação_Σ(ação: str) -> None:
    assert isinstance(ação, str)


class MyCustomData(BaseModel):
    name: str
    price: Annotated[float, Field(description="This is the price.")]
    is_offer: Union[bool, None] = None


@action
def custom_data(data: MyCustomData) -> None:
    assert isinstance(data, MyCustomData)
