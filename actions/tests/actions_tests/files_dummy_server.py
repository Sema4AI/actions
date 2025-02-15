import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class _SimpleFileServer(BaseHTTPRequestHandler):
    def __init__(self, files_path: Path, server: "FilesDummyServer", *args, **kwargs):
        self.files_path = files_path
        self.files_path.mkdir(parents=True, exist_ok=True)
        self._server = server
        super().__init__(*args, **kwargs)

    def _send_response(self, status_code=200, headers=None, body=None):
        self.send_response(status_code)
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(body.encode("utf-8"))

    def _check_action_invocation_context_header(self):
        return "x-action-invocation-context" in self.headers

    def do_GET(self):
        from urllib.parse import parse_qs

        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.split("/")[1:]

        # /threads/:threadId/file-by-ref?file_ref=fileRef
        if (
            len(path_parts) == 3
            and path_parts[0] == "threads"
            and path_parts[2] == "file-by-ref"
        ):
            file_ref = parse_qs(parsed_path.query).get("file_ref", [None])[0]
            if not file_ref:
                self._send_response(
                    400,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({"error": "Missing file_ref"}),
                )
                return

            if not self._check_action_invocation_context_header():
                self._send_response(
                    400,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps(
                        {"error": "Missing x-action-invocation-context header"}
                    ),
                )
                return

            if self._server.write_to_local:
                # Dummy file URL generation
                file_path = self.files_path / file_ref
                response_body = json.dumps({"file_url": file_path.as_uri()})
                self._send_response(
                    200,
                    headers={"Content-Type": "application/json"},
                    body=response_body,
                )
            else:
                # Get the presigned get url
                url = f"http://localhost:{self._server.get_port()}/download"
                response_body = json.dumps({"file_url": url})
                self._send_response(
                    200,
                    headers={"Content-Type": "application/json"},
                    body=response_body,
                )
        # /download
        elif len(path_parts) == 1 and path_parts[0] == "download":
            self._send_response(
                200,
                headers={"Content-Type": "application/json"},
                body="content-gotten-from-download",
            )
            return
        else:
            self._send_response(
                404,
                headers={"Content-Type": "application/json"},
                body=json.dumps({"error": "Not Found"}),
            )
            return

    def do_POST(self):
        import sema4ai_http

        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.split("/")[1:]

        content_length = int(self.headers.get("Content-Length", 0))
        content_type = self.headers.get("Content-Type")
        post_data = self.rfile.read(content_length)
        if (
            post_data
            and content_type
            not in [
                "application/octet-stream",
            ]
            and not content_type.startswith("multipart/form-data")
        ):
            try:
                request_body = json.loads(post_data)
            except json.JSONDecodeError:
                self._send_response(
                    400,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({"error": "Invalid JSON"}),
                )
                return
        else:
            request_body = {}

        if len(path_parts) == 1 and path_parts[0] == "upload":
            assert content_type in [
                "application/octet-stream",
            ] or content_type.startswith("multipart/form-data")
            self._send_response(200, headers={"Content-Type": "application/json"})
            return

        if not self._check_action_invocation_context_header():
            self._send_response(
                400,
                headers={"Content-Type": "application/json"},
                body=json.dumps(
                    {"error": "Missing x-action-invocation-context header"}
                ),
            )
            return

        # /threads/:threadId/files/request-upload
        if (
            len(path_parts) == 4
            and path_parts[0] == "threads"
            and path_parts[2] == "files"
            and path_parts[3] == "request-upload"
        ):
            # Handle the file upload initiation
            file_name = request_body.get("file_name")
            file_size = request_body.get("file_size")
            if not file_name:
                self._send_response(
                    400,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({"error": "file_name is required"}),
                )
                return
            if not file_size:
                self._send_response(
                    400,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({"error": "file_size is required"}),
                )
                return

            if self._server.write_to_local:
                file_path = self.files_path / file_name
                url = file_path.as_uri()
                form_data = {}
                file_id = "dummy-file-id"
            else:
                import os

                gen_url = os.environ.get("CONTROL_ROOM_URL_POST")
                gen_headers = os.environ.get("CONTROL_ROOM_AUTH_HEADER")
                file_id = "dummy-file-id"
                if gen_url and gen_headers:
                    gen_url += "/files"
                    headers = {}
                    header_key, header_value = [
                        s.strip() for s in gen_headers.split(":")
                    ]
                    headers[header_key] = header_value
                    response = sema4ai_http.post(
                        gen_url,
                        headers=headers,
                        body=json.dumps(
                            {"file_name": file_name, "file_size": file_size}
                        ).encode("utf-8"),
                    )
                    if response.status != 200:
                        self._send_response(
                            400,
                            headers={"Content-Type": "application/json"},
                            body=json.dumps(
                                {"error": "Unable to create presign post url."}
                            ),
                        )
                    data = response.json()
                    if not data:
                        self._send_response(
                            400,
                            headers={"Content-Type": "application/json"},
                            body=json.dumps(
                                {
                                    "error": f"Empty data received. Found: {response.data}"
                                }
                            ),
                        )
                        return

                    upload_data = data.get("upload")
                    if not upload_data:
                        self._send_response(
                            400,
                            headers={"Content-Type": "application/json"},
                            body=json.dumps(
                                {
                                    "error": f"No upload available. Found: {response.data}"
                                }
                            ),
                        )
                        return
                    url = upload_data["url"]
                    form_data = upload_data["form_data"]
                else:
                    url = f"http://localhost:{self._server.get_port()}/upload"
                    form_data = {"in": "form-data"}

            response_body = json.dumps(
                {
                    "url": url,
                    "form_data": form_data,
                    "file_id": file_id,
                    "file_ref": file_name,
                }
            )
            self._send_response(
                200, headers={"Content-Type": "application/json"}, body=response_body
            )

        # /threads/:threadId/files/confirm-upload
        elif (
            len(path_parts) == 4
            and path_parts[0] == "threads"
            and path_parts[2] == "files"
            and path_parts[3] == "confirm-upload"
        ):
            if request_body:
                if "file_ref" in request_body and "file_id" in request_body:
                    self._send_response(
                        200, headers={"Content-Type": "application/json"}
                    )
                    return
                else:
                    self._send_response(
                        400,
                        headers={"Content-Type": "application/json"},
                        body=json.dumps(
                            {"error": "Missing file_ref o in request body"}
                        ),
                    )
                    return
            else:
                self._send_response(
                    400,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({"error": "Request body must not be empty"}),
                )

        else:
            self._send_response(
                404,
                headers={"Content-Type": "application/json"},
                body=json.dumps({"error": "Not Found"}),
            )


class FilesDummyServer:
    def __init__(self, files_path: Path):
        self.files_path = files_path
        self.write_to_local = True

    def _start_in_thread(self, files_path: Path):
        import threading

        port = 0
        server_address = ("", port)
        httpd = HTTPServer(
            server_address,
            lambda *args, **kwargs: _SimpleFileServer(
                files_path, self, *args, **kwargs
            ),
        )
        print(f"Starting server on port `{httpd.server_port}`")
        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()
        return httpd

    def start(self):
        self.httpd = self._start_in_thread(self.files_path)

    def get_port(self):
        return self.httpd.server_port

    def stop(self):
        self.httpd.shutdown()

    def set_write_to_local(self, write_to_local: bool):
        self.write_to_local = write_to_local
