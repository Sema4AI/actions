import asyncio
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from .mcp_models import (
    Implementation,
    InitializeRequest,
    InitializeResult,
    MCPBaseModel,
    ServerCapabilities,
)
from .protocols import IStreamableHttpMCPHandler, IStreamableHttpMCPSessionHandler

log = logging.getLogger(__name__)


_DONE: Literal["DONE"] = "DONE"


class StreamableHttpMCPHandler(IStreamableHttpMCPHandler):
    """Base MCP low-level implementation (base framework to handle MCP requests using streamable HTTP)."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._initialized = False

    async def handle_requests(
        self, mcp_models: list[MCPBaseModel]
    ) -> MCPBaseModel | EventSourceResponse:
        """Handle an MCP request.

        Args:
            mcp_models: The MCP models to handle (one or more).

        Returns:
            One MCP model or an EventSourceResponse
        """
        from sema4ai.mcp_core.mcp_models import JSONRPCResponse

        single_model = len(mcp_models) == 1

        if not self._initialized:
            for model in mcp_models:
                if isinstance(model, InitializeRequest):
                    if self._initialized:
                        raise ValueError(
                            f"Error: InitializeRequest cannot be sent more than once, received: {mcp_models}"
                        )
                    if not single_model:
                        raise ValueError(
                            f"Error: InitializeRequest cannot be batched, received: {mcp_models}"
                        )
                    self._initialized = True

                    response = JSONRPCResponse(
                        id=model.id,
                        result=InitializeResult(
                            capabilities=ServerCapabilities(),
                            protocolVersion="2025-03-26",
                            serverInfo=Implementation(name="test-server", version="1.0.0"),
                        ),
                    )
                    return response

        return await self._handle_requests(mcp_models)

    async def _process_mcp_requests(
        self,
        queue: asyncio.Queue[dict[str, str] | Literal["DONE"]],
        mcp_models: list[MCPBaseModel],
    ) -> None:
        """Process MCP requests and put results in the queue."""
        from sema4ai.mcp_core.mcp_models import create_json_rpc_error

        try:
            for model in mcp_models:
                # Process each model and put results in queue
                # For now, just echo the model as JSON
                pass

            # Signal completion
            await queue.put(_DONE)
        except Exception as e:
            # Handle errors by sending them to the queue
            await queue.put(create_json_rpc_error(str(e)))
            await queue.put(_DONE)

    async def event_generator(self, queue: asyncio.Queue[dict[str, str] | Literal["DONE"]]):
        """Generate SSE events from the queue."""
        from sema4ai.mcp_core.mcp_models import create_json_rpc_error

        while True:
            try:
                # Get next item from queue
                item = await queue.get()

                # Check if we're done
                if item == _DONE:
                    break

                yield item

            except Exception as e:
                log.exception(e)
                yield create_json_rpc_error(str(e))
                break
            finally:
                queue.task_done()

    async def _handle_requests(
        self, mcp_models: list[MCPBaseModel]
    ) -> MCPBaseModel | EventSourceResponse:
        """Handle MCP requests using an async queue and EventSourceResponse."""

        # A queue to store the results of the requests (or other messages to be sent to the client)
        # until a "DONE" message is put in the queue.
        queue: asyncio.Queue[dict[str, str] | Literal["DONE"]] = asyncio.Queue()

        _task = asyncio.create_task(self._process_mcp_requests(queue, mcp_models))

        return EventSourceResponse(self.event_generator(queue))

    async def handle_notifications(self, mcp_models: list[MCPBaseModel]) -> None:
        """Handle MCP notifications (sent from the client to the server)."""

    async def handle_responses(self, mcp_models: list[MCPBaseModel]) -> None:
        """Handle MCP responses (something requested by the server and answered by the client)."""

    async def handle_sse_stream(self, last_event_id: str | None) -> EventSourceResponse:
        """Handle SSE stream requests (sent from the server to the client)."""

        async def event_generator():
            if False:
                yield {"data": "test"}

        return EventSourceResponse(event_generator())


class StreamableHttpMCPSessionHandler(IStreamableHttpMCPSessionHandler):
    """Base MCP session handler that handles sessions."""

    def __init__(self) -> None:
        self._handlers: dict[str, IStreamableHttpMCPHandler] = {}

    async def obtain_session_handler(
        self, request: Request, session_id: str | None
    ) -> IStreamableHttpMCPHandler:
        """Obtain an MCP session handler."""
        import uuid

        if session_id is None:
            session_id = str(uuid.uuid4())
        self._handlers[session_id] = StreamableHttpMCPHandler(session_id)
        return self._handlers[session_id]

    async def get_session_handler(
        self, request: Request, session_id: str
    ) -> IStreamableHttpMCPHandler:
        """Get an MCP session handler."""
        return self._handlers[session_id]

    async def end_session(self, request: Request, session_id: str) -> None:
        """End an MCP session."""
        self._handlers.pop(session_id, None)


def create_streamable_http_router(
    session_handler: IStreamableHttpMCPSessionHandler,
    router: APIRouter | None = None,
    route_name: str = "/mcp",
) -> APIRouter:
    router = APIRouter() if router is None else router
    route_name = route_name if route_name.startswith("/") else f"/{route_name}"

    @router.post(route_name)
    async def handle_post(
        request: Request,
        accept: str = Header(...),
        mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    ):
        from sema4ai.mcp_core.mcp_base_model import MessageType
        from sema4ai.mcp_core.mcp_models import (
            ERROR_CODE_PARSE_ERROR,
            create_json_rpc_error,
            create_mcp_model,
        )

        # Spec says: The client MUST use HTTP POST to send JSON-RPC messages to the MCP endpoint.
        # Spec says: The client MUST include an Accept header, listing both application/json
        # and text/event-stream as supported content types.
        if "application/json" not in accept and "text/event-stream" not in accept:
            raise HTTPException(status_code=400, detail="Invalid Accept header")

        mcp_handler = await session_handler.obtain_session_handler(request, mcp_session_id)

        response_headers: dict[str, str] = {}
        if mcp_handler.session_id:
            response_headers["Mcp-Session-Id"] = mcp_handler.session_id

        # Read and parse the request body
        try:
            body = await request.json()
        except Exception as e:
            error_dict = create_json_rpc_error(
                f"Error parsing request body as json: {e}",
                code=ERROR_CODE_PARSE_ERROR,
            )
            return JSONResponse(content=error_dict, headers=response_headers)

        # Spec says: The body of the POST request MUST be one of the following:
        #     A single JSON-RPC request, notification, or response
        #     An array batching one or more requests and/or notifications
        #     An array batching one or more responses

        try:
            if isinstance(body, dict):
                mcp_models = [create_mcp_model(body)]
            elif isinstance(body, list):
                mcp_models = [create_mcp_model(item) for item in body]
                if len(mcp_models) == 0:
                    raise ValueError("Empty list of MCP models")
            else:
                raise ValueError(f"Invalid request body, expected dict or list, got {type(body)}")

            requests = []

            for model in mcp_models:
                message_type = model.get_message_type()
                if message_type == MessageType.REQUEST:
                    requests.append(model)  # Requests are handled last

                elif message_type == MessageType.NOTIFICATION:
                    await mcp_handler.handle_notifications([model])

                elif message_type == MessageType.RESPONSE:
                    await mcp_handler.handle_responses([model])
                else:
                    raise ValueError(f"Invalid message type: {message_type} -- {model}")

            if not requests:
                # Spec says: If the input consists solely of (any number of) JSON-RPC responses or notifications:
                #     If the server accepts the input, the server MUST return HTTP status code 202 Accepted with no body.
                #     If the server cannot accept the input, it MUST return an HTTP error status code (e.g., 400 Bad Request).
                # The HTTP response body MAY comprise a JSON-RPC error response that has no id.
                return JSONResponse(content={}, status_code=202, headers=response_headers)

            response = await mcp_handler.handle_requests(mcp_models)

            # Spec says: If the input contains any number of JSON-RPC requests, the server MUST either return Content-Type: text/event-stream,
            # to initiate an SSE stream, or Content-Type: application/json, to return one JSON object. The client MUST support both these cases.

            if isinstance(response, EventSourceResponse):
                return response

            if isinstance(response, MCPBaseModel):
                msg_as_dict = response.to_dict()

                return JSONResponse(content=msg_as_dict, headers=response_headers)

            raise ValueError(
                f"Internal error in IMCPImplementation.handle_requests: Invalid response type: {type(response)} -- {response}"
            )

        except Exception as e:
            # Create error response (generic error)
            error_dict = create_json_rpc_error(str(e), id=body.get("id", None))
            return JSONResponse(content=error_dict, headers=response_headers)

    @router.get(route_name)
    async def handle_get(
        request: Request,
        last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
        accept: str = Header(...),
        mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    ):
        # Spec says:
        # - The client MAY issue an HTTP GET to the MCP endpoint. This can be used to open an SSE stream,
        #   allowing the server to communicate to the client, without the client first sending data via HTTP POST.
        # - The client MUST include an Accept header, listing text/event-stream as a supported content type.
        # - The server MUST either return Content-Type: text/event-stream in response to this HTTP GET, or else
        #   return HTTP 405 Method Not Allowed, indicating that the server does not offer an SSE stream at this endpoint.
        if "text/event-stream" not in accept:
            raise HTTPException(
                status_code=405,
                detail="text/event-stream not included in Accept header",
            )

        if mcp_session_id is None:
            raise HTTPException(status_code=400, detail="Mcp-Session-Id is required")

        try:
            mcp_handler = await session_handler.get_session_handler(request, mcp_session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Session not found")

        # Spec says: If the server initiates an SSE stream:
        #     The server MAY send JSON-RPC requests and notifications on the stream. These requests and notifications MAY be batched.
        #     These messages SHOULD be unrelated to any concurrently-running JSON-RPC request from the client.
        #     The server MUST NOT send a JSON-RPC response on the stream unless resuming a stream associated with a previous client request.
        #     The server MAY close the SSE stream at any time.
        #     The client MAY close the SSE stream at any time.

        return mcp_handler.handle_sse_stream(last_event_id)

    @router.delete(route_name)
    async def handle_delete(
        request: Request,
        mcp_session_id: str = Header(..., alias="Mcp-Session-Id"),
    ):
        await session_handler.end_session(request, mcp_session_id)
        return JSONResponse(content={}, status_code=200)

    return router
