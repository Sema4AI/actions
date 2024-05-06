import logging
import typing
from typing import Literal, TypedDict

from fastapi.routing import APIRouter
from pydantic.main import BaseModel

if typing.TYPE_CHECKING:
    from sema4ai.action_server._models import Action, ActionPackage

log = logging.getLogger(__name__)

secrets_api_router = APIRouter(prefix="/api/secrets")


ActionPackageScopeTypedDict = TypedDict(
    "ActionPackageScopeTypedDict", {"action-package": str}
)


class InMemorySecrets:
    """
    A helper class which allows keeping secrets in memory and can later be used
    to update the x-action-context header with those secrets.
    """

    def __init__(self) -> None:
        self._global_scope_secrets: dict[str, str] = {}
        self._action_package_scope_secrets: dict[str, dict[str, str]] = {}

    def update_headers(
        self, action_package: "ActionPackage", action: "Action", headers: dict[str, str]
    ):
        from sema4ai.action_server._encryption import (
            get_encryption_keys,
            make_encrypted_data_envelope,
            make_unencrypted_data_envelope,
        )

        secrets: dict[str, str] = {}
        if self._global_scope_secrets:
            secrets.update(self._global_scope_secrets)

        if self._action_package_scope_secrets.get(action_package.name):
            secrets.update(self._action_package_scope_secrets[action_package.name])

        if secrets:
            # Ok, we do have secrets. This means we have to pass them in the x-action-context
            # header. If it's present we don't do anything besides logging (because the
            # caller should've already set the secrets).
            for k in headers:
                if k.lower() == "x-action-context":
                    log.info(
                        "/api/secrets were set but are not being used because 'x-action-context' header is already set in the request."
                    )
                    return headers

            # No x-action-context, let's create it now.
            keys: tuple[bytes, ...] = get_encryption_keys()
            headers = headers.copy()
            if not keys:
                # No encryption is being used
                headers["x-action-context"] = make_unencrypted_data_envelope(
                    {"secrets": secrets}
                )
            else:
                headers["x-action-context"] = make_encrypted_data_envelope(
                    keys[0], {"secrets": secrets}
                )

        return headers

    def _update_secrets(
        self,
        secrets: dict[str, str],
        scope: Literal["global"] | ActionPackageScopeTypedDict,
    ):
        if scope == "global":
            # Note: resets previous values
            self._global_scope_secrets = secrets

        elif isinstance(scope, dict) and scope.get("action-package"):
            # Note: resets previous values for the action package
            self._action_package_scope_secrets[scope["action-package"]] = secrets

        else:
            raise ValueError(
                f"Cannot recognize to which scope the secrets are related to (received scope: {scope})"
            )


IN_MEMORY_SECRETS = InMemorySecrets()


class SetSecretData(BaseModel):
    data: str


@secrets_api_router.post("")
async def set_secrets(data: SetSecretData) -> str:
    """
    API to set secrets in memory which will later be passed on to actions when they're run
    (those are later passed using the x-action-context -- it's meant to be
    used in cases where a process is managing the action server but is not intercepting
    requests to set the x-action-context as would be needed to set the secrets).

    Args:
        data: The data to be set as secrets. Note that it's expected to be passed in the
        same way that the x-action-context is passed (note that it can be encrypted or not).

    returns:
        'ok' string if it worked (if it didn't work an exception is thrown with an error message).
    """
    from sema4ai.action_server._encryption import MaybeEncryptedJsonData

    encrypted_data = MaybeEncryptedJsonData(data.data)
    value = encrypted_data.value
    if not isinstance(value, dict):
        raise ValueError(
            f"Expected the data to be a base64 mapping to a json(dict). Found: {type(value)}"
        )

    secrets = value.get("secrets")
    scope = value.get("scope")
    if not secrets:
        raise ValueError("Expected that the received data would have a 'secrets' key.")
    if not scope:
        raise ValueError("Expected that the received data would have a 'scope' key.")

    if not isinstance(secrets, dict):
        raise ValueError("Expected the received secrets to be a dict.")

    for k, v in secrets.items():
        if not isinstance(k, str):
            raise ValueError("Expected the received secrets keys to be strings.")

        if not isinstance(v, str):
            raise ValueError("Expected the received secrets values to be strings.")

    IN_MEMORY_SECRETS._update_secrets(
        typing.cast(dict[str, str], secrets),
        typing.cast(Literal["global"] | ActionPackageScopeTypedDict, scope),
    )
    return "ok"
