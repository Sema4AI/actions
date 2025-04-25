import logging
import os
import ssl
import sys
import typing
from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property, lru_cache
from pathlib import Path
from typing import NamedTuple

import urllib3

from sema4ai_http.types import NetworkConfigType

_DEFAULT_LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    import ssl

    from sema4ai_http.types import ProfileType

_TYPE_BODY = typing.Union[bytes, typing.IO[typing.Any], typing.Iterable[bytes], str]

__version__ = "2.0.1"


class _SSLContextFactory:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def build_ssl_context(
        self,
        protocol: int | None,
        enable_legacy_server_connect: bool | None = None,
    ) -> ssl.SSLContext:
        import truststore

        protocol = ssl.PROTOCOL_TLS_CLIENT if protocol is None else protocol
        ssl_context = truststore.SSLContext(protocol)

        self._configure_ssl_verification(ssl_context)

        if enable_legacy_server_connect:
            self._configure_tls_renegociation(ssl_context)

        return ssl_context

    def _configure_ssl_verification(self, ssl_context: ssl.SSLContext) -> None:
        disable_ssl = self.config.get("disable-ssl", False)
        ssl_context.verify_mode = ssl.CERT_NONE if disable_ssl else ssl.CERT_REQUIRED

    def _configure_tls_renegociation(self, ssl_context: ssl.SSLContext) -> None:
        if sys.version_info < (3, 12):
            _SSL_LEGACY_SERVER_CONNECT = 0x4
        else:
            _SSL_LEGACY_SERVER_CONNECT = ssl.OP_LEGACY_SERVER_CONNECT
        ssl_context.options |= _SSL_LEGACY_SERVER_CONNECT


class _NetworkConfig:
    def __init__(self) -> None:
        self.connection_pool = self._build_connection_pool()

    @cached_property
    def profile_config(self) -> "ProfileType":
        config_file = self._get_network_settings_path()

        if not config_file.exists():
            return {}

        import yaml

        try:
            config_content = config_file.read_text()
        except Exception as e:
            _DEFAULT_LOGGER.error(
                f"Failed to read configuration file {config_file}: {e}"
            )
            return {}

        try:
            config = typing.cast(NetworkConfigType, yaml.safe_load(config_content))
        except yaml.YAMLError as e:
            _DEFAULT_LOGGER.error(f"Failed to parse YAML from {config_file}: {e}")
            return {}

        if not isinstance(config, dict):
            _DEFAULT_LOGGER.error(
                f"Invalid configuration format in {config_file}, expected a dictionary."
            )
            return {}

        current_profile = config.get("current-profile", "")
        profiles = config.get("profiles", [])  # type: list[ProfileType]

        for profile in profiles:
            if not isinstance(profile, dict):
                _DEFAULT_LOGGER.warning(
                    "Ignoring invalid profile entry, expected a dictionary."
                )
                continue

            if profile.get("name") == current_profile:
                return profile

        _DEFAULT_LOGGER.error(f"No matching profile found for '{current_profile}'.")
        return {}

    @staticmethod
    def _get_network_settings_path() -> Path:
        if sys.platform == "win32":
            localappdata = os.environ.get("LOCALAPPDATA")
            if not localappdata:
                raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
            sema4_home = Path(localappdata) / "sema4ai"
        else:
            # Linux/Mac
            sema4_home = Path("~/.sema4ai").expanduser()

        return sema4_home / "network-settings.yaml"

    def get_ssl_context(self) -> ssl.SSLContext:
        return _SSLContextFactory(self.profile_config).build_ssl_context(
            ssl.PROTOCOL_TLS_CLIENT
        )

    # TODO: add support for no-proxy setting
    def _build_connection_pool(self) -> urllib3.PoolManager | urllib3.ProxyManager:
        ssl_context = self.get_ssl_context()

        if "proxy-settings" in self.profile_config:
            proxy_settings = self.profile_config["proxy-settings"]
            self.connection_pool = urllib3.ProxyManager(
                proxy_url=proxy_settings.get("https-proxy")
                or proxy_settings.get("http-proxy"),
                ssl_context=ssl_context,
            )
        else:
            self.connection_pool = urllib3.PoolManager(ssl_context=ssl_context)

        return self.connection_pool


@lru_cache
def _get_connection_manager() -> urllib3.PoolManager | urllib3.ProxyManager:
    return _NetworkConfig().connection_pool


def build_ssl_context(
    protocol: int | None = None, *, enable_legacy_server_connect: bool | None = None
) -> "ssl.SSLContext":
    return _SSLContextFactory({}).build_ssl_context(
        protocol, enable_legacy_server_connect
    )


@dataclass(slots=True)
class ProxyConfig:
    http: list[str]
    https: list[str]
    no_proxy: list[str]

    @classmethod
    def from_network_config(cls, network_config: _NetworkConfig) -> "ProxyConfig":
        def _parse_proxy_value(value: str | None) -> list[str]:
            return [v.strip() for v in value.split(",")] if value else []

        if proxy_settings := network_config.profile_config.get("proxy-settings"):
            http_proxy = _parse_proxy_value(proxy_settings.get("http-proxy"))
            https_proxy = _parse_proxy_value(proxy_settings.get("https-proxy"))
            no_proxy = _parse_proxy_value(proxy_settings.get("no_proxy"))
        else:
            http_proxy = []
            https_proxy = []
            no_proxy = []

        return cls(http=http_proxy, https=https_proxy, no_proxy=no_proxy)


@dataclass(slots=True)
class NetworkProfile:
    ssl_context: ssl.SSLContext | None
    proxy_config: ProxyConfig

    @classmethod
    def from_network_config(cls, network_config: _NetworkConfig) -> "NetworkProfile":
        return cls(
            ssl_context=network_config.get_ssl_context(),
            proxy_config=ProxyConfig.from_network_config(network_config),
        )


def get_network_profile() -> NetworkProfile:
    return NetworkProfile.from_network_config(_NetworkConfig())


class ResponseWrapper:
    """
    A wrapper around urllib3's BaseHTTPResponse to provide a more user-friendly API.
    All attributes of the BaseHTTPResponse are available via the response property or
    from the reponse itself.
    """

    def __init__(self, response: urllib3.BaseHTTPResponse) -> None:
        self.response = response

    def __getattr__(self, item):
        return getattr(self.response, item)

    @property
    def status(self) -> int:
        return self.response.status

    @property
    def status_code(self) -> int:
        return self.response.status

    @property
    def text(self) -> str:
        charset = "utf-8"
        content_type = self.response.headers.get("content-type", "")
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].strip()
        return self.response.data.decode(charset, errors="replace")

    def raise_for_status(self) -> None:
        if self.response.status >= 400:
            raise urllib3.exceptions.HTTPError(
                f"HTTP {self.response.status}: {self.response.reason}"
            )

    def ok(self) -> bool:
        return 200 <= self.response.status < 400


class DownloadStatus(Enum):
    """Status"""

    DONE = auto()
    PARTIAL = auto()
    ALREADY_EXISTS = auto()
    HTTP_ERROR = auto()


def get(
    url,
    /,
    body: _TYPE_BODY | None = None,
    fields: typing.Any | None = None,
    headers: typing.Mapping[str, str] | None = None,
    json: typing.Any | None = None,
    **urlopen_kw: typing.Any,
) -> ResponseWrapper:
    """
    Perform a GET request using urllib3.

    It utilizes PoolManager or ProxyManager depending on the network settings
    defined in `$HOME/.sema4ai/network-settings.yaml`.
    """
    return ResponseWrapper(
        _get_connection_manager().request(
            "get",
            url,
            body=body,
            fields=fields,
            headers=headers,
            json=json,
            **urlopen_kw,
        )
    )


def post(
    url,
    /,
    body: _TYPE_BODY | None = None,
    fields: typing.Any | None = None,
    headers: typing.Mapping[str, str] | None = None,
    json: typing.Any | None = None,
    **urlopen_kw: typing.Any,
) -> ResponseWrapper:
    """
    Perform a POST request using urllib3.

    It utilizes PoolManager or ProxyManager depending on the network settings
    defined in `$HOME/.sema4ai/network-settings.yaml`.
    """
    return ResponseWrapper(
        _get_connection_manager().request(
            "post",
            url,
            body=body,
            fields=fields,
            headers=headers,
            json=json,
            **urlopen_kw,
        )
    )


def put(
    url,
    /,
    body: _TYPE_BODY | None = None,
    fields: typing.Any | None = None,
    headers: typing.Mapping[str, str] | None = None,
    json: typing.Any | None = None,
    **urlopen_kw: typing.Any,
) -> ResponseWrapper:
    """
    Perform a PUT request using urllib3.

    It utilizes PoolManager or ProxyManager depending on the network settings
    defined in `$HOME/.sema4ai/network-settings.yaml`.
    """
    return ResponseWrapper(
        _get_connection_manager().request(
            "put",
            url,
            body=body,
            fields=fields,
            headers=headers,
            json=json,
            **urlopen_kw,
        )
    )


def patch(
    url,
    /,
    body: _TYPE_BODY | None = None,
    fields: typing.Any | None = None,
    headers: typing.Mapping[str, str] | None = None,
    json: typing.Any | None = None,
    **urlopen_kw: typing.Any,
) -> ResponseWrapper:
    """
    Perform a PATCH request using urllib3.

    It utilizes PoolManager or ProxyManager depending on the network settings
    defined in `$HOME/.sema4ai/network-settings.yaml`.
    """
    return ResponseWrapper(
        _get_connection_manager().request(
            "patch",
            url,
            body=body,
            fields=fields,
            headers=headers,
            json=json,
            **urlopen_kw,
        )
    )


def delete(
    url,
    /,
    body: _TYPE_BODY | None = None,
    fields: typing.Any | None = None,
    headers: typing.Mapping[str, str] | None = None,
    json: typing.Any | None = None,
    **urlopen_kw: typing.Any,
) -> ResponseWrapper:
    """
    Perform a DELETE request using urllib3.

    It utilizes PoolManager or ProxyManager depending on the network settings
    defined in `$HOME/.sema4ai/network-settings.yaml`.
    """
    return ResponseWrapper(
        _get_connection_manager().request(
            "delete",
            url,
            body=body,
            fields=fields,
            headers=headers,
            json=json,
            **urlopen_kw,
        )
    )


@dataclass(slots=True)
class _RequestInfo:
    url: str
    headers: dict[str, str] | None
    chunk_size: int
    pool_manager: urllib3.PoolManager
    timeout: int

    def set_range_header(self, value) -> None:
        if not self.headers:
            self.headers = {}
        else:
            self.headers = self.headers.copy()

        self.headers["Range"] = f"bytes={value}-"

    def make_request(self) -> urllib3.BaseHTTPResponse:
        return self.pool_manager.request(
            "get",
            self.url,
            headers=self.headers,
            preload_content=False,
            timeout=self.timeout,
        )


class _PartialDownloader:
    _status: DownloadStatus | None
    _http_error: urllib3.exceptions.HTTPError | None

    def __init__(
        self,
        *,
        request_info: _RequestInfo,
        target: Path,
        logger: logging.Logger,
        overwrite_existing: bool,
        max_retries: int,
        resume_existing: bool,
    ):
        if target.is_dir():
            raise ValueError("Target must not be a directory")

        if target.exists() and not overwrite_existing:
            self._status = DownloadStatus.ALREADY_EXISTS
        else:
            self._status = None

        self._request_info = request_info
        self._target = target
        self._logger = logger
        self._max_retries = max_retries
        self._current_try = 0

        self._partial_target = self.get_partial_target(target)
        if not resume_existing:
            self.remove_part()

        self._http_error = None

    @staticmethod
    def get_partial_target(target: str | Path) -> Path:
        as_path = Path(target)
        target_dir, target_filename = as_path.parent, as_path.name
        return target_dir / f"{target_filename}.part"

    @property
    def status(self) -> DownloadStatus | None:
        return self._status

    def remove_part(self):
        self._partial_target.unlink(missing_ok=True)

    def _handle_request_error(self, error: Exception) -> DownloadStatus:
        # We log and suppress urllib3 exceptions
        if isinstance(error, urllib3.exceptions.HTTPError):
            self._logger.exception(
                "Error downloading (will try to resume)", exc_info=error
            )
            self._http_error = error
            return self._set_status(DownloadStatus.HTTP_ERROR)

        # For anything else we reraise the error
        raise error from error

    def _set_status(self, status: DownloadStatus):
        """Helper method use to set status"""

        self._status = status
        return status

    def __iter__(self):
        return self

    def __next__(self):
        if self._status in [DownloadStatus.DONE, DownloadStatus.ALREADY_EXISTS]:
            raise StopIteration

        if self._current_try > self._max_retries:
            raise StopIteration

        self._status = DownloadStatus.PARTIAL
        self._current_try += 1

        self._logger.info(f"Download attempt #{self._current_try}")

        try:
            current_size = self._partial_target.stat().st_size
        except FileNotFoundError:
            # If file was not found then we start a new download
            current_size = 0

        if current_size != 0:
            self._request_info.set_range_header(current_size)

        try:
            response = self._request_info.make_request()
        except Exception as err:
            return self._handle_request_error(err)

        content_length = int(response.headers.get("Content-Length") or -1)

        if content_length < 1:
            if not current_size:
                raise ValueError("Request returned no content")

            if current_size >= content_length:
                self._logger.debug("File already downloaded")
                return self._set_status(DownloadStatus.DONE)

        if current_size:
            self._logger.debug(f"Current file size: {current_size:_} bytes")
            content_range = response.headers.get("Content-Range", "")

            if (expected_content_length := int(content_range.split("/")[-1] or -1)) < 0:
                raise ValueError("Resuming downloads is not supported.")

            self._logger.debug(f"Expected file size: {expected_content_length:_} bytes")

            if content_length == 0 and current_size == expected_content_length:
                return self._set_status(DownloadStatus.DONE)

            if current_size >= expected_content_length:
                raise ValueError("Current file size exceeds expected download size")

            self._logger.info(f"Resuming download for {self._request_info.url}")

        else:
            expected_content_length = content_length

        file_mode = "ab" if current_size else "wb"

        with self._partial_target.open(mode=file_mode) as stream:
            # Note: in a bad connection it can return an empty chunk
            # even before finishing (so, we resume it afterward if
            # that was the case).
            try:
                while chunk := response.read(self._request_info.chunk_size):
                    stream.write(chunk)
            except Exception as err:
                self._handle_request_error(err)

        if self._partial_target.stat().st_size != expected_content_length:
            # Check if the file size on disk matches the expected content length
            # if not set the status as partial
            return self._set_status(DownloadStatus.PARTIAL)

        return self._set_status(DownloadStatus.DONE)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # An error occurred so we delete the partial file
        if exc_val and not isinstance(exc_val, KeyboardInterrupt):
            self._partial_target.unlink(missing_ok=True)

        # Everything is fine so we save the partial file as the target
        if not exc_val and self._status == DownloadStatus.DONE:
            self._partial_target.replace(self._target)
            return

        if self._status == DownloadStatus.HTTP_ERROR and self._http_error:
            raise self._http_error


class DownloadResult(NamedTuple):
    status: DownloadStatus
    path: Path


def partial_file_exists(target: str | Path) -> bool:
    """Helper function that returns if the partial file exists for a specific target"""
    return _PartialDownloader.get_partial_target(target).exists()


def download_with_resume(
    url: str,
    target: str | Path,
    *,
    headers: dict[str, str] | None = None,
    make_executable: bool = False,
    logger: logging.Logger = _DEFAULT_LOGGER,
    chunk_size: int = 1024 * 5,
    pool_manager: urllib3.PoolManager | None = None,
    max_retries: int = 10,
    timeout: int = 5,
    wait_interval: float | int = 1,
    overwrite_existing: bool = False,
    resume_from_existing_part_file: bool = True,
) -> DownloadResult:
    """
    Downloads a file from a URL to a target path with resume support.

    Args:
        url (str): URL to download.
        target (Path | str): The filepath where to download the file.
        If target is a directory the filename will be set to the last part of the url
        headers (dict[str, str] | None): Optional headers to pass to the download function.
        make_executable (bool): Whether to make the file executable. Defaults to False.
        logger (logging.Logger): Optional logger to use.
        chunk_size (int): Size of download chunks. Defaults to 5120 bytes.
        pool_manager (urllib3.PoolManager): Optional urllib3.PoolManager to use.
        max_retries (int): Maximum number of retries. Defaults to 10 retries.
        timeout (int): Timeout in seconds. Default to 5 seconds
        wait_interval (float | int): Time in seconds to wait between retries. Defaults to 1 second.
        overwrite_existing (bool): Whether to overwrite existing files. Defaults to False.
        resume_from_existing_part_file (bool): Whether to resume the download from an existing partial file. Defaults to True.

    Returns:
        Path: Path to the downloaded file.

    """
    import time

    target_path: Path = Path(target)
    if target_path.is_dir() and url:
        filename = url.split("/")[-1]
        target_path = target_path / filename

    if pool_manager is None:
        pool_manager = _get_connection_manager()

    request_info = _RequestInfo(
        url=url,
        headers=headers,
        chunk_size=chunk_size,
        pool_manager=pool_manager,
        timeout=timeout,
    )

    logger.info(f"Downloading '{url}' to '{target_path.absolute()}'")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with _PartialDownloader(
        request_info=request_info,
        target=target_path,
        logger=logger,
        overwrite_existing=overwrite_existing,
        resume_existing=resume_from_existing_part_file,
        max_retries=max_retries,
    ) as downloader:
        for status in downloader:
            match status:
                case DownloadStatus.PARTIAL | DownloadStatus.HTTP_ERROR:
                    logger.info(
                        f"Partial download requested. Waiting {wait_interval} seconds"
                    )
                    if wait_interval:
                        time.sleep(wait_interval)

                case DownloadStatus.DONE:
                    logger.info("File successfully downloaded")
                case DownloadStatus.ALREADY_EXISTS:
                    logger.info("File already downloaded")
                case _:
                    raise RuntimeError(f"Unknown download status: {status}")

    if make_executable:
        import stat

        target_path.chmod(target_path.stat().st_mode | stat.S_IEXEC)

    return DownloadResult(downloader.status, target_path)
