import asyncio
import codecs
import json
import logging
import os
import socket
import sys
import time
import typing
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Literal, Optional, Tuple, Union

from pydantic import BaseModel, ValidationError
from termcolor import colored

if typing.TYPE_CHECKING:
    import websockets
    from aiohttp import ClientSession

log = logging.getLogger(__name__)


class SessionPayload(BaseModel):
    sessionId: str
    sessionSecret: str


class BodyPayload(BaseModel):
    requestId: str
    path: str
    method: str = "GET"
    body: dict | None = None
    headers: dict


class ExposeSessionJson(BaseModel):
    expose_session: str
    url: str


def get_expose_session_path(datadir: str) -> str:
    return os.path.join(datadir, "expose_session.json")


def read_expose_session_json(datadir: str) -> None | ExposeSessionJson:
    session_json = None
    try:
        expose_session_path = get_expose_session_path(datadir)
        log.debug(f"🗂️ Reading expose_session.json path={expose_session_path}")
        with open(expose_session_path, "r") as f:
            session_json = ExposeSessionJson(**json.load(f))
    except FileNotFoundError:
        pass
    except ValidationError as e:
        log.error("Failed to load previous expose session", e)
    except json.JSONDecodeError as e:
        log.error("Failed to decode exopse session json", e)
    return session_json


def write_expose_session_json(
    datadir: str, expose_session_json: ExposeSessionJson
) -> None:
    expose_session_path = get_expose_session_path(datadir)
    log.debug(f"🗂️ Writing expose_session.json path={expose_session_path}")
    with open(expose_session_path, "w") as f:
        json.dump(
            expose_session_json.model_dump(mode="json"),
            f,
            indent=2,
        )


def get_expose_session(payload: SessionPayload) -> str:
    return f"{payload.sessionId}:{payload.sessionSecret}".encode("ascii").hex()


def get_expose_session_payload(expose_session: str) -> SessionPayload:
    session_id, session_secret = codecs.decode(
        expose_session.encode("ascii"), "hex"
    ).split(b":")
    return SessionPayload(
        sessionId=session_id.decode(), sessionSecret=session_secret.decode()
    )


async def forward_request_async(
    session: "ClientSession", base_url: str, payload: BodyPayload
) -> Tuple[int, dict]:
    url = base_url.rstrip("/") + "/" + payload.path.lstrip("/")

    async with session.request(
        payload.method, url, json=payload.body, headers=payload.headers
    ) as response:
        return response.status, await response.json()


async def handle_ping_pong(
    ws: "websockets.WebSocketClientProtocol",
    pong_queue: asyncio.Queue,
    ping_interval: int,
):
    while True:
        await asyncio.sleep(ping_interval)
        await ws.send("ping")

        try:
            await asyncio.wait_for(pong_queue.get(), timeout=ping_interval)
        except (asyncio.TimeoutError, TimeoutError):
            log.debug("Lost connection to expose server")
            await ws.close()
            break


def handle_session_payload(
    session_payload: SessionPayload, expose_url: str, datadir: str, api_key: str | None
):
    url = f"https://{session_payload.sessionId}.{expose_url}"
    log.info(
        colored("  🌍 Public URL: ", "green", attrs=["bold"])
        + colored(f"{url}", "light_blue")
    )
    if api_key:
        log.info(
            colored("  🔑 API Authorization Bearer key: ", attrs=["bold"])
            + f"{api_key}\n"
        )
    new_expose_session = get_expose_session(session_payload)
    write_expose_session_json(
        datadir=datadir,
        expose_session_json=ExposeSessionJson(
            expose_session=new_expose_session,
            url=url,
        ),
    )


async def handle_body_payload(
    session: "ClientSession",
    get_ws_coro: Coroutine[
        Any, Any, Union["websockets.WebSocketClientProtocol", Literal["FINISH"]]
    ],
    payload: BodyPayload,
    base_url: str,
):
    try:
        status, json_dict = await forward_request_async(
            session=session, base_url=base_url, payload=payload
        )
        response_converted = json.dumps(
            {
                "requestId": payload.requestId,
                "response": json.dumps(
                    json_dict,
                    indent=2,
                ),
                "status": status,
            }
        )

        timeout_at = time.monotonic() + 30  # Retry up to 30 seconds before giving up
        while True:
            ws = await get_ws_coro

            if ws == "FINISH":
                # It seems it won't be made available, so, just finish it and
                # stop waiting.
                break

            try:
                await ws.send(response_converted)
            except Exception:
                if timeout_at > time.monotonic():
                    log.exception(
                        "Error sending body payload (timed out: will not retry)"
                    )
                    break
                log.exception("Error sending body payload (will retry)")
            else:
                # No exception: finish
                break

    except Exception:
        log.exception("Error handling body payload")


def _headers_from_session_payload(session_payload: SessionPayload):
    headers = {
        "x-session-id": session_payload.sessionId,
        "x-session-secret": session_payload.sessionSecret,
    }
    return headers


class ServerEvent:
    pass


@dataclass
class EventConnected(ServerEvent):
    ws: "websockets.WebSocketClientProtocol"


@dataclass
class EventMessage(ServerEvent):
    message: str | bytes


@dataclass
class EventSessionPayload(ServerEvent):
    session_payload: SessionPayload


@dataclass
class EventAsyncIOLoop(ServerEvent):
    loop: asyncio.AbstractEventLoop


@dataclass
class EventTaskListenForRequests(ServerEvent):
    task: asyncio.Task


class EventTaskListenForRequestsFinished(ServerEvent):
    pass


async def listen_for_requests(
    server_url: str,
    expose_url: str,
    datadir: str,
    expose_session: str | None = None,
    ping_interval: int = 4,
    api_key: str | None = None,
    on_event: Callable[[ServerEvent], None] | None = None,
) -> None:
    import aiohttp
    import websockets

    pong_queue: asyncio.Queue = asyncio.Queue(maxsize=1)

    session_payload: Optional[SessionPayload] = (
        get_expose_session_payload(expose_session) if expose_session else None
    )

    headers = _headers_from_session_payload(session_payload) if session_payload else {}

    # In testing wss:// is added (in production it's just sema4ai.link and
    # we connect to wss://client.sema4ai.link and when we receive the session
    # id/secret we print it as: https://{session_payload.sessionId}.{expose_url}).
    if not expose_url.startswith("wss://") and not expose_url.startswith("ws://"):
        use_url = f"wss://client.{expose_url}"
    else:
        use_url = expose_url

    use_ws: Optional[
        Union["websockets.WebSocketClientProtocol", Literal["FINISH"]]
    ] = None
    use_ws_event = asyncio.Event()

    async def get_ws_coro() -> (
        Union["websockets.WebSocketClientProtocol", Literal["FINISH"]]
    ):
        nonlocal use_ws
        nonlocal use_ws_event

        while use_ws is None:
            use_ws_event.clear()
            await use_ws_event.wait()

        return use_ws

    try:
        https_info = os.environ.get("SEMA4AI-SERVER-HTTPS-INFO")
        connector: Optional[aiohttp.BaseConnector] = None
        if https_info:
            try:
                loaded = json.loads(https_info)
            except Exception:
                raise RuntimeError(
                    f'Unable to load "SEMA4AI-SERVER-HTTPS-INFO" env var: {https_info}'
                )

            if loaded.get("use_https"):
                ssl_certfile = loaded.get("ssl_certfile")

                if not ssl_certfile:
                    raise RuntimeError(
                        "Using https but `ssl_certfile` is not available."
                    )

                if not os.path.exists(ssl_certfile):
                    raise RuntimeError(f"ssl_certfile: {ssl_certfile} does not exist.")

                import ssl
                from ssl import Purpose

                ctx = ssl.create_default_context(Purpose.SERVER_AUTH)
                ctx.load_verify_locations(
                    ssl_certfile,
                )

                connector = aiohttp.TCPConnector(ssl=ctx)

        ws: websockets.WebSocketClientProtocol
        async with aiohttp.ClientSession(connector=connector) as session:
            async for ws in websockets.connect(
                use_url,
                extra_headers=headers,
                logger=log,
                open_timeout=2,
                close_timeout=0,
            ):
                if on_event is not None:
                    on_event(EventConnected(ws))
                use_ws = ws
                use_ws_event.set()

                ping_task = asyncio.create_task(
                    handle_ping_pong(ws, pong_queue, ping_interval)
                )

                try:
                    while True:
                        message = await ws.recv()
                        if on_event is not None:
                            on_event(EventMessage(message))

                        if message == "pong":
                            await pong_queue.put("pong")
                            continue

                        data = json.loads(message)

                        match data:
                            case {"sessionId": _, "sessionSecret": _}:
                                try:
                                    session_payload = SessionPayload(**data)
                                    if on_event is not None:
                                        on_event(EventSessionPayload(session_payload))
                                    # Make sure that after we connect the session is
                                    # always the same for reconnects.
                                    # Note: tricky detail: because we're reconnecting
                                    # in the above `for` which already has the `extra_headers`
                                    # bound, we just update the headers in-place...
                                    # this could fail in the future is websockets.connect
                                    # for some reason does a copy of the extra headers,
                                    # so, we have to be careful (probably not the best
                                    # approach, but working for a fast fix).
                                    headers.update(
                                        _headers_from_session_payload(session_payload)
                                    )
                                    handle_session_payload(
                                        session_payload,
                                        expose_url,
                                        datadir,
                                        api_key,
                                    )
                                except ValidationError as e:
                                    if not session_payload:
                                        log.error(
                                            "Expose session initialization failed",
                                            e,
                                        )
                                        continue
                            case _:
                                try:
                                    body_payload = BodyPayload(**data)
                                    asyncio.create_task(
                                        handle_body_payload(
                                            session,
                                            get_ws_coro(),
                                            body_payload,
                                            server_url,
                                        )
                                    )
                                except ValidationError as e:
                                    log.error("Expose request validation failed", e)
                                    continue
                except websockets.exceptions.ConnectionClosedError:
                    log.info("Lost connection. Reconnecting to expose server...")
                    use_ws = None
                    use_ws_event.clear()

                except socket.gaierror as e:
                    log.info(f"Socket error: {e}")
                    use_ws = None
                    use_ws_event.clear()

                except Exception as e:
                    log.error(f"Unexpected exception: {e}")
                    use_ws = None
                    use_ws_event.clear()

                finally:
                    ping_task.cancel()
                    try:
                        await ping_task
                    except asyncio.CancelledError:
                        pass
            else:
                log.info("Expose server connection closed")
                use_ws = None
                use_ws_event.clear()
    finally:
        use_ws = "FINISH"
        use_ws_event.set()


async def expose_server(
    server_url: str,
    expose_url: str,
    datadir: str,
    expose_session: str | None = None,
    ping_interval: int = 4,
    api_key: str | None = None,
    on_event: Callable[[ServerEvent], None] | None = None,
):
    """
    Exposes the server to the world.
    """
    if on_event is not None:
        loop = asyncio.get_running_loop()
        on_event(EventAsyncIOLoop(loop))

    task = asyncio.create_task(
        listen_for_requests(
            server_url,
            expose_url,
            datadir,
            expose_session,
            ping_interval,
            api_key,
            on_event,
        )
    )
    if on_event is not None:
        on_event(EventTaskListenForRequests(task))
    try:
        await task  # Wait for listen_for_requests to complete
    except asyncio.CancelledError:
        log.info("Expose server listen requests cancelled.")
    except Exception:
        log.exception("Expose server finished with unexpected exception.")
    finally:
        if on_event is not None:
            on_event(EventTaskListenForRequestsFinished())


def _setup_logging(verbose="v", force=False):
    logging.basicConfig(
        level=logging.DEBUG if verbose.count("v") > 0 else logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        force=force,
    )

    def remove_traceback(record):
        if record.levelname == "INFO":
            if record.exc_info:
                record.exc_info = None
        return True

    # Don't bee too verbose when attempting to reconnect.
    log.addFilter(remove_traceback)


def main(
    parent_pid: str,
    server_url: str,
    verbose: str,
    expose_url: str,
    datadir: str,
    expose_session: str,
    api_key: str | None,
    config_logging: bool = True,
) -> None:
    """
    Args:
        parent_pid:
            The pid of the parent (when the given pid exists, this process must
            also exit itself). If it's an empty string, it's ignored.

        verbose:
            A string with `v` chars (currently a single `v` means debug, otherwise
            info).

        server_url:
            The url to where the data should be forwarded.

        expose_url:
            The url for the expose (usually "sema4ai.link").

            Note that the protocol here is that it'll connect to something as:

            wss://client.{expose_url}

            Which will then provide a message with a payload such as:

                {"sessionId": _, "sessionSecret": _}

            and then the server will start accepting connections at:

            https://{session_payload.sessionId}.{expose_url}

            and then messages can be sent to that address to be received
            by the action server.

        datadir:
            The directory where the expose session information should
            be stored.

        expose_session:
            A string with the information of a previous session which
            should be restored (or 'None' if there's no previous session
            information to be restored).

        api_key:
            The api key that should be passed to the action server along with
            the forwarded messages so that the action server accepts it.
    """

    if config_logging:
        _setup_logging(verbose)

    if parent_pid:
        from sema4ai.action_server._preload_actions.preload_actions_autoexit import (
            exit_when_pid_exists,
        )

        exit_when_pid_exists(parent_pid)

    try:
        asyncio.run(
            expose_server(
                server_url=server_url,
                expose_url=expose_url,
                datadir=datadir,
                expose_session=expose_session if expose_session != "None" else None,
                api_key=api_key,
            )
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        (
            parent_pid,
            server_url,
            verbose,
            expose_url,
            datadir,
            expose_session,
            api_key,
        ) = sys.argv[1:]
    except Exception:
        raise RuntimeError(f"Unable to initialize with sys.argv: {sys.argv}")

    main(
        parent_pid,
        server_url,
        verbose,
        expose_url,
        datadir,
        expose_session,
        api_key,
    )
