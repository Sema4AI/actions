import logging
import ssl
import stat
import sys
import time
from copy import copy
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

import truststore
import urllib3

_DEFAULT_LOGGER = logging.getLogger(__name__)


if sys.version_info < (3, 12):
    _SSL_LEGACY_SERVER_CONNECT = 0x4
else:
    _SSL_LEGACY_SERVER_CONNECT = ssl.OP_LEGACY_SERVER_CONNECT


class DownloadStatus(Enum):
    """Status"""

    DONE = auto()
    PARTIAL = auto()
    ALREADY_EXISTS = auto()
    HTTP_ERROR = auto()


def build_ssl_context(
    protocol: int = None, *, enable_legacy_server_connect: bool = False
) -> ssl.SSLContext:
    """Returns a Truststore SSL context with OP_LEGACY_SERVER_CONNECT flag enabled"""
    ctx = truststore.SSLContext(protocol)
    if enable_legacy_server_connect:
        ctx.options |= _SSL_LEGACY_SERVER_CONNECT
    return ctx


_DEFAULT_POOL = urllib3.PoolManager(
    ssl_context=build_ssl_context(ssl.PROTOCOL_TLS_CLIENT), cert_reqs="CERT_REQUIRED"
)


def get(url, /, **kwargs) -> urllib3.BaseHTTPResponse:
    return _DEFAULT_POOL.request("get", url, **kwargs)


def post(url, /, **kwargs) -> urllib3.BaseHTTPResponse:
    return _DEFAULT_POOL.request("post", url, **kwargs)


def put(url, /, **kwargs) -> urllib3.BaseHTTPResponse:
    return _DEFAULT_POOL.request("put", url, **kwargs)


def patch(url, /, **kwargs) -> urllib3.BaseHTTPResponse:
    return _DEFAULT_POOL.request("patch", url, **kwargs)


def delete(url, /, **kwargs) -> urllib3.BaseHTTPResponse:
    return _DEFAULT_POOL.request("delete", url, **kwargs)


@dataclass(slots=True)
class _RequestInfo:
    url: str
    headers: dict[str, str] | None
    chunk_size: int
    poll_manager: urllib3.PoolManager
    timeout: int

    def set_range_header(self, value) -> "_RequestInfo":
        clone = copy(self)
        if not clone.headers:
            clone.headers = {}

        clone.headers["Range"] = f"bytes={value}-"

        return clone

    def make_request(self) -> urllib3.BaseHTTPResponse:
        return self.poll_manager.request(
            "get",
            self.url,
            headers=self.headers,
            preload_content=False,
            timeout=self.timeout,
        )


class _PartialDownloader:
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
    def get_partial_target(target: Path) -> Path:
        target_dir, target_filename = target.parent, target.name
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
            request_info = self._request_info.set_range_header(current_size)
        else:
            request_info = self._request_info

        try:
            response = request_info.make_request()
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

            self._logger.info(f"Resuming download for {request_info.url}")

        else:
            expected_content_length = content_length

        file_mode = "ab" if current_size else "wb"

        with self._partial_target.open(mode=file_mode) as stream:
            # Note: in a bad connection it can return an empty chunk
            # even before finishing (so, we resume it afterward if
            # that was the case).
            try:
                while chunk := response.read(request_info.chunk_size):
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
            raise self._http_error from self._http_error


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
    poll_manager: urllib3.PoolManager = _DEFAULT_POOL,
    max_retries: int = 10,
    timeout: int = 5,
    wait_interval: float | int = 1,
    overwrite_existing: bool = False,
    resume_existing: bool = True,
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
        poll_manager (urllib3.PoolManager): Optional urllib3.PoolManager to use.
        max_retries (int): Maximum number of retries. Defaults to 10 retries.
        timeout (int): Timeout in seconds. Default to 5 seconds
        wait_interval (float | int): Time in seconds to wait between retries. Defaults to 1 second.
        overwrite_existing (bool): Whether to overwrite existing files. Defaults to False.
        resume_existing (bool): Whether to resume if an existing .part file exists. Defaults to True.

    Returns:
        Path: Path to the downloaded file.

    """
    target: Path = Path(target)
    if target.is_dir() and url:
        filename = url.split("/")[-1]
        target = target / filename

    request_info = _RequestInfo(
        url=url,
        headers=headers,
        chunk_size=chunk_size,
        poll_manager=poll_manager,
        timeout=timeout,
    )

    logger.info(f"Downloading '{url}' to '{target.absolute()}'")
    target.parent.mkdir(parents=True, exist_ok=True)

    with _PartialDownloader(
        request_info=request_info,
        target=target,
        logger=logger,
        overwrite_existing=overwrite_existing,
        resume_existing=resume_existing,
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
            target.chmod(target.stat().st_mode | stat.S_IEXEC)

    return DownloadResult(downloader.status, target)
