import typing

from sema4ai.actions._secret import Secret

if typing.TYPE_CHECKING:
    from sema4ai.actions._action_context import ActionContext


class _RawSecret(Secret):
    """
    Internal API to wrap a secret which is not passed encrypted.
    """

    def __init__(self, value: str):
        """
        Args:
            value: The secret value to be wrapped in this class (note that
                it's automatically hidden in the logs).
        """
        from robocorp import log

        log.hide_from_output(value)
        log.hide_from_output(repr(value))
        self.__value = value

    @property
    def value(self) -> str:
        """
        Provides the actual secret wrapped in this class.
        """
        return self.__value


class _SecretInActionContext(Secret):
    """
    Internal API to wrap a secret which is passed encrypted.
    """

    def __init__(self, action_context: "ActionContext", path: str):
        """
        Args:
            action_context: The action context.
            path: the path of the data required inside of the action context
                (a '/' splitted path, for instance: 'secrets/my_passwd')
        """
        if not path:
            raise RuntimeError("A valid path must be passed.")

        self._action_context = action_context
        self._paths = path.split("/")

    @property
    def value(self) -> str:
        """
        Provides the actual secret wrapped in this class.
        """
        from robocorp import log

        with log.suppress():
            dct = self._action_context.value

            v = None
            for path in self._paths:
                if not isinstance(dct, dict):
                    dct = None  # Remove from context
                    raise RuntimeError(
                        f"Unable to get path: {self._paths} in action context (expected dict to get {path!r} from)."
                    )
                try:
                    dct = v = dct[path]
                except KeyError:
                    dct = None  # Remove from context
                    raise RuntimeError(
                        f"Unable to get path: {self._paths} in action context (current path: {path!r})."
                    )

            dct = None  # Remove from context
            if v is None:
                raise RuntimeError(
                    f"Error. Path ({self._paths}) invalid for the action context."
                )

            if not isinstance(v, str):
                del v
                raise RuntimeError(
                    f"Error. Path ({self._paths}) did not map to a string in the action context."
                )

            return v
