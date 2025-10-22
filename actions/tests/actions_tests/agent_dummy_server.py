import json
import time
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
            elif isinstance(body, bytes):
                self.wfile.write(body)
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

        # Handle /api/v2/data-frames endpoint (list dataframes)
        elif (
            len(path_parts) == 3
            and path_parts[0] == "api"
            and path_parts[1] == "v2"
            and path_parts[2] == "data-frames"
        ):
            # Extract query parameters
            query_params = urllib.parse.parse_qs(parsed_path.query)
            thread_id = query_params.get("thread_id", [None])[0]

            # Store the request for testing
            self._server.last_request = {
                "path": self.path,
                "thread_id": thread_id,
                "method": "GET",
            }

            # Return mock dataframe list
            response = [
                {
                    "name": "sales_data",
                    "description": "Q1 sales records",
                    "num_rows": 100,
                    "num_columns": 5,
                    "column_headers": ["date", "product", "quantity", "price", "total"],
                },
                {
                    "name": "customer_data",
                    "description": None,
                    "num_rows": 50,
                    "num_columns": 3,
                    "column_headers": ["id", "name", "email"],
                },
            ]

            self._send_response(
                200,
                headers={"Content-Type": "application/json"},
                body=response,
            )
            return

        # Handle /api/v2/data-frames/{name} endpoint (get specific dataframe)
        elif (
            len(path_parts) == 4
            and path_parts[0] == "api"
            and path_parts[1] == "v2"
            and path_parts[2] == "data-frames"
        ):
            dataframe_name = path_parts[3]

            # Extract query parameters
            query_params = urllib.parse.parse_qs(parsed_path.query)
            thread_id = query_params.get("thread_id", [None])[0]
            limit = int(query_params.get("limit", [10000])[0])
            offset = int(query_params.get("offset", [0])[0])
            column_names = query_params.get("column_names", [None])[0]
            order_by = query_params.get("order_by", [None])[0]
            format_type = query_params.get("format", ["json"])[0]

            # Store the request for testing
            self._server.last_request = {
                "path": self.path,
                "thread_id": thread_id,
                "method": "GET",
                "dataframe_name": dataframe_name,
                "limit": limit,
                "offset": offset,
                "column_names": column_names,
                "order_by": order_by,
                "format": format_type,
            }

            # Handle 404 case for non-existent dataframes
            if dataframe_name == "nonexistent_df":
                self._send_response(
                    404,
                    headers={"Content-Type": "application/json"},
                    body={"error": "DataFrame not found"},
                )
                return

            # Return mock dataframe data based on requested format
            if format_type == "parquet":
                # For testing, we'll always return JSON even when Parquet is requested
                # This simulates a server that doesn't support Parquet format
                response = {
                    "columns": ["product", "sales"],
                    "rows": [["Widget", 100], ["Gadget", 200]],
                    "name": dataframe_name,
                    "description": f"Data for {dataframe_name}",
                }

                self._send_response(
                    200,
                    headers={"Content-Type": "application/json"},
                    body=response,
                )
                return
            else:
                # Default JSON response
                response = {
                    "columns": ["product", "sales"],
                    "rows": [["Widget", 100], ["Gadget", 200]],
                    "name": dataframe_name,
                    "description": f"Data for {dataframe_name}",
                }

                self._send_response(
                    200,
                    headers={"Content-Type": "application/json"},
                    body=response,
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
        # Use port 0 to let the OS assign a free port (like files_dummy_server.py)
        self.server = HTTPServer(("localhost", 0), _AgentDummyServer)
        self.server._server_instance = self  # Store reference to self
        self.port = self.server.server_port

        self.server.serve_forever()

    def start(self):
        self.thread = Thread(target=self._start_in_thread, daemon=True)
        self.thread.start()
        # Give the server a moment to start
        time.sleep(0.1)

    def get_port(self):
        return self.port

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)
