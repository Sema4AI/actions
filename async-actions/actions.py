"""
A bare-bone AI Action template

Please check out the base guidance on AI Actions in our main repository readme:
https://github.com/sema4ai/actions/blob/master/README.md

"""

import time
from sema4ai.actions import action
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    name: str = Field(description="Name of the item", default="")
    price: int = Field(description="Price of the item", default=0)


class Order(BaseModel):
    date: str = Field(description="Date of the order", default="")
    items: list[OrderItem] = Field(description="List of items", default=[])


@action(is_async=True)
def get_order_information(sleep_time: int = 10) -> Order:
    """
    Long-running async function, returning mocked data after 5 seconds.

    Args:
        sleep_time: Seconds to sleep before returning data.

    Returns:
        Mocked order data.
    """

    time.sleep(sleep_time)

    data: Order = Order(
        date=time.strftime("%Y-%m-%d"),
        items=[
            OrderItem(name="MacBook Pro", price=3000),
            OrderItem(name="Logitech Mouse", price=50),
        ],
    )

    return data