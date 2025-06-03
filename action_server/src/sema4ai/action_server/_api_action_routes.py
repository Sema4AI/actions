import logging

from fastapi import params
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser
from starlette.middleware import Middleware
from starlette.requests import HTTPConnection
from starlette.types import Receive, Scope, Send

from sema4ai.action_server._app import _CustomFastAPI

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


class APIKeyAuthBackend(AuthenticationBackend):
    """
    Authentication backend that validates API key.
    """

    def __init__(
        self,
        api_key: str,
    ):
        self.api_key = api_key

    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, BaseUser] | None:
        from starlette.authentication import SimpleUser
        from starlette.exceptions import HTTPException
        from starlette.status import HTTP_403_FORBIDDEN

        auth_header = next(
            (
                conn.headers.get(key)
                for key in conn.headers
                if key.lower() == "authorization"
            ),
            None,
        )
        if not auth_header or not auth_header.lower().startswith("bearer "):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Validate the token with the provider
        if token != self.api_key:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials",
            )

        return AuthCredentials([]), SimpleUser("authenticated")


class _ActionRoutes:
    def __init__(
        self,
        whitelist: str | None,
        endpoint_dependencies: list[params.Depends],
    ):
        """
        Args:
            whitelist: The whitelist of actions to register.
            endpoint_dependencies: The dependencies for the endpoint (which will require the API key).
            api_key: The API key to use for the endpoint.
        """
        from mcp.server.sse import SseServerTransport
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

        from sema4ai.action_server._models import Action, ActionPackage
        from sema4ai.action_server.mcp.setup_mcp_server_from_actions import (
            McpServerSetupHelper,
        )

        self.whitelist = whitelist
        self.endpoint_dependencies = endpoint_dependencies
        self.action_package_id_to_action_package: dict[str, ActionPackage] = {}
        self.actions: list[Action] = []
        self.registered_route_names: set[str] = set()
        self.mcp_server_setup_helper: McpServerSetupHelper = McpServerSetupHelper()
        self._session_manager: StreamableHTTPSessionManager | None = None
        self._sse_transport: SseServerTransport | None = None

    def setup_mcp_server(self, api_key: str | None) -> None:
        """
        Setup the MCP server with both streamable HTTP and SSE support.
        """
        from starlette.middleware.authentication import AuthenticationMiddleware

        from sema4ai.action_server._app import get_app

        app = get_app()

        middleware: list[Middleware] = []
        if api_key:
            middleware.append(
                Middleware(
                    AuthenticationMiddleware,
                    backend=APIKeyAuthBackend(api_key=api_key),
                )
            )

        self._setup_mcp(app, middleware)
        self._setup_sse(app, middleware)

    def _setup_mcp(self, app: _CustomFastAPI, middleware: list[Middleware]):
        from contextlib import asynccontextmanager

        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        assert self._session_manager is None
        self._session_manager = StreamableHTTPSessionManager(
            app=self.mcp_server_setup_helper.server,
            event_store=None,
            json_response=True,
            stateless=True,
        )

        async def handle_streamable_http(
            scope: Scope, receive: Receive, send: Send
        ) -> None:
            assert self._session_manager is not None
            await self._session_manager.handle_request(scope, receive, send)

        routes: list[Route | Mount] = []

        routes.append(
            Mount(
                "/",
                app=handle_streamable_http,
            )
        )

        @asynccontextmanager
        async def lifespan(app):
            async with self._session_manager.run():
                yield

        app.custom_lifespan.register(lifespan)

        # Passing the lifespan to the Starlette constructor doesn't work at this point
        # (as it's not the "main" Starlette instance).
        self.streamable_http_server = Starlette(
            debug=False,
            routes=routes,
            middleware=middleware,
        )

        app.mount("/mcp", self.streamable_http_server)

    def _setup_sse(self, app: _CustomFastAPI, middleware: list[Middleware]):
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        # -- Setup SSE
        sse = SseServerTransport("/messages/")
        routes: list[Route | Mount] = []

        from starlette.requests import Request
        from starlette.responses import Response

        async def handle_sse(scope: Scope, receive: Receive, send: Send):
            async with sse.connect_sse(
                scope,
                receive,
                send,
            ) as streams:
                await self.mcp_server_setup_helper.server.run(
                    streams[0],
                    streams[1],
                    self.mcp_server_setup_helper.server.create_initialization_options(),
                )
            return Response()

        async def sse_endpoint(request: Request) -> Response:
            # Convert the Starlette request to ASGI parameters
            return await handle_sse(request.scope, request.receive, request._send)  # type: ignore[reportPrivateUsage]

        routes.append(
            Route(
                "/",
                endpoint=sse_endpoint,
                methods=["GET"],
            )
        )
        routes.append(
            Mount(
                "/messages/",
                app=sse.handle_post_message,
            )
        )

        self.sse_server = Starlette(debug=False, routes=routes, middleware=middleware)
        app.mount("/sse", self.sse_server)

    def register_actions(self) -> None:
        import json

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

            doc_desc: str | None = ""
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
            action_kind = "action"
            if options:
                options_as_dict = json.loads(options)
                if options_as_dict:
                    display_name_in_options = options_as_dict.get("display_name")
                    if display_name_in_options:
                        display_name = display_name_in_options

                    action_kind = options_as_dict.get("kind", "action")

            (
                func_fast_api,
                func_internal,
                openapi_extra,
            ) = _actions_run.generate_func_from_action(
                action_package, action, display_name
            )

            if action.is_consequential is not None:
                openapi_extra["x-openai-isConsequential"] = action.is_consequential
            openapi_extra["x-operation-kind"] = action_kind

            route_name = build_url_api_run(action_package.name, action.name)
            assert (
                route_name not in registered_route_names
            ), f"Route: {route_name} already registered."
            app.add_api_route(
                route_name,
                func_fast_api,
                name=action.name,
                summary=display_name,
                description=doc_desc,
                operation_id=action.name,
                methods=["POST"],
                dependencies=self.endpoint_dependencies,
                openapi_extra=openapi_extra,
            )
            registered_route_names.add(route_name)

            self.mcp_server_setup_helper.register_action(
                func_internal, action_package, action, display_name, doc_desc
            )

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
