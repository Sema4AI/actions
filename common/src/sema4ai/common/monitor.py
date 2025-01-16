import logging

from sema4ai.common.protocols import ICancelMonitorListener, IMonitor

log = logging.getLogger(__name__)


class Monitor:
    def __init__(self, title: str = ""):
        self._title = title
        self._cancelled: bool = False
        self._listeners: tuple[ICancelMonitorListener, ...] = ()

    def add_cancel_listener(self, listener: ICancelMonitorListener):
        if self._cancelled:
            listener()
        else:
            self._listeners += (listener,)

    def cancel(self) -> None:
        if self._title:
            log.info("Cancelled: %s", self._title)
        self._cancelled = True

        for listener in self._listeners:
            listener()
        self._listeners = ()

    def check_cancelled(self) -> None:
        if self._cancelled:
            from concurrent.futures import CancelledError

            raise CancelledError()

    def is_cancelled(self) -> bool:
        return self._cancelled

    def __typecheckself__(self) -> None:
        from sema4ai.common.protocols import check_implements

        _: IMonitor = check_implements(self)
