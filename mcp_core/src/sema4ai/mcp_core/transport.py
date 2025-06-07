import asyncio
import json
import uuid
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse


class McpTransport:
    def __init__(self, app: FastAPI) -> None:
        @app.post("/mcp")
        async def handle_post(
            request: Request,
            accept: str = Header(...),
        ):
            # Spec says: The client MUST use HTTP POST to send JSON-RPC messages to the MCP endpoint.

            # Spec says: The client MUST include an Accept header, listing both application/json
            # and text/event-stream as supported content types.
            if "application/json" not in accept and "text/event-stream" not in accept:
                raise HTTPException(status_code=400, detail="Invalid Accept header")

            # Read and parse the request body
            body = await request.json()

            # Spec says: The body of the POST request MUST be one of the following:
            #     A single JSON-RPC request, notification, or response
            #     An array batching one or more requests and/or notifications
            #     An array batching one or more responses

            # Handle initialization request
            if isinstance(body, dict) and body.get("method") == "initialize":
                response = JSONResponse(
                    content={"jsonrpc": "2.0", "id": body.get("id"), "result": {}},
                )
                return response

            # Handle notifications and responses
            if isinstance(body, dict) and body.get("id") is None:
                return Response(status_code=202)

            # For requests, initiate SSE stream
            return EventSourceResponse(
                self.handle_sse_stream(body),
                headers={"Content-Type": "text/event-stream"},
            )

        @app.get("/mcp")
        async def handle_get(
            request: Request,
            last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
            accept: str = Header(...),
        ):
            if "text/event-stream" not in accept:
                raise HTTPException(status_code=405, detail="SSE not supported")

            return EventSourceResponse(self.handle_sse_stream(None, last_event_id))

    async def handle_sse_stream(
        self,
        request_body: Optional[Union[Dict, List]],
        last_event_id: Optional[str] = None,
    ):
        """Handle SSE stream for both POST and GET requests"""
        # TODO: Implement actual message handling and streaming
        # This is a placeholder that sends a test message
        yield {
            "event": "message",
            "id": str(uuid.uuid4()),
            "data": json.dumps({"jsonrpc": "2.0", "method": "test", "params": {}}),
        }
        await asyncio.sleep(1)  # Keep connection alive
