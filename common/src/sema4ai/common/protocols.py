from enum import Enum
from typing import Any, Generic, Protocol, TypedDict, TypeVar

T = TypeVar("T")
Y = TypeVar("Y", covariant=True)


def check_implements(x: T) -> T:
    """
    Helper to check if a class implements some protocol.

    :important: It must be the last method in a class due to
                https://github.com/python/mypy/issues/9266

        Example:

    def __typecheckself__(self) -> None:
        _: IExpectedProtocol = check_implements(self)

    Mypy should complain if `self` is not implementing the IExpectedProtocol.
    """
    return x


class Sentinel(Enum):
    SENTINEL = 0
    USE_DEFAULT_TIMEOUT = 1


class ActionResultDict(TypedDict, Generic[T]):
    success: bool
    message: None | (
        str
    )  # if success == False, this can be some message to show to the user
    result: T | None


class ActionResult(Generic[T]):
    success: bool
    message: None | (
        str
    )  # if success == False, this can be some message to show to the user
    result: T | None

    def __init__(
        self, success: bool, message: str | None = None, result: T | None = None
    ):
        self.success = success
        self.message = message
        self.result = result

    def as_dict(self) -> ActionResultDict[T]:
        return {"success": self.success, "message": self.message, "result": self.result}

    def __str__(self):
        return f"ActionResult(success={self.success!r}, message={self.message!r}, result={self.result!r})"

    __repr__ = __str__

    @classmethod
    def make_failure(cls, message: str) -> "ActionResult[T]":
        return ActionResult(success=False, message=message, result=None)

    @classmethod
    def make_success(cls, result: T) -> "ActionResult[T]":
        return ActionResult(success=True, message=None, result=result)


class ICancelMonitorListener(Protocol):
    def __call__(self) -> Any:
        pass


class IMonitor(Protocol):
    def cancel(self) -> None:
        pass

    def check_cancelled(self) -> None:
        """
        raises CancelledError (from concurrent.futures import CancelledError) if cancelled.
        """

    def is_cancelled(self) -> bool:
        """
        returns True if cancelled, False otherwise.
        """

    def add_cancel_listener(self, listener: ICancelMonitorListener):
        """
        Adds a listener that'll be called when the monitor is cancelled.
        """
