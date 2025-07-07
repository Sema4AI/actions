import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class _AgentDummyServer(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self._server = server._server_instance
        super().__init__(request, client_address, server)

    def _send_response(self, status_code=200, headers=None, body=None):
        self.send_response(status_code)
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        if body:
            if isinstance(body, str):
                self.wfile.write(body.encode("utf-8"))
            else:
                self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.split("/")[1:]

        # Handle /api/v2/ok endpoint for URL accessibility check
        if (
            len(path_parts) == 3
            and path_parts[0] == "api"
            and path_parts[1] == "v2"
            and path_parts[2] == "ok"
        ):
            self._send_response(
                200,
                headers={"Content-Type": "application/json"},
                body={"status": "ok"},
            )
            return
        else:
            self._send_response(
                404,
                headers={"Content-Type": "application/json"},
                body={"error": "Not Found"},
            )
            return

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.split("/")[1:]

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            request_body = json.loads(post_data)
        except json.JSONDecodeError:
            self._send_response(
                400,
                headers={"Content-Type": "application/json"},
                body={"error": "Invalid JSON"},
            )
            return

        # /api/v2/prompts/generate
        if (
            len(path_parts) == 4
            and path_parts[0] == "api"
            and path_parts[1] == "v2"
            and path_parts[2] == "prompts"
            and path_parts[3] == "generate"
        ):
            # Extract query parameters
            query_params = urllib.parse.parse_qs(parsed_path.query)
            thread_id = query_params.get("thread_id", [None])[0]
            agent_id = query_params.get("agent_id", [None])[0]

            # Store the request for testing
            self._server.last_request = {
                "body": request_body,
                "thread_id": thread_id,
                "agent_id": agent_id,
                "path": self.path,  # Store the full request path
            }

            # Return the expected response format
            response = {
                "content": [
                    {
                        "kind": "text",
                        "text": "The random number I picked between 1 and 100 is 73.",
                    }
                ],
                "role": "agent",
                "raw_response": None,
                "stop_reason": None,
                "usage": {
                    "input_tokens": 115,
                    "output_tokens": 16,
                    "total_tokens": 131,
                },
                "metrics": {},
                "metadata": {},
                "additional_response_fields": {},
            }

            self._send_response(
                200, headers={"Content-Type": "application/json"}, body=response
            )
            return
        else:
            self._send_response(
                404,
                headers={"Content-Type": "application/json"},
                body={"error": "Not Found"},
            )
            return


class AgentDummyServer:
    def __init__(self):
        self.server = None
        self.thread = None
        self.port = None
        self.last_request = None

    def _start_in_thread(self):
        # Find an available port
        for port in range(8000, 8100):
            try:
                self.server = HTTPServer(("localhost", port), _AgentDummyServer)
                self.server._server_instance = self  # Store reference to self
                self.port = port
                break
            except OSError:
                continue

        if self.server is None:
            raise RuntimeError("Could not find an available port")

        self.server.serve_forever()

    def start(self):
        self.thread = Thread(target=self._start_in_thread, daemon=True)
        self.thread.start()
        # Give the server a moment to start
        import time

        time.sleep(0.1)

    def get_port(self):
        return self.port

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)
