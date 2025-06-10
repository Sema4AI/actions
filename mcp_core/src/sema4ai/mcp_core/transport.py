from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from sema4ai.mcp_core.protocols import IMCPSessionHandler

from .mcp_models import JSONRPCError, JSONRPCErrorErrorParams, MCPBaseModel


def create_streamable_http_router(
    session_handler: IMCPSessionHandler,
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
        from sema4ai.mcp_core.mcp_models import create_mcp_model

        # Spec says: The client MUST use HTTP POST to send JSON-RPC messages to the MCP endpoint.
        # Spec says: The client MUST include an Accept header, listing both application/json
        # and text/event-stream as supported content types.
        if "application/json" not in accept and "text/event-stream" not in accept:
            raise HTTPException(status_code=400, detail="Invalid Accept header")

        mcp_handler = await session_handler.obtain_session_handler(
            request, mcp_session_id
        )

        response_headers: dict[str, str] = {}
        if mcp_handler.session_id:
            response_headers["Mcp-Session-Id"] = mcp_handler.session_id

        # Read and parse the request body
        try:
            body = await request.json()
        except Exception as e:
            error = JSONRPCError(
                jsonrpc="2.0",
                id=0,  # Unable to get ID from request body because it's not a valid json
                error=JSONRPCErrorErrorParams(
                    code=-32000,
                    message=f"Error parsing request body as json: {e}",
                ),
            )
            return JSONResponse(content=error.to_dict(), headers=response_headers)

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
                raise ValueError(
                    f"Invalid request body, expected dict or list, got {type(body)}"
                )

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
                return JSONResponse(
                    content={}, status_code=202, headers=response_headers
                )

            response = await mcp_handler.handle_message(mcp_models)

            # Spec says: If the input contains any number of JSON-RPC requests, the server MUST either return Content-Type: text/event-stream,
            # to initiate an SSE stream, or Content-Type: application/json, to return one JSON object. The client MUST support both these cases.

            if isinstance(response, EventSourceResponse):
                return response

            if isinstance(response, MCPBaseModel):
                msg_as_dict = response.to_dict()

                return JSONResponse(content=msg_as_dict, headers=response_headers)

            raise ValueError(
                f"Internal error in IMCPImplementation.handle_message: Invalid response type: {type(response)} -- {response}"
            )

        except Exception as e:
            # Create error response
            error = JSONRPCError(
                jsonrpc="2.0",
                id=body.get("id", 1),
                error=JSONRPCErrorErrorParams(
                    code=-32000,
                    message=str(e),
                ),
            )
            return JSONResponse(content=error.to_dict(), headers=response_headers)

    @router.get(route_name)
    async def handle_get(
        request: Request,
        last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
        accept: str = Header(...),
        mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    ):
        if "text/event-stream" not in accept:
            raise HTTPException(status_code=405, detail="SSE not supported")

        if mcp_session_id is None:
            raise HTTPException(status_code=400, detail="Mcp-Session-Id is required")

        mcp_handler = await session_handler.get_session_handler(request, mcp_session_id)

        return mcp_handler.handle_sse_stream(last_event_id)

    @router.delete(route_name)
    async def handle_delete(
        request: Request,
        mcp_session_id: str = Header(..., alias="Mcp-Session-Id"),
    ):
        await session_handler.end_session(request, mcp_session_id)
        return JSONResponse(content={}, status_code=200)

    return router
