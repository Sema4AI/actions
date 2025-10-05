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


class NoSecretInActionContextError(Exception):
    """
    Raised when a secret is not found in the action context.
    """


def _decrypt_secret_or_return_plain(var_name: str, data: str) -> str:
    import base64
    import json

    from sema4ai.actions._action_context import _decrypt_from_data_envelope

    try:
        loaded_data = json.loads(base64.b64decode(data.encode("ascii")).decode("utf-8"))
        if isinstance(loaded_data, dict):
            if (
                "cipher" in loaded_data
                and "algorithm" in loaded_data
                and "iv" in loaded_data
                and "auth-tag" in loaded_data
            ):
                found = _decrypt_from_data_envelope(loaded_data, var_name)
                if found is not None:
                    if isinstance(found, str):
                        return found
                    return json.dumps(found)
    except Exception:
        pass  # Unable to decrypt (probably not encrypted in the first place)

    # If we get here, it's not encrypted.
    return data


class _SecretInActionContext(Secret):
    """
    Internal API to wrap a secret which is passed encrypted.
    """

    def __init__(self, action_context: "ActionContext | None", secret_name: str):
        """
        Args:
            action_context: The action context.
            path: the path of the data required inside of the action context
                (a '/' splitted path, for instance: 'secrets/my_passwd')
        """
        if not secret_name:
            raise RuntimeError("A valid secret name must be passed.")

        self._action_context = action_context

        path = f"secrets/{secret_name}"
        self._paths = path.split("/")
        self._env_var_name = secret_name.upper()
        self._request_name = f"x-{secret_name.replace('_', '-')}"

    def __secret_from_env_or_request(self, error_if_not_found: str) -> str:
        """
        If this method is called, it means that the secret is not available in the
        action context.

        This method will try to get the secret from the request headers or from the
        environment variables.
        """
        import os

        from sema4ai.actions._action import get_current_requests_contexts
        from sema4ai.actions._action_context import _is_robocorp_log_available

        ret = None

        current_requests_contexts = get_current_requests_contexts()
        if current_requests_contexts is not None:
            request = current_requests_contexts.request
            if request is not None:
                value = request.headers.get(self._request_name)
                if value:
                    return _decrypt_secret_or_return_plain(self._env_var_name, value)

        value = os.getenv(self._env_var_name)
        if value:
            # Let's see if it's encrypted and decrypt if needed.
            ret = _decrypt_secret_or_return_plain(self._env_var_name, value)

        if ret is not None:
            if _is_robocorp_log_available():
                from robocorp import log

                log.hide_from_output(ret)
                log.hide_from_output(repr(ret))
            return ret

        error_if_not_found = f"{error_if_not_found} (note: also checked env var: {self._env_var_name} and request header: {self._request_name})."
        raise NoSecretInActionContextError(error_if_not_found)

    @property
    def value(self) -> str:
        """
        Provides the actual secret wrapped in this class.
        """
        from robocorp import log

        with log.suppress():
            if self._action_context is None:
                return self.__secret_from_env_or_request(
                    "Unable to get the secret in the action context because it's not available"
                )

            dct = self._action_context.value

            v = None
            for path in self._paths:
                if not isinstance(dct, dict):
                    dct = None  # Remove from context
                    return self.__secret_from_env_or_request(
                        f"Unable to get path: {self._paths} in action context (expected dict to get {path!r} from)"
                    )
                try:
                    dct = v = dct[path]
                except KeyError:
                    dct = None  # Remove from context
                    return self.__secret_from_env_or_request(
                        f"Unable to get path: {self._paths} in action context (current path: {path!r})"
                    )

            dct = None  # Remove from context
            if v is None:
                return self.__secret_from_env_or_request(
                    f"Error. Path ({self._paths}) invalid for the action context"
                )

            if not isinstance(v, str):
                del v
                return self.__secret_from_env_or_request(
                    f"Error. Path ({self._paths}) did not map to a string in the action context"
                )

            return v
