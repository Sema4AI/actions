from typing import Any, Callable, Dict, List, Sequence, Union

from sema4ai.tasks import IAction
from sema4ai.tasks import Status as _Status
from sema4ai.tasks._protocols import (
    ActionsListActionTypedDict as _ActionsListActionTypedDict,
)

ActionsListActionTypedDict = _ActionsListActionTypedDict

Status = _Status

IActionCallback = Callable[[IAction], Any]
IActionsCallback = Callable[[Sequence[IAction]], Any]


JSONValue = Union[
    Dict[str, "JSONValue"], List["JSONValue"], str, int, float, bool, None
]
