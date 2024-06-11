import base64
import json
import os
from typing import Any, Dict, List, Optional

from sema4ai.actions._protocols import JSONValue


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


def decrypt(key: bytes, iv: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
    ).decryptor()

    return decryptor.update(ciphertext) + decryptor.finalize()


def get_encryption_keys(env: Optional[dict[str, str]] = None) -> tuple[bytes, ...]:
    """
    Args:
        env: The environment to be used.

    Returns:
        A tuple with the keys which should be used for encryption.
    """
    keys = _get_str_list_from_env("ACTION_SERVER_DECRYPT_KEYS", env=env or os.environ)
    return tuple(base64.b64decode(key.encode("ascii")) for key in keys)


def make_unencrypted_data_envelope(data: Any) -> str:
    """
    Our envelope in this case is a base64(json(data))
    """
    action_server_context: str = json.dumps(data)
    return base64.b64encode(action_server_context.encode("utf-8")).decode("ascii")


def encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    # Generate a random 96-bit IV.
    iv = os.urandom(12)

    # Construct an AES-GCM Cipher object with the given key and a
    # randomly generated IV.
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
    ).encryptor()

    # Encrypt the plaintext and get the associated ciphertext.
    # GCM does not require padding.
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    return (iv, ciphertext, encryptor.tag)


def make_encrypted_data_envelope(key: bytes, secrets: Any) -> str:
    """
    Our envelope in this case is a base64(json(encrypted-envelope(json(data))))
    """

    data: bytes = json.dumps(secrets).encode("utf-8")
    iv, encrypted_data, tag = encrypt(key, data)

    action_server_context = {
        "cipher": base64.b64encode(encrypted_data).decode("ascii"),
        "algorithm": "aes256-gcm",
        "iv": base64.b64encode(iv).decode("ascii"),
        "auth-tag": base64.b64encode(tag).decode("ascii"),
    }

    ret: str = base64.b64encode(
        json.dumps(action_server_context).encode("utf-8")
    ).decode("ascii")
    return ret


class MaybeEncryptedJsonData:
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
                  'secrets': {'secret_name': 'secret_value'}
                }

                The path to access the secret_name would be:
                'secrets/secret_name'.

        """
        self._env = env
        loaded_data = json.loads(base64.b64decode(data.encode("ascii")).decode("utf-8"))
        if not isinstance(loaded_data, dict):
            raise RuntimeError("Expected data to have json content object as root.")

        # Ok, we have the basic info, now, this info may be encrypted or not
        # (if it's encrypted we have 'cipher', 'algorithm' and 'iv', otherwise
        # we have the raw info directly -- such as 'secrets').
        if (
            "cipher" in loaded_data
            and "algorithm" in loaded_data
            and "iv" in loaded_data
        ):
            self._encrypted = True
            self._encrypted_data: Dict[str, JSONValue] = loaded_data
        else:
            self._encrypted = False
            self._raw_data: Dict[str, JSONValue] = loaded_data

    @property
    def encrypted(self) -> bool:
        return self._encrypted

    @property
    def value(self) -> JSONValue:
        # Data already decrypted
        try:
            return self._raw_data
        except AttributeError:
            pass

        if not self._encrypted:
            raise RuntimeError("Expected data to be encrypted if it reached here!")

        keys: tuple[bytes, ...] = get_encryption_keys(env=self._env)

        if not keys:
            raise RuntimeError(
                "The data seems to be encrypted, but decryption keys are not available in ACTION_SERVER_DECRYPT_KEYS."
            )

        cipher = self._encrypted_data["cipher"]
        algorithm = self._encrypted_data["algorithm"]
        iv = self._encrypted_data["iv"]
        auth_tag = self._encrypted_data["auth-tag"]

        if not isinstance(cipher, str):
            raise RuntimeError(f"Expected the cipher to be a str. Found: {cipher!r}")

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
            raise RuntimeError("Unable to decode the 'cipher' field passed as base64.")

        try:
            iv_decoded_base_64: bytes = base64.b64decode(iv)
        except Exception:
            raise RuntimeError("Unable to decode the 'iv' field passed as base64.")

        try:
            auth_tag_decoded_base_64 = base64.b64decode(auth_tag)
        except Exception:
            raise RuntimeError(
                "Unable to decode the 'auth-tag' field passed as base64."
            )

        if algorithm != "aes256-gcm":
            raise RuntimeError(f"Unable to recognize encryption algorithm: {algorithm}")

        for key in keys:
            try:
                raw_data = decrypt(
                    key,
                    iv_decoded_base_64,
                    cipher_decoded_base_64,
                    auth_tag_decoded_base_64,
                )
                break
            except Exception:
                continue
        else:
            raise RuntimeError(
                "It was not possible to decode the data with any of the available keys."
            )

        return json.loads(raw_data)
