from typing import Optional, Protocol

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from .mcp_models import JSONRPCError, JSONRPCErrorErrorParams, MCPBaseModel


class IMCPImplementation(Protocol):
    """Protocol defining the interface for MCP implementations."""

    async def start_session(self, session_id: str) -> None:
        """Start an MCP session.

        Args:
            session_id: The ID of the session
        """

    async def end_session(self, session_id: str) -> None:
        """End an MCP session.

        Args:
            session_id: The ID of the session
        """

    async def handle_sse_stream(
        self, last_event_id: Optional[str]
    ) -> EventSourceResponse:
        """Handle an SSE stream.

        Args:
            last_event_id: The last event ID

        Returns:
            An EventSourceResponse for streaming responses
        """

    async def handle_message(
        self, request: list[MCPBaseModel]
    ) -> MCPBaseModel | EventSourceResponse:
        """Handle an MCP request.

        Args:
            request: The MCP request to handle

        Returns:
            Either a response model or an EventSourceResponse for streaming responses
        """

    async def handle_notifications(self, notifications: list[MCPBaseModel]) -> None:
        """Handle an MCP notification.

        Args:
            notifications: The MCP notifications to handle
        """

    async def handle_responses(self, responses: list[MCPBaseModel]) -> None:
        """Handle an MCP response.

        Args:
            responses: The MCP responses to handle (from a request the server sent to the client)
        """


class McpTransport:
    def __init__(self, app: FastAPI, implementation: IMCPImplementation) -> None:
        @app.post("/mcp")
        async def handle_post(
            request: Request,
            accept: str = Header(...),
        ):
            from sema4ai.mcp_core.mcp_base_model import MessageType
            from sema4ai.mcp_core.mcp_models import create_mcp_model

            # Spec says: The client MUST use HTTP POST to send JSON-RPC messages to the MCP endpoint.
            # Spec says: The client MUST include an Accept header, listing both application/json
            # and text/event-stream as supported content types.
            if "application/json" not in accept and "text/event-stream" not in accept:
                raise HTTPException(status_code=400, detail="Invalid Accept header")

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
                return JSONResponse(content=error.to_dict())

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
                        await implementation.handle_notifications([model])

                    elif message_type == MessageType.RESPONSE:
                        await implementation.handle_responses([model])
                    else:
                        raise ValueError(
                            f"Invalid message type: {message_type} -- {model}"
                        )

                if not requests:
                    # Spec says: If the input consists solely of (any number of) JSON-RPC responses or notifications:
                    #     If the server accepts the input, the server MUST return HTTP status code 202 Accepted with no body.
                    #     If the server cannot accept the input, it MUST return an HTTP error status code (e.g., 400 Bad Request).
                    # The HTTP response body MAY comprise a JSON-RPC error response that has no id.
                    return JSONResponse(content={}, status_code=202)

                response = await implementation.handle_message(mcp_models)

                # Spec says: If the input contains any number of JSON-RPC requests, the server MUST either return Content-Type: text/event-stream,
                # to initiate an SSE stream, or Content-Type: application/json, to return one JSON object. The client MUST support both these cases.

                if isinstance(response, EventSourceResponse):
                    return response

                if isinstance(response, MCPBaseModel):
                    msg_as_dict = response.to_dict()

                    return JSONResponse(content=msg_as_dict)

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
                return JSONResponse(content=error.to_dict())

        @app.get("/mcp")
        async def handle_get(
            request: Request,
            last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
            accept: str = Header(...),
        ):
            if "text/event-stream" not in accept:
                raise HTTPException(status_code=405, detail="SSE not supported")

            return implementation.handle_sse_stream(last_event_id)
