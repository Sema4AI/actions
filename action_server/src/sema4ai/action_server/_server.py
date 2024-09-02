import asyncio
import logging
import os
import socket
import subprocess
import sys
import typing
from functools import partial
from typing import Optional, Sequence

from termcolor import colored

from ._protocols import ArgumentsNamespaceStart, IBeforeStartCallback

if typing.TYPE_CHECKING:
    from asyncio.events import AbstractEventLoop

log = logging.getLogger(__name__)


def _name_as_summary(name: str) -> str:
    return name.replace("_", " ").title()


def _name_to_url(name: str) -> str:
    from sema4ai.action_server._slugify import slugify

    return slugify(name.replace("_", "-"))


def build_url_api_run(action_package_name: str, action_name: str) -> str:
    return f"/api/actions/{_name_to_url(action_package_name)}/{_name_to_url(action_name)}/run"


def get_action_description_from_docs(docs: str) -> str:
    import docstring_parser

    doc_desc: str
    try:
        parsed = docstring_parser.parse(docs)
        if parsed.short_description and parsed.long_description:
            doc_desc = f"{parsed.short_description}\n{parsed.long_description}"
        else:
            doc_desc = parsed.long_description or parsed.short_description or ""
    except Exception:
        log.exception("Error parsing docstring: %s", docs)
        doc_desc = str(docs or "")
    return doc_desc


class _ActionRoutes:
    def __init__(self, whitelist: str | None, endpoint_dependencies: list):
        from sema4ai.action_server._models import Action, ActionPackage

        self.whitelist = whitelist
        self.endpoint_dependencies = endpoint_dependencies
        self.action_package_id_to_action_package: dict[str, ActionPackage] = {}
        self.actions: list[Action] = []
        self.registered_route_names: set[str] = set()

    def register_actions(self) -> None:
        import json
        from typing import Optional

        from . import _actions_run
        from ._app import get_app
        from ._models import Action, ActionPackage, get_db

        db = get_db()
        app = get_app()
        action: Action
        action_package_id_to_action_package: dict[str, ActionPackage] = dict(
            (action_package.id, action_package)
            for action_package in db.all(ActionPackage)
        )

        actions = db.all(Action)
        registered_route_names: set[str] = set()
        for action in actions:
            if not action.enabled:
                # Disabled actions should not be registered.
                continue

            doc_desc: Optional[str] = ""
            if action.docs:
                doc_desc = get_action_description_from_docs(action.docs)

            if not doc_desc:
                doc_desc = ""

            action_package = action_package_id_to_action_package.get(
                action.action_package_id
            )
            if not action_package:
                log.critical(
                    "Unable to find action package: %s", action.action_package_id
                )
                continue

            if self.whitelist:
                from ._whitelist import accept_action

                if not accept_action(self.whitelist, action_package.name, action.name):
                    log.info(
                        "Skipping action %s / %s (not in whitelist)",
                        action_package.name,
                        action.name,
                    )
                    continue
            display_name = _name_as_summary(action.name)
            options = action.options
            if options:
                options_as_dict = json.loads(options)
                if options_as_dict:
                    display_name_in_options = options_as_dict.get("display_name")
                    if display_name_in_options:
                        display_name = display_name_in_options

            func, openapi_extra = _actions_run.generate_func_from_action(
                action_package, action, display_name
            )
            if action.is_consequential is not None:
                openapi_extra["x-openai-isConsequential"] = action.is_consequential

            route_name = build_url_api_run(action_package.name, action.name)
            assert (
                route_name not in registered_route_names
            ), f"Route: {route_name} already registered."
            app.add_api_route(
                route_name,
                func,
                name=action.name,
                summary=display_name,
                description=doc_desc,
                operation_id=action.name,
                methods=["POST"],
                dependencies=self.endpoint_dependencies,
                openapi_extra=openapi_extra,
            )
            registered_route_names.add(route_name)

        self.action_package_id_to_action_package = action_package_id_to_action_package
        self.actions = actions
        self.registered_route_names = registered_route_names

    def unregister_actions(self):
        from sema4ai.action_server._app import get_app

        # We need to iterate backwards to remove with indexes.
        app = get_app()
        i = len(app.router.routes)
        for route in reversed(app.router.routes):
            i -= 1
            if route.path_format in self.registered_route_names:
                log.debug("Unregistering route: %s", route.path_format)
                del app.router.routes[i]


class _LoopHolder:
    loop: Optional["AbstractEventLoop"] = None


def start_server(
    start_args: ArgumentsNamespaceStart,
    api_key: str | None,
    expose_session: str | None,
    before_start: Sequence[IBeforeStartCallback],
) -> None:
    import json
    import threading
    import typing
    from dataclasses import asdict
    from functools import lru_cache
    from typing import Any

    import uvicorn
    from fastapi import Depends, HTTPException, Security
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from fastapi.staticfiles import StaticFiles
    from starlette.requests import Request
    from starlette.responses import HTMLResponse

    from . import _actions_process_pool
    from ._api_action_package import action_package_api_router
    from ._api_oauth2 import oauth2_api_router
    from ._api_run import run_api_router
    from ._api_secrets import secrets_api_router
    from ._app import get_app
    from ._server_websockets import websocket_api_router
    from ._settings import get_settings

    if typing.TYPE_CHECKING:
        from ._watcher import ActionServerFileWatcher

    expose: bool = start_args.expose
    whitelist: str | None = start_args.whitelist
    file_watcher: None | "ActionServerFileWatcher" = None

    settings = get_settings()

    settings_dict = asdict(settings)
    settings_str = "\n".join(f"    {k} = {v!r}" for k, v in settings_dict.items())
    log.debug(f"Starting server. Settings:\n{settings_str}")

    app = get_app()

    artifacts_dir = settings.artifacts_dir

    app.mount(
        "/artifacts",
        StaticFiles(directory=artifacts_dir),
        name="artifacts",
    )

    def verify_api_key(
        token: HTTPAuthorizationCredentials = Security(HTTPBearer(auto_error=True)),
    ) -> HTTPAuthorizationCredentials:
        if token.credentials != api_key:
            raise HTTPException(
                status_code=403,
                detail="Invalid or missing API Key",
            )
        else:
            return token

    endpoint_dependencies = []

    if api_key:
        endpoint_dependencies.append(Depends(verify_api_key))

    action_routes = _ActionRoutes(whitelist, endpoint_dependencies)
    action_routes.register_actions()

    if os.getenv("RC_ADD_SHUTDOWN_API", "").lower() in ("1", "true"):

        def shutdown(timeout: int = -1):
            import _thread
            import time

            from sema4ai.action_server._robo_utils.run_in_thread import run_in_thread

            _thread.interrupt_main()

            def interrupt_again():
                time.sleep(timeout)
                _thread.interrupt_main()

            if timeout > 0:
                run_in_thread(interrupt_again, daemon=True)

        app.add_api_route("/api/shutdown/", shutdown, methods=["POST"])

    app.include_router(run_api_router, include_in_schema=settings.full_openapi_spec)
    app.include_router(
        action_package_api_router, include_in_schema=settings.full_openapi_spec
    )
    app.include_router(websocket_api_router)
    app.include_router(secrets_api_router, include_in_schema=settings.full_openapi_spec)
    app.include_router(oauth2_api_router, include_in_schema=settings.full_openapi_spec)

    @lru_cache
    def get_static_config_data() -> dict[str, Any]:
        """
        This information is not expected to be changed after the action
        server is started.
        """
        from sema4ai.action_server import __version__

        from ._server_expose import get_expose_session_payload, read_expose_session_json

        payload = {
            "expose_url": False,
            "auth_enabled": False,
            # When the action server version changes, this means that anything
            # may have changed (including the action server UI).
            "version": __version__,
        }

        if api_key:
            payload["auth_enabled"] = True

        if expose:
            current_expose_session = read_expose_session_json(
                datadir=str(settings.datadir)
            )

            expose_session_payload = (
                get_expose_session_payload(current_expose_session.expose_session)
                if current_expose_session
                else None
            )

            if expose_session_payload:
                payload[
                    "expose_url"
                ] = f"https://{expose_session_payload.sessionId}.{settings.expose_url}"
        return payload

    if start_args.auto_reload:
        _reload_lock = threading.Lock()

        def do_reload(explicit: bool = False) -> bool:
            """
            Internal function to do a reload of the actions.

            Returns:
                True if the reload was successful and False otherwise.
            """
            from sema4ai.action_server._cli_impl import _import_actions
            from sema4ai.action_server._models import get_db
            from sema4ai.action_server._server_websockets import report_mtime_changed

            db = get_db()
            with _reload_lock, db.connect():
                # This is run in a thread. We can't have 2 reloads at the same
                # time, so, a lock is required.

                if explicit:
                    log.info("Reload explicitly called!")
                else:
                    log.info("File-changes detected: auto-reloading!")
                code = _import_actions(
                    start_args,
                    settings,
                    disable_not_imported=True,
                )
                if code != 0:
                    log.info(
                        "Unable to do auto-reload (actions could not be imported)."
                    )
                    return False

                action_routes.unregister_actions()
                action_routes.register_actions()

                actions_process_pool = _actions_process_pool.get_actions_process_pool()
                actions_process_pool.on_reload(
                    action_routes.action_package_id_to_action_package,
                    action_routes.actions,
                )
                app.update_mtime_uuid()
                assert _LoopHolder.loop is not None
                report_mtime_changed(_LoopHolder.loop)
                return True

        from ._watcher import ActionServerFileWatcher

        file_watcher = ActionServerFileWatcher(start_args.dir, do_reload)
        file_watcher.start()

    @app.get("/config", include_in_schema=settings.full_openapi_spec)
    async def serve_config() -> dict[str, Any]:
        payload = get_static_config_data()
        # When the mtime changes, this means that the contents
        # (actions/action packages/expose) may have changed or the
        # action server was restarted (potentially with different settings).
        payload["mtime_uuid"] = app.mtime_uuid
        return payload

    async def serve_log_html(request: Request):
        from robocorp.log import _index_v3 as index

        return HTMLResponse(index.FILE_CONTENTS["index.html"])

    IN_DEV = (
        False  # Set to True to auto-reload the action server UI on each new request.
    )

    def _index_contents(_cache={}) -> bytes:
        if IN_DEV:
            # No caching in dev mode
            _cache.pop("cached", None)

        try:
            return _cache["cached"]
        except KeyError:
            pass

        import base64

        from sema4ai.action_server._storage import get_key

        from . import __version__, _static_contents

        if IN_DEV:
            # Always reload in dev mode.
            from importlib import reload

            _static_contents = reload(_static_contents)

        index_html = _static_contents.FILE_CONTENTS["index.html"]

        key = base64.b64encode(get_key("ui")).decode("utf-8")
        _cache["cached"] = index_html.replace(
            b"<script",
            f"<script>window.ENCRYPTION_KEY={key!r};window.__ACTION_SERVER_VERSION__={__version__!r};</script><script".encode(
                "utf-8"
            ),
            1,
        )
        return _cache["cached"]

    async def serve_index(request: Request):
        from sema4ai.action_server._user_session import session_scope

        with session_scope(request) as session:
            response = HTMLResponse(_index_contents())
            session.response = response
        return response

    index_routes = [
        "/",
        "/runs/{full_path:path}",
        "/actions/{full_path:path}",
        "/oauth2/settings/{full_path:path}",
    ]
    for index_route in index_routes:
        app.add_api_route(
            index_route,
            serve_index,
            response_class=HTMLResponse,
            include_in_schema=settings.full_openapi_spec,
        )

    # At this point the FastAPI app should be configured. What's missing now
    # is setup callbacks related to the startup and actuall start the async
    # loop.

    for callback in before_start:
        if not callback(app):
            return

    expose_subprocess = None

    def _get_currrent_host():
        port = settings.port if settings.port != 0 else None
        host = settings.address
        if port is None:
            sockets_ipv4 = [
                s for s in server.servers[0].sockets if s.family == socket.AF_INET
            ]
            if len(sockets_ipv4) == 0:
                raise Exception("Unable to find a port to expose")
            sockname = sockets_ipv4[0].getsockname()
            # Note: the host is kept the original one passed
            # (i.e.: if it was 'localhost', we don't want to get 127.0.0.1 instead
            # because if we're using https://localhost then 127.0.0.1 may not work).
            # host = sockname[0]
            port = sockname[1]

        return (host, port)

    def expose_later(loop):
        from sema4ai.action_server._settings import is_frozen

        nonlocal expose_subprocess

        if not server.started:
            loop.call_later(1 / 15.0, partial(expose_later, loop))
            return

        (host, port) = _get_currrent_host()
        url = f"{protocol}://{host}:{port}"

        parent_pid = os.getpid()

        if is_frozen():
            # The executable is 'action-server.exe'.
            args = [sys.executable]
        else:
            # The executable is 'python'.
            args = [
                sys.executable,
                "-m",
                "sema4ai.action_server",
            ]

        args += [
            "server-expose",
            str(parent_pid),
            url,
            "" if not settings.verbose else "v",
            settings.expose_url,
            settings.datadir,
            str(expose_session),
            api_key,
        ]
        settings.use_https
        env = os.environ.copy()
        env["SEMA4AI-SERVER-HTTPS-INFO"] = json.dumps(
            {"use_https": settings.use_https, "ssl_certfile": settings.ssl_certfile}
        )
        expose_subprocess = subprocess.Popen(args, env=env)

    protocol = "https" if settings.use_https else "http"

    def _on_started_message(self, **kwargs):
        (host, port) = _get_currrent_host()
        url = f"{protocol}://{host}:{port}"
        settings = get_settings()
        settings.base_url = url

        log.info(
            colored("\n  ⚡️ Local Action Server: ", "green", attrs=["bold"])
            + colored(url, "light_blue")
        )

        if os.getenv("SEMA4AI_OPTIMIZE_FOR_CONTAINER") != "1":
            # No need to log the contents below when in a container.
            if not expose:
                log.info(
                    colored("     Public access: use ", attrs=["dark"])
                    + colored("--expose", attrs=["bold"])
                    + colored(" to expose\n", attrs=["dark"])
                )

                if api_key:
                    log.info(
                        colored("  🔑 API Authorization Bearer key: ", attrs=["bold"])
                        + f"{api_key}\n"
                    )

    async def _on_startup() -> None:
        loop = asyncio.get_event_loop()
        _LoopHolder.loop = loop
        if expose:
            loop.call_later(1 / 15.0, partial(expose_later, loop))

    def _on_shutdown() -> None:
        import psutil

        if file_watcher is not None:
            file_watcher.stop()

        log.info("Stopping action server...")
        from sema4ai.action_server._robo_utils.process import (
            kill_process_and_subprocesses,
        )

        expose_pid = None
        if expose_subprocess is not None:
            log.info("Shutting down expose subprocess: %s", expose_subprocess.pid)
            expose_pid = expose_subprocess.pid
            kill_process_and_subprocesses(expose_pid)

        p = psutil.Process(os.getpid())
        try:
            children_processes = list(p.children(recursive=True))
        except Exception:
            log.exception("Error listing subprocesses.")

        for child in children_processes:
            if child.pid != expose_pid:  # If it's still around, don't kill it again.
                log.info(
                    f"Killing sub-process when exiting action server: {child.name()} (pid: {child.pid})"
                )
                try:
                    kill_process_and_subprocesses(child.pid)
                except Exception:
                    log.exception("Error killing subprocess: %s", child.pid)

    app.add_event_handler("startup", _on_startup)
    app.add_event_handler("shutdown", _on_shutdown)

    with _actions_process_pool.setup_actions_process_pool(
        settings,
        action_routes.action_package_id_to_action_package,
        action_routes.actions,
    ):
        kwargs = settings.to_uvicorn()
        config = uvicorn.Config(app=app, **kwargs)
        server = uvicorn.Server(config)
        server._log_started_message = _on_started_message  # type: ignore[assignment]

        asyncio.run(server.serve())
