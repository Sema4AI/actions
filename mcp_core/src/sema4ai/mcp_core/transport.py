import asyncio
import json
import uuid
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse


# JSON-RPC message types
class JsonRpcMessage(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Union[Dict, List]] = None
    result: Optional[Union[Dict, List, str, int, float, bool, None]] = None
    error: Optional[Dict] = None


class McpTransport:
    def __init__(self, app: FastAPI) -> None:
        self.sessions: Dict[str, Dict] = {}

        @app.post("/mcp")
        async def handle_post(
            request: Request,
            mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
            accept: str = Header(...),
        ):
            # Validate Accept header
            if "application/json" not in accept and "text/event-stream" not in accept:
                raise HTTPException(status_code=400, detail="Invalid Accept header")

            # Read and parse the request body
            body = await request.json()

            # Handle initialization request
            if isinstance(body, dict) and body.get("method") == "initialize":
                session_id = str(uuid.uuid4())
                self.sessions[session_id] = {"streams": set()}
                response = JSONResponse(
                    content={"jsonrpc": "2.0", "id": body.get("id"), "result": {}},
                    headers={"Mcp-Session-Id": session_id},
                )
                return response

            # Validate session if provided
            if mcp_session_id and mcp_session_id not in self.sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            # Handle notifications and responses
            if isinstance(body, dict) and body.get("id") is None:
                return Response(status_code=202)

            # For requests, initiate SSE stream
            return EventSourceResponse(
                self.handle_sse_stream(body, mcp_session_id),
                headers={"Content-Type": "text/event-stream"},
            )

        @app.get("/mcp")
        async def handle_get(
            request: Request,
            mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
            last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
            accept: str = Header(...),
        ):
            if "text/event-stream" not in accept:
                raise HTTPException(status_code=405, detail="SSE not supported")

            if mcp_session_id and mcp_session_id not in self.sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            return EventSourceResponse(
                self.handle_sse_stream(None, mcp_session_id, last_event_id)
            )

        @app.delete("/mcp")
        async def handle_delete(
            mcp_session_id: str = Header(..., alias="Mcp-Session-Id"),
        ):
            if mcp_session_id in self.sessions:
                del self.sessions[mcp_session_id]
            return Response(status_code=200)

    async def handle_sse_stream(
        self,
        request_body: Optional[Union[Dict, List]],
        session_id: Optional[str],
        last_event_id: Optional[str] = None,
    ):
        """Handle SSE stream for both POST and GET requests"""
        if session_id:
            self.sessions[session_id]["streams"].add(asyncio.current_task())
            try:
                # TODO: Implement actual message handling and streaming
                # This is a placeholder that sends a test message
                yield {
                    "event": "message",
                    "id": str(uuid.uuid4()),
                    "data": json.dumps(
                        {"jsonrpc": "2.0", "method": "test", "params": {}}
                    ),
                }
                await asyncio.sleep(1)  # Keep connection alive
            finally:
                if session_id in self.sessions:
                    self.sessions[session_id]["streams"].remove(asyncio.current_task())
        else:
            yield {
                "event": "error",
                "data": json.dumps({"error": "No session ID provided"}),
            }
