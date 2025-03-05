"""
This module contains a helper which will create a server at a given host/port
and provide a Future which will return when that host/port is accessed.

To be used as a helper during OAuth2 authentication.
"""

import os
import ssl
import sys
import wsgiref.simple_server
from collections.abc import Callable
from concurrent.futures import Future
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, TypedDict
from wsgiref.simple_server import WSGIServer


class _RedirectWSGIApp:
    """
    WSGI app to handle the authorization redirect.

    Stores the request URI and displays the given success message.
    """

    def __init__(self, success_message: str):
        """
        Args:
            success_message: The message to display in the web browser
                the authorization flow is complete.
        """
        self.last_request_uri: str | None = None
        self.last_body: str | None = None
        self.last_headers: Optional[dict[str, str]] = None
        self._success_message = success_message

    def __call__(
        self, environ: dict[str, Any], start_response: Callable[[str, list], Any]
    ) -> list[bytes]:
        """
        Store the requested uri and return a text message.

        Args:
            environ: The WSGI environment.
            start_response: Callable to provide response headers.

        Returns:
            The response body.
        """

        headers = {}

        for header, value in environ.items():
            if header.startswith("HTTP_"):
                headers[header[5:].replace("_", "-").lower()] = value

        try:
            content_length = int(environ.get("CONTENT_LENGTH", "0"))
            if content_length > 0:
                body = (
                    environ["wsgi.input"]
                    .read(content_length)
                    .decode("utf-8", "replace")
                )
            else:
                body = ""

        except Exception:
            start_response("400 Bad Request", [])
            return []

        else:
            start_response(
                "200 OK",
                [
                    ("Content-type", "text/plain; charset=utf-8"),
                    (
                        "Cache-Control",
                        "no-store, no-cache, max-age=0, must-revalidate, proxy-revalidate",
                    ),
                ],
            )
            self.last_request_uri = wsgiref.util.request_uri(environ)
            self.last_body = body
            self.last_headers = headers
            return [self._success_message.encode("utf-8")]


class _WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, fmt, *args):
        pass  # No need to log anything.


def _wrap_socket(
    sock,
    keyfile=None,
    certfile=None,
):
    """
    Converts a regular socket into as SSL socket.
    """
    from ssl import SSLContext

    if keyfile and not certfile:
        raise ValueError("certfile must be specified")
    context = SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.VerifyMode.CERT_NONE
    if certfile:
        context.load_cert_chain(certfile, keyfile)
    return context.wrap_socket(
        sock=sock,
        server_side=True,
        do_handshake_on_connect=True,
        suppress_ragged_eofs=True,
    )


@lru_cache
def _get_action_server_user_sema4_path() -> Path:
    """
    Note: use the same folder as the action server (to reuse the certificate
    that was generated there if available).
    """
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA")
        if not localappdata:
            raise RuntimeError("Error. LOCALAPPDATA not defined in environment!")
        home = Path(localappdata) / "sema4ai"
    else:
        # Linux/Mac
        home = Path("~/.sema4ai").expanduser()

    user_sema4_path = home / "action-server"
    user_sema4_path.mkdir(parents=True, exist_ok=True)
    return user_sema4_path


def _start_server(
    host: str = "localhost",
    port: int = 4444,
    *,
    use_https: bool = False,
    ssl_self_signed: bool = False,
    ssl_keyfile: str | None = None,
    ssl_certfile: str | None = None,
    show_message: str = "Ok, it worked.",
) -> tuple[WSGIServer, _RedirectWSGIApp, str]:
    """
    Args:
        keyfile:
            Required if SSL is required.
        certfile:
            Required if SSL is required.

    Returns:
        The server the app and the address for the server (the server
        is not actually handling requests at this point).
    """
    wsgiref.simple_server.WSGIServer.allow_reuse_address = False
    wsgi_app = _RedirectWSGIApp(show_message)

    local_server = wsgiref.simple_server.make_server(
        host, port, wsgi_app, handler_class=_WSGIRequestHandler
    )

    protocol = "https" if use_https else "http"

    if use_https:
        if not ssl_self_signed:
            if not ssl_keyfile or not ssl_certfile:
                raise RuntimeError(
                    "When use_https is used, either `ssl_self_signed` must be passed or the `ssl_keyfile` and `ssl_certfile` arguments must be provided."
                )
        else:
            if ssl_keyfile or ssl_certfile:
                raise RuntimeError(
                    "When `ssl_self_signed`is passed `ssl_keyfile` and `ssl_certfile` should not be provided (a key/certificate will be generated in the default location)."
                )

    if use_https:
        if ssl_self_signed:
            from . import gen_certificate

            user_path = _get_action_server_user_sema4_path()

            # Note: Same paths from the action server.

            private_path = user_path / "action-server-private-keyfile.pem"
            public_path = user_path / "action-server-public-certfile.pem"

            public, private = gen_certificate.gen_self_signed_certificate()

            public_path.write_bytes(public)
            private_path.write_bytes(private)

            KEY_FILE_PERMISSIONS = 0o600
            private_path.chmod(KEY_FILE_PERMISSIONS)
            ssl_keyfile = str(private_path)
            ssl_certfile = str(public_path)
        else:
            # Note: this was already previously checked.
            assert ssl_keyfile and ssl_certfile

        # Wrap the server with SSL
        local_server.socket = _wrap_socket(
            local_server.socket,
            keyfile=ssl_keyfile,
            certfile=ssl_certfile,
        )

    sockname = local_server.socket.getsockname()
    address = f"{protocol}://{sockname[0]}:{sockname[1]}"
    return local_server, wsgi_app, address


class LastRequestInfoTypedDict(TypedDict):
    uri: str | None
    body: str | None
    headers: dict[str, str] | None


def start_server_in_thread(
    **kwargs,
) -> tuple[Future[LastRequestInfoTypedDict], Future[str]]:
    """
    Calls `_start_server` with the passed args in a thread and returns
    a future which returns the last uri accessed.

    If the returned `Future` is cancelled, the server is also closed.
    """
    import threading

    fut_provide_uri: Future[LastRequestInfoTypedDict] = Future()
    fut_provide_callback_address: Future[str] = Future()

    def method() -> None:
        try:
            # Start the server
            local_server, app, address = _start_server(**kwargs)
            fut_provide_callback_address.set_result(address)

            def on_done(*args, **kwargs):
                # Close when done (either cancelled or in regular flow)
                local_server.server_close()

            fut_provide_uri.add_done_callback(on_done)

            local_server.handle_request()  # serve one request, then exit
            # local_server.serve_forever()

            if not fut_provide_uri.cancelled():
                if app.last_request_uri or app.last_body or app.last_headers:
                    result: LastRequestInfoTypedDict = {
                        "uri": app.last_request_uri,
                        "body": app.last_body,
                        "headers": app.last_headers,
                    }
                    fut_provide_uri.set_result(result)
                else:
                    fut_provide_uri.set_exception(
                        RuntimeError("last_request_uri not set in request")
                    )
        except BaseException as e:
            if not fut_provide_uri.cancelled():
                fut_provide_uri.set_exception(e)
        finally:
            try:
                local_server.server_close()
            except Exception:
                pass

    t = threading.Thread(target=method, name="OAuth2 Server", daemon=True)
    t.start()
    return fut_provide_uri, fut_provide_callback_address


if __name__ == "__main__":
    last_request, reserved_address = start_server_in_thread()
    print(reserved_address.result(timeout=30))
    last_request.cancel()
    print("last uri", last_request.result())
