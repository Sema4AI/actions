import typing
from typing import Any, Callable, Dict, List, Sequence, Union

from sema4ai.tasks import ITask as _ITask
from sema4ai.tasks import Status as _Status
from sema4ai.tasks._protocols import TasksListTaskTypedDict


class IAction(_ITask, typing.Protocol):
    pass


Status = _Status

IActionCallback = Callable[[IAction], Any]
IActionsCallback = Callable[[Sequence[IAction]], Any]


class ActionsListActionTypedDict(TasksListTaskTypedDict):
    pass


JSONValue = Union[
    Dict[str, "JSONValue"], List["JSONValue"], str, int, float, bool, None
]
