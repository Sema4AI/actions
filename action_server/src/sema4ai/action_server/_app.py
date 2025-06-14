import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from functools import cache
from typing import Callable, Never

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from . import _errors
from ._settings import get_settings

LOGGER = logging.getLogger(__name__)


class _CustomLifespan:
    def __init__(self) -> None:
        self._registered_lifespans: list[
            Callable[[FastAPI], AbstractAsyncContextManager[Never, bool | None]]
        ] = []

    def register(
        self,
        lifespan: Callable[[FastAPI], AbstractAsyncContextManager[Never, bool | None]],
    ) -> None:
        self._registered_lifespans.append(lifespan)

    @asynccontextmanager
    async def __call__(self, main_app: FastAPI):
        from contextlib import AsyncExitStack

        async with AsyncExitStack() as stack:
            for lifespan in self._registered_lifespans:
                await stack.enter_async_context(lifespan(main_app))
            yield


class _CustomFastAPI(FastAPI):
    mtime_uuid: str

    def __init__(self, *args, **kwargs) -> None:
        custom_lifespan = _CustomLifespan()
        assert "lifespan" not in kwargs
        kwargs["lifespan"] = custom_lifespan

        super().__init__(*args, **kwargs)
        self.update_mtime_uuid()
        self.custom_lifespan = custom_lifespan

    def update_mtime_uuid(self) -> None:
        import uuid

        self.mtime_uuid: str = str(uuid.uuid4())

    def openapi(self):
        """
        As we're no longer using custom models for the routing APIs (instead of
        pydantic or generated methods for the API, the body is directly queried
        and interpreted as json and its schema validated), FastAPI is no longer
        adding the error references, so, we override the FastAPI.openapi()
        method to provide the needed components.
        """
        if self.openapi_schema:
            return self.openapi_schema

        openapi = FastAPI.openapi(self)
        components = openapi.setdefault("components", {})
        schemas = components.setdefault("schemas", {})
        schemas["HTTPValidationError"] = {
            "properties": {
                "errors": {
                    "items": {"$ref": "#/components/schemas/ValidationError"},
                    "type": "array",
                    "title": "Errors",
                }
            },
            "type": "object",
            "title": "HTTPValidationError",
        }
        schemas["ValidationError"] = {
            "properties": {
                "loc": {
                    "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                    "type": "array",
                    "title": "Location",
                },
                "msg": {"type": "string", "title": "Message"},
                "type": {"type": "string", "title": "Error Type"},
            },
            "type": "object",
            "required": ["loc", "msg", "type"],
            "title": "ValidationError",
        }

        return openapi


@cache
def get_app() -> _CustomFastAPI:
    from sema4ai.action_server import __version__

    settings = get_settings()

    server = {"url": settings.server_url}

    app = _CustomFastAPI(
        title=settings.title,
        servers=[server],
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.add_exception_handler(_errors.RequestError, _errors.request_error_handler)  # type: ignore
    app.add_exception_handler(HTTPException, _errors.http_error_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, _errors.http422_error_handler)  # type: ignore
    app.add_exception_handler(Exception, _errors.http500_error_handler)

    return app
