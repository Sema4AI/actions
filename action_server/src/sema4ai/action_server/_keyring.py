import sys
import typing
from logging import getLogger

import keyring
from keyring.backends import Windows

# By default in Windows and MacOS the keyring backend is not loaded
# https://github.com/jaraco/keyring/issues/359
if sys.platform == "win32":
    keyring.set_keyring(Windows.WinVaultKeyring())
elif sys.platform == "darwin":
    keyring.core.set_keyring(
        keyring.core.load_keyring("keyring.backends.macOS.Keyring")
    )

log = getLogger(__name__)


DEFAULT_CR_HOSTNAME = "https://us1.robocorp.com"

KEYRING_SERVICE_NAME = "ACTION_SERVER_LOGIN"
KEYRING_KEY_HOSTNAME = "hostname"
KEYRING_KEY_ACCESS_CREDENTIALS = "access-credentials"


def get_access_credentials() -> typing.Optional[str]:
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    try:
        return keyring.get_password(
            KEYRING_SERVICE_NAME, KEYRING_KEY_ACCESS_CREDENTIALS
        )
    except Exception as e:
        log.error(bold_red(f"Failed to get stored access credentials {e}"))

    return None


def get_hostname() -> str:
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    try:
        hostname = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_KEY_HOSTNAME)
    except Exception as e:
        log.error(bold_red(f"Failed to get stored access credentials {e}"))

    return hostname if hostname else DEFAULT_CR_HOSTNAME


def store_access_credentials(access_credentials: str) -> None:
    keyring.set_password(
        KEYRING_SERVICE_NAME, KEYRING_KEY_ACCESS_CREDENTIALS, access_credentials
    )


def store_hostname(hostname: str) -> None:
    keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_KEY_HOSTNAME, hostname)
