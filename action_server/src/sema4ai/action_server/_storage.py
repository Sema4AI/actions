import base64
import os
import typing
from functools import lru_cache
from logging import getLogger
from pathlib import Path

from pydantic.main import BaseModel

from sema4ai.action_server._settings import (
    get_default_settings_dir,
    get_user_sema4_path,
)

log = getLogger(__name__)

STORAGE_FILE_NAME = "action_server_storage.json"

KEY_FILE_NAME = ".storage.key"
KEY_FILE_PERMISSIONS = 0o600

AES_KEY_LEN = 32

DEFAULT_CR_HOSTNAME = "https://us1.robocorp.com"


class StorageEncryptedValue(BaseModel):
    value: str
    iv: str
    tag: str


class StorageCloud(BaseModel):
    hostname: str
    access_credentials: StorageEncryptedValue


class Storage(BaseModel):
    cloud: StorageCloud


@lru_cache
def get_storage_path() -> Path:
    return get_default_settings_dir() / STORAGE_FILE_NAME


@lru_cache
def get_key_file_path() -> Path:
    return get_user_sema4_path() / KEY_FILE_NAME


@lru_cache
def get_key() -> bytes:
    key_file_path = get_key_file_path()
    if key_file_path.exists():
        if key_file_path.is_file():
            if key_file_path.stat().st_size == AES_KEY_LEN:
                with open(key_file_path, "rb") as f:
                    return f.read()
            log.warning("Invalid key file found, recreating the key")
            key_file_path.unlink()
        else:
            log.error(
                f"Found key file as directory, trying to remove it: {str(key_file_path)}"
            )
            key_file_path.rmdir()

    key = os.urandom(AES_KEY_LEN)
    with open(key_file_path, "wb") as f:
        f.write(key)
    key_file_path.chmod(KEY_FILE_PERMISSIONS)
    return key


def encrypt_value(value: str) -> StorageEncryptedValue:
    from sema4ai.action_server._encryption import encrypt

    key = get_key()

    iv, encrypted_value, tag = encrypt(key, value.encode("utf-8"))

    b64_iv = base64.b64encode(iv).decode("utf-8")
    b64_value = base64.b64encode(encrypted_value).decode("utf-8")
    b64_tag = base64.b64encode(tag).decode("utf-8")

    return StorageEncryptedValue(iv=b64_iv, tag=b64_tag, value=b64_value)


def decrypt_value(encrypted_value: StorageEncryptedValue) -> str:
    from sema4ai.action_server._encryption import decrypt

    key = get_key()

    iv = base64.b64decode(encrypted_value.iv)
    tag = base64.b64decode(encrypted_value.tag)
    value = base64.b64decode(encrypted_value.value)

    decrypted_value = decrypt(key, iv, value, tag)

    return decrypted_value.decode("utf-8")


@lru_cache
def load_storage() -> typing.Optional[Storage]:
    """
    Load the storage from a file.

    Returns:
        File read error.
    """
    storage_file_path = get_storage_path()

    if not storage_file_path.exists():
        return None

    with open(storage_file_path, "r") as f:
        contents = f.read()
    try:
        return Storage.model_validate_json(contents)
    except ValueError:
        storage_file_path.unlink()
        raise Exception("Invalid storage file removed")


def save_storage(storage: Storage):
    """
    Save the storage to a file and reset the load_cache.

    Args:
        Storage contents.

    Throws:
        File write error.
    """
    storage_file_path = get_storage_path()

    with open(storage_file_path, "w") as f:
        f.write(storage.model_dump_json())
    load_storage.cache_clear()


def get_access_credentials() -> typing.Optional[str]:
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    try:
        storage = load_storage()
        if not storage:
            return None
        return decrypt_value(storage.cloud.access_credentials)
    except Exception as e:
        log.error(bold_red(f"Failed to get stored access credentials\n{e}"))
        raise Exception(
            f"Unable to decrypt the values in storage, please remove: {get_storage_path()}"
        )


def get_hostname() -> str:
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    try:
        storage = load_storage()
        if not storage:
            return DEFAULT_CR_HOSTNAME
        hostname = storage.cloud.hostname
    except Exception as e:
        log.error(bold_red(f"Failed to get stored hostname\n{e}"))

    return hostname if hostname else DEFAULT_CR_HOSTNAME


def store(access_credentials: str, hostname: str) -> None:
    """
    Save the cloud storage to a file and reset the load_cache.

    Args:
        access_credentials: Action Server Control Room access credentials
        hostname: Action Server Control Room hostname

    Throws:
        File write error.
    """
    storage_cloud = StorageCloud(
        access_credentials=encrypt_value(access_credentials), hostname=hostname
    )
    storage = Storage(cloud=storage_cloud)
    save_storage(storage)
