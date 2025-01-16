from logging import getLogger

logger = getLogger(__name__)


class OnExitContextManager:
    def __init__(self, on_exit):
        self.on_exit = on_exit

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.on_exit()


class Callback:
    """
    A helper class to register callbacks and call them when notified.

    Example:
        with callback.register(lambda x: print(x)):
            ...
            callback(1) # Will call all callbacks registered passing 1 as argument.

    Note that it's thread safe to register/unregister callbacks while callbacks
    are being notified, but it's not thread-safe to register/unregister at the
    same time in multiple threads.
    """

    def __init__(self, reversed=False, raise_exceptions=False):
        self.raise_exceptions = raise_exceptions
        self._reversed = reversed
        self._callbacks = ()

    def register(self, callback) -> OnExitContextManager:
        """
        Register a callback to be called when the callback is notified.


        Returns:
            An OnExitContextManager which can be used as a context manager to
            automatically unregister the callback when the context manager is
            exited.

        Example:
            with callback.register(lambda: print("Hello, world!")):
                ...
                callback() # Will call all callbacks registered.

        Note: it's not thread safe to register/unregister callbacks in multiple threads
        (a callback may end up not being registered if that's the case).
        """
        self._callbacks = self._callbacks + (callback,)

        # Enable using as a context manager to automatically call the unregister.
        return OnExitContextManager(lambda: self.unregister(callback))

    def unregister(self, callback) -> None:
        self._callbacks = tuple(x for x in self._callbacks if x != callback)

    def __len__(self):
        return len(self._callbacks)

    def __call__(self, *args, **kwargs):
        if self._reversed:
            iter_in = reversed(self._callbacks)
        else:
            iter_in = self._callbacks
        for c in iter_in:
            try:
                c(*args, **kwargs)
            except Exception:
                logger.exception(f"Error calling: {c}.")
                if self.raise_exceptions:
                    raise


__all__ = ["Callback"]
