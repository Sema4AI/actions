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
        from sema4ai.actions._action import get_provider_and_scope_from_annotation_args
        from sema4ai.actions._variables_scope import (
            get_validate_and_convert_kwargs_scope,
        )

        access_token = value.get("access_token")
        if not access_token:
            raise KeyError(
                "Error. The `access_token` key is required to build an OAuth2Secret, but it wasn't passed."
            )

        validate_and_convert_scope = get_validate_and_convert_kwargs_scope()

        provider = value.get("provider")
        scopes = value.get("scopes")
        if not scopes or not provider:
            if validate_and_convert_scope is not None:
                from typing import get_args

                # Use default values from the type hints.
                args = get_args(validate_and_convert_scope.param_type)
                (
                    provider_from_args,
                    scopes_from_args,
                ) = get_provider_and_scope_from_annotation_args(
                    args, "<unavailable>", "<unavailable>"
                )

                if not provider:
                    provider = provider_from_args

                if not scopes:
                    scopes = scopes_from_args

        metadata = value.get("metadata")  # This is optional
        super().__init__(
            provider or "<unavailable>", scopes or [], access_token, metadata
        )
