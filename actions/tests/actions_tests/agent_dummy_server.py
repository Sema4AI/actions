import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Shared test data
SAMPLE_AGENTS = [
    {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Test Agent 1",
        "description": "desc",
        "mode": "chat",
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Test Agent 2",
        "description": "desc2",
        "mode": "assistant",
    },
]

SAMPLE_CONVERSATIONS = [
    {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "name": "Test Conversation 1",
        "agent_id": "550e8400-e29b-41d4-a716-446655440001",
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "name": "Test Conversation 2",
        "agent_id": "550e8400-e29b-41d4-a716-446655440001",
    },
]

SAMPLE_MESSAGES = {
    "next": None,
    "has_more": False,
    "data": [
        {
            "content": [
                {
                    "content_id": "d23db9b1-29a8-4162-8d31-fe8c9b6b5418",
                    "kind": "text",
                    "complete": True,
                    "text": "What is the hottest day?",
                    "citations": [],
                }
            ],
            "role": "user",
            "complete": True,
            "commited": True,
            "created_at": "2025-06-23T15:05:49.316317Z",
            "updated_at": "2025-06-23T15:05:49.316324Z",
            "agent_metadata": {},
            "server_metadata": {},
            "parent_run_id": None,
            "message_id": "9713ed17-cad7-43ae-9560-9115e291c8a1",
        },
        {
            "content": [
                {
                    "content_id": "bc1a2976-a21c-4dba-90f1-a3cda8c08e62",
                    "kind": "thought",
                    "complete": True,
                    "thought": 'The user\'s question, "What is the hottest day?", lacks context about location, timeframe, or data source. I need clarification to give a helpful answer.',
                },
                {
                    "content_id": "9b3bb4ea-3efe-4a63-8f97-464d11861996",
                    "kind": "text",
                    "complete": True,
                    "text": 'Could you clarify what location, year, or data you\'re referring to when you ask "What is the hottest day?" For example, are you asking about the hottest day ever recorded on Earth, in a specific city, or for a recent time period?',
                    "citations": [],
                },
            ],
            "role": "agent",
            "complete": True,
            "commited": True,
            "created_at": "2025-06-23T15:05:50.330965Z",
            "updated_at": "2025-06-23T15:05:50.330970Z",
            "agent_metadata": {},
            "server_metadata": {},
            "parent_run_id": "01485d83-d05d-4e7f-8b9e-8b7e57de8e68",
            "message_id": "76495210-1071-436d-a66c-ea29792b3506",
        },
    ],
}


class AgentDummyHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(json.dumps(data).encode("utf-8"))))
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
        self.wfile.flush()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/public/v1/agents":
            if "name" in query:
                if query["name"][0] == "Test Agent 1":
                    self._send_json(
                        {
                            "data": [SAMPLE_AGENTS[0]],
                            "next": None,
                            "has_more": False,
                        }
                    )
                    return
                else:
                    self._send_json({"data": [], "next": None, "has_more": False})
            else:
                self._send_json(
                    {
                        "data": SAMPLE_AGENTS,
                        "next": None,
                        "has_more": False,
                    }
                )
                return

        if path.endswith("/conversations"):
            if "name" in query:
                name = query["name"][0]
                if name == "Test Conversation 1":
                    self._send_json(
                        {
                            "data": [SAMPLE_CONVERSATIONS[0]],
                            "next": None,
                            "has_more": False,
                        }
                    )
                else:
                    self._send_json({"data": [], "next": None, "has_more": False})
            else:
                self._send_json(
                    {
                        "data": SAMPLE_CONVERSATIONS,
                        "next": None,
                        "has_more": False,
                    }
                )
            return

        if "/messages" in path:
            self._send_json(SAMPLE_MESSAGES)
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Get request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body) if body else {}

        if path.endswith("/conversations"):
            parts = path.split("/")
            agent_id = parts[
                5
            ]  # /api/public/v1/agents/{agent_id}/conversations -> parts[5] is agent_id
            conversation_name = data.get("name", "New Conversation")

            self._send_json(
                {
                    "id": str(uuid.uuid4()),
                    "name": conversation_name,
                    "agent_id": agent_id,
                },
                status=201,
            )
            return

        if "/messages" in path:
            parts = path.split("/")
            agent_id = parts[
                5
            ]  # /api/public/v1/agents/{agent_id}/conversations/{conversation_id}/messages -> parts[5] is agent_id
            message_content = data.get("content", "")

            self._send_json(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message_content,
                            "timestamp": "2023-01-01T00:00:00Z",
                        },
                        {
                            "role": "agent",
                            "content": "Agent reply",
                            "timestamp": "2023-01-01T00:00:01Z",
                        },
                    ]
                }
            )
            return

        # Default 404 for unknown endpoints
        self._send_json({"error": "Not found"}, status=404)


class AgentDummyServer:
    def __init__(self, host="127.0.0.1", port=0):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the dummy server in a separate thread."""
        self.server = HTTPServer((self.host, self.port), AgentDummyHandler)
        self.port = self.server.server_port

        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the dummy server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=1)

    def get_port(self):
        """Get the port the server is running on."""
        return self.port
