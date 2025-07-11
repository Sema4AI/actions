import typing
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    TypedDict,
    TypeVar,
    Union,
)

ExcInfo = tuple[type[BaseException], BaseException, TracebackType]
OptExcInfo = Union[ExcInfo, tuple[None, None, None]]


T = TypeVar("T")
Y = TypeVar("Y", covariant=True)


def check_implements(x: T) -> T:
    """
    Helper to check if a class implements some protocol.

    Important: It must be the last method in a class due to
        https://github.com/python/mypy/issues/9266

    Example:

    ```
    def __typecheckself__(self) -> None:
        _: IExpectedProtocol = check_implements(self)
    ```

    Mypy should complain if `self` is not implementing the IExpectedProtocol.
    """
    return x


class Status(str, Enum):
    """Action state"""

    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"


class IAction(typing.Protocol):
    module_name: str
    filename: str
    method: typing.Callable

    status: Status
    message: str
    exc_info: Optional[OptExcInfo]

    # If the action completed successfully, this will be
    # the value returned by the action.
    result: Any

    options: Optional[Dict]

    @property
    def input_schema(self) -> Dict[str, Any]:
        """
        The input schema from the function signature.

        Example:

        ```
        {
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Some value.",
                    "title": "Value",
                    "default": 0
                }
            },
            "type": "object"
        }
        ```
        """

    @property
    def output_schema(self) -> Dict[str, Any]:
        """
        The output schema based on the function signature.

        Example:

        ```
        {
            "type": "string",
            "description": ""
        }
        ```
        """

    @property
    def managed_params_schema(self) -> Dict[str, Any]:
        """
        The schema for the managed parameters.

        Example:

        ```
        {
            "my_password": {
                "type": "Secret"
            },
            "request": {
                "type": "Request"
            }
        }
        ```
        """

    @property
    def name(self) -> str:
        """
        The name of the action.
        """

    @property
    def lineno(self) -> int:
        """
        The line where the action is declared.
        """

    def run(self) -> Any:
        """
        Runs the action and returns its result.
        """

    @property
    def failed(self) -> bool:
        """
        Returns true if the action failed.
        (in which case usually exc_info is not None).
        """


class IContext(typing.Protocol):
    def show(
        self, msg: str, end: str = "", kind: str = "", flush: Optional[bool] = None
    ):
        pass

    def show_error(self, msg: str, flush: Optional[bool] = None):
        pass

    @contextmanager
    def register_lifecycle_prints(self) -> Iterator[None]:
        pass


class ICallback(typing.Protocol):
    """
    Note: the actual __call__ must be defined in a subclass protocol.
    """

    def register(self, callback):
        pass

    def unregister(self, callback):
        pass


class IAutoUnregisterContextManager(typing.Protocol):
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class IOnActionFuncFoundCallback(ICallback, typing.Protocol):
    def __call__(self, func: Callable, *args, **kwargs):
        pass

    def register(self, callback: Callable) -> IAutoUnregisterContextManager:
        pass

    def unregister(self, callback: Callable) -> None:
        pass


class IBeforeCollectActionsCallback(ICallback, typing.Protocol):
    def __call__(self, path: Path, action_names: Set[str]):
        pass

    def register(
        self, callback: Callable[[Path, Set[str]], Any]
    ) -> IAutoUnregisterContextManager:
        pass

    def unregister(self, callback: Callable[[Path, Set[str]], Any]) -> None:
        pass


class IAfterCollectActionsCallback(ICallback, typing.Protocol):
    """
    Called after all actions have been collected.
    """

    def __call__(self, actions: List[IAction]):
        pass

    def register(
        self, callback: Callable[[List[IAction]], Any]
    ) -> IAutoUnregisterContextManager:
        pass

    def unregister(self, callback: Callable[[List[IAction]], Any]) -> None:
        pass


IActionCallback = Callable[[IAction], Any]
IActionsCallback = Callable[[Sequence[IAction]], Any]


class IBeforeActionRunCallback(ICallback, typing.Protocol):
    def __call__(self, action: IAction):
        pass

    def register(self, callback: IActionCallback) -> IAutoUnregisterContextManager:
        pass

    def unregister(self, callback: IActionCallback) -> None:
        pass


class IBeforeAllActionsRunCallback(ICallback, typing.Protocol):
    def __call__(self, actions: Sequence[IAction]):
        pass

    def register(self, callback: IActionsCallback) -> IAutoUnregisterContextManager:
        pass

    def unregister(self, callback: Callable[[Sequence[IAction]], Any]) -> None:
        pass


class IAfterAllActionsRunCallback(ICallback, typing.Protocol):
    def __call__(self, actions: Sequence[IAction]):
        pass

    def register(self, callback: IActionsCallback) -> IAutoUnregisterContextManager:
        pass

    def unregister(self, callback: IActionsCallback) -> None:
        pass


class IAfterActionRunCallback(ICallback, typing.Protocol):
    def __call__(self, action: IAction):
        pass

    def register(self, callback: IActionCallback) -> IAutoUnregisterContextManager:
        pass

    def unregister(self, callback: IActionCallback) -> None:
        pass


class ActionsListActionTypedDict(TypedDict):
    """
    When python -m sema4ai.actions list is run, the output is a
    list[ActionsListActionTypedDict].
    """

    name: str
    line: int
    file: str
    docs: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    managed_params_schema: Dict[str, Any]
    options: Optional[Dict]


JSONValue = Union[
    Dict[str, "JSONValue"], List["JSONValue"], str, int, float, bool, None
]
