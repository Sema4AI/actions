import base64
import json
import os
import typing
from typing import Dict, List, Optional

if typing.TYPE_CHECKING:
    from sema4ai.actions._protocols import JSONValue
    from sema4ai.actions._request import Request


def _get_str_list_from_env(env_name: str, env) -> List[str]:
    # Verify if it's an encrypted header.
    in_env: str = env.get(env_name, "")
    if not in_env:
        return []

    try:
        lst_info_to_decrypt = json.loads(in_env)
    except Exception:
        raise RuntimeError(
            f"Error: the {env_name} is expected to be a json list of strings, "
            f"however it cannot be interpreted as json. Found: {in_env}"
        )
    if not isinstance(lst_info_to_decrypt, list):
        raise RuntimeError(
            f"Error: the {env_name} is expected to be a json list (of strings). "
            f"Found: {lst_info_to_decrypt}."
        )

    for entry in lst_info_to_decrypt:
        if not isinstance(entry, str):
            raise RuntimeError(
                f"Error: the {env_name} is expected to be a json list containing "
                f"only strings. Found: {lst_info_to_decrypt}."
            )

    return lst_info_to_decrypt


def _decrypt(key: bytes, iv: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
    ).decryptor()

    return decryptor.update(ciphertext) + decryptor.finalize()


def _is_robocorp_log_available():
    # When frozen it can't really be used.
    import sys

    if getattr(sys, "frozen", False):
        return False

    if not hasattr(os, "__file__"):
        return False

    return True


class BaseContext:
    """
    This is data received as input which may or may not be encrypted.

    When a user requests the actual value, it'll be decrypted if that's the case.
    """

    _encrypted: bool

    def __init__(self, data: str, env: Optional[Dict[str, str]] = None):
        """
        Args:
            data: The data requested from that source.
                If encrypted, must be something as:

                base64(json.dumps({
                   cipher: blob_of_data
                   algorithm: "aes256-gcm"
                   iv: nonce
                }))

                Otherwise the payload should be passed directly,
                which should be something as:
                    base64(json.dumps({
                      'secrets': {'secret_name': 'secret_value'}
                    }))

            path: the payload is expected to be a json object, and the
                path defined here maps to how to get that value.

                i.e.: if the payload has:

                {
                  'secrets': {'secret_name': 'secret_value'},
                  'invocation_context': {
                    'workroom_base_url': str | None,
                    'agent_id': str | None,
                    'invoked_on_behalf_of_user_id': str | None,
                    'thread_id': str | None,
                    'tenant_id': str,
                  },
                }

                The path to access the secret_name would be:
                'secrets/secret_name'.

        """
        self._env = env
        self._initial_data = data
        loaded_data = json.loads(base64.b64decode(data.encode("ascii")).decode("utf-8"))
        if not isinstance(loaded_data, dict):
            raise RuntimeError(
                f"Expected {self._header_name()} header to have json contents."
            )

        # Ok, we have the basic info, now, this info may be encrypted or not
        # (if it's encrypted we have 'cipher', 'algorithm' and 'iv', otherwise
        # we have the raw info directly -- such as 'secrets').
        if (
            "cipher" in loaded_data
            and "algorithm" in loaded_data
            and "iv" in loaded_data
        ):
            self._encrypted = True
            self._encrypted_data: Dict[str, "JSONValue"] = loaded_data
        else:
            self._encrypted = False
            self._raw_data: Dict[str, "JSONValue"] = loaded_data
            self._hide_secrets()

    @property
    def initial_data(self) -> str:
        """
        The initial data received from the request (x-action-context header).
        """
        return self._initial_data

    @property
    def value(self) -> "JSONValue":
        from typing import Any

        # Data already decrypted
        try:
            return self._raw_data
        except AttributeError:
            pass

        if not self._encrypted:
            raise RuntimeError("Expected data to be encrypted if it reached here!")

        ctx: Any
        if _is_robocorp_log_available():
            from robocorp import log

            ctx = log.suppress()
        else:
            from contextlib import nullcontext

            ctx = nullcontext()

        with ctx:
            keys = _get_str_list_from_env(
                "ACTION_SERVER_DECRYPT_KEYS", env=self._env or os.environ
            )

            if not keys:
                raise RuntimeError(
                    f"The information in the {self._header_name()} seems to be encrypted, but decryption keys are not available in ACTION_SERVER_DECRYPT_KEYS."
                )

            cipher = self._encrypted_data["cipher"]
            algorithm = self._encrypted_data["algorithm"]
            iv = self._encrypted_data["iv"]
            auth_tag = self._encrypted_data["auth-tag"]

            if not isinstance(cipher, str):
                raise RuntimeError(
                    f"Expected the cipher to be a str. Found: {cipher!r}"
                )

            if not isinstance(algorithm, str):
                raise RuntimeError(
                    f"Expected the algorithm to be a str. Found: {algorithm!r}"
                )

            if not isinstance(iv, str):
                raise RuntimeError(f"Expected the iv to be a str. Found: {iv!r}")

            if not isinstance(auth_tag, str):
                raise RuntimeError(
                    f"Expected the auth-tag to be a str. Found: {auth_tag!r}"
                )

            try:
                cipher_decoded_base_64: bytes = base64.b64decode(cipher)
            except Exception:
                raise RuntimeError(
                    f"Unable to decode the 'cipher' field passed to {self._header_name()} as base64."
                )

            try:
                iv_decoded_base_64: bytes = base64.b64decode(iv)
            except Exception:
                raise RuntimeError(
                    f"Unable to decode the 'iv' field passed to {self._header_name()} as base64."
                )

            try:
                auth_tag_decoded_base_64 = base64.b64decode(auth_tag)
            except Exception:
                raise RuntimeError(
                    f"Unable to decode the 'auth-tag' field passed to {self._header_name()} as base64."
                )

            if algorithm != "aes256-gcm":
                raise RuntimeError(
                    f"Unable to recognize {self._header_name()} encryption algorithm: {algorithm}"
                )

            for key in keys:
                k: bytes = base64.b64decode(key.encode("ascii"))
                try:
                    raw_data = _decrypt(
                        k,
                        iv_decoded_base_64,
                        cipher_decoded_base_64,
                        auth_tag_decoded_base_64,
                    )
                    break
                except Exception:
                    continue
            else:
                raise RuntimeError(
                    f"It was not possible to decode the {self._header_name()} header with any of the available keys."
                )

            self._raw_data = json.loads(raw_data)
            self._hide_secrets()

        return self._raw_data

    def _hide_secrets(self):
        """
        Subclasses can implement this method to hide sensitive data.
        """

    @classmethod
    def _header_name(cls) -> str:
        raise NotImplementedError("Subclasses should implement this method.")

    @classmethod
    def from_request(cls, request: Optional["Request"]) -> Optional["BaseContext"]:
        if not request:
            return None
        data = request.headers.get(cls._header_name())
        if data is None:
            return None
        return cls(data)


class ActionContext(BaseContext):
    @classmethod
    def _header_name(cls) -> str:
        return "x-action-context"

    def _hide_secrets(self):
        secrets = self._raw_data.get("secrets")
        if secrets and isinstance(secrets, dict):
            if _is_robocorp_log_available():
                from robocorp import log

                for secret_value in secrets.values():
                    if isinstance(secret_value, str):
                        log.hide_from_output(secret_value)
                        log.hide_from_output(repr(secret_value))


class DataContext(BaseContext):
    @classmethod
    def _header_name(cls) -> str:
        return "x-data-context"

    def _hide_secrets(self):
        data_server_config = self._raw_data.get("data-server")
        if data_server_config and isinstance(data_server_config, dict):
            if _is_robocorp_log_available():
                from robocorp import log

                if isinstance(data_server_config, dict):
                    secret_value = data_server_config.get("password")
                    if isinstance(secret_value, str):
                        log.hide_from_output(secret_value)
                        log.hide_from_output(repr(secret_value))


class InvocationContext(BaseContext):
    @classmethod
    def _header_name(cls) -> str:
        return "x-action-invocation-context"


class RequestContexts:
    def __init__(self, request: Optional["Request"]):
        self._request = request
        self._data_context: Optional[DataContext] = None
        self._action_context: Optional[ActionContext] = None
        self._invocation_context: Optional[InvocationContext] = None

    @property
    def data_context(self) -> Optional[DataContext]:
        if self._data_context is None and self._request is not None:
            self._data_context = typing.cast(
                DataContext, DataContext.from_request(self._request)
            )
        return self._data_context

    @property
    def action_context(self) -> Optional[ActionContext]:
        if self._action_context is None and self._request is not None:
            self._action_context = typing.cast(
                ActionContext, ActionContext.from_request(self._request)
            )
        return self._action_context

    @property
    def invocation_context(self) -> Optional[InvocationContext]:
        if self._invocation_context is None and self._request is not None:
            self._invocation_context = typing.cast(
                InvocationContext, InvocationContext.from_request(self._request)
            )
        return self._invocation_context
