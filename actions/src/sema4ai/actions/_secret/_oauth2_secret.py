from typing import Any, Optional

from sema4ai.actions._action_context import ActionContext
from sema4ai.actions._secret import JSONValue, OAuth2Secret, ProviderT, ScopesT


class _BaseInternalOAuth2Secret(OAuth2Secret):
    def __init__(
        self,
        provider: ProviderT,
        scopes: ScopesT,
        access_token: str,
        metadata: JSONValue = None,
    ):
        self._provider = provider
        self._scopes = scopes
        self._access_token = access_token
        self._metadata = metadata

        from robocorp import log

        log.hide_from_output(access_token)
        log.hide_from_output(repr(access_token))

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def scopes(self) -> list[str]:
        return self._scopes

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def metadata(self) -> JSONValue:
        return self._metadata


class _OAuth2SecretInActionContext(_BaseInternalOAuth2Secret):
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

    def _get_dict_in_action_context(self) -> dict:
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

            if not isinstance(v, dict):
                del v
                raise RuntimeError(
                    f"Error. Path ({self._paths}) did not map to a dict in the action context."
                )

            return v

    @property
    def access_token(self) -> str:
        """
        Provides the actual access_token wrapped in this class.
        """
        from robocorp import log

        with log.suppress():
            dct = self._get_dict_in_action_context()
            ret = dct["access_token"]
            log.hide_from_output(ret)
            log.hide_from_output(repr(ret))
            return ret

    @property
    def provider(self) -> str:
        """
        Provides the actual provider wrapped in this class.
        """
        from robocorp import log

        with log.suppress():
            dct = self._get_dict_in_action_context()
            return dct["provider"]

    @property
    def scopes(self) -> list[str]:
        """
        Provides the actual scopes wrapped in this class.
        """
        from robocorp import log

        with log.suppress():
            dct = self._get_dict_in_action_context()
            return dct["scopes"]

    @property
    def metadata(self) -> Optional[Any]:
        """
        Provides the actual metadata wrapped in this class.
        """
        from robocorp import log

        with log.suppress():
            dct = self._get_dict_in_action_context()
            return dct.get("metadata")


class _RawOauth2Secret(_BaseInternalOAuth2Secret):
    """
    Internal API to wrap a secret which is not passed encrypted.
    """

    def __init__(self, value: dict):
        """
        Args:
            value: A dict with the values meant to be wrapped in this class.
        """

        access_token = value.get("access_token")
        if not access_token:
            raise KeyError(
                "Error. The `access_token` key is required to build an OAuth2Secret, but it wasn't passed."
            )
        provider = value.get("provider")
        if not provider:
            raise KeyError(
                "Error. The `provider` key is required to build an OAuth2Secret, but it wasn't passed."
            )
        scopes = value.get("scopes")
        if not scopes:
            raise KeyError(
                "Error. The `scopes` key is required to build an OAuth2Secret, but it wasn't passed."
            )

        metadata = value.get("metadata")  # This is optional
        super().__init__(provider, scopes, access_token, metadata)
