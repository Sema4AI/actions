FileId = str


class _Client:
    _local_path: str | None = None

    def __init__(self, file_management_url_value: str = ""):
        """

        :param file_management_url_value: If given uses this value for the url, otherwise
        it will use the value of the SEMA4AI_FILE_MANAGEMENT_URL environment variable, if set.
        """
        import os
        import urllib

        from sema4ai.actions import _uris

        if not file_management_url_value:
            file_management_url_value = os.environ.get(
                "SEMA4AI_FILE_MANAGEMENT_URL", ""
            )
            if not file_management_url_value:
                # Backward compatibility
                file_management_url_value = os.environ.get("FILE_MANAGEMENT_URL", "")
        else:
            file_management_url_value = file_management_url_value

        self._url = file_management_url_value
        if not self._url:
            raise ValueError(
                """The SEMA4AI_FILE_MANAGEMENT_URL environment variable is not set.
It must be set either to the service URL (https://localhost:56781/server)
or to a local file system path (file:///path/to/directory) where
files will be stored."""
            )

        parsed_url = urllib.parse.urlparse(self._url)
        self._is_local_mode: bool = parsed_url.scheme == "file"
        if self._is_local_mode:
            self._local_path = _uris.to_fs_path(self._url)
        else:
            self._local_path = None

    def is_local_mode(self) -> bool:
        return self._is_local_mode

    def get_x_action_context(self) -> str:
        return "{}"  # The value is the x-action-context to be used in the header

    def get_bytes(self, filename: str, thread_id: str) -> bytes:
        import os.path
        from pathlib import Path

        from sema4ai.actions import _uris

        if self.is_local_mode():
            # Join the filename to the uri
            assert (
                self._local_path is not None
            ), "Expected local_path to be set when in local mode."
            path = os.path.join(self._local_path, filename)

            p = Path(path)
            return p.read_bytes()
        else:
            # In this case we have the following protocol to follow: a GET request
            # is done to the server (to <_url>/threads) sending the `x-action-context`
            # header with a body with a json with {"file_name": <filename>}. The server
            # will then respond with a body with:
            # response.body {
            # file_url: string // presigned-get URL (could be the path to a local file such as file://c/temp/save-to-file.pdf or an S3 URL)
            # }
            # The client will then do a GET request to the file_url with the content of the file and
            # should later send the upload complete notification.
            import urllib

            import sema4ai_http

            url = f"{self._url}/threads/{thread_id}/file-by-ref"
            headers = {
                "Content-Type": "application/json",
                "x-action-context": self.get_x_action_context(),
            }

            # Send the initial request
            response = sema4ai_http.get(
                url, fields={"file_ref": filename}, headers=headers
            )
            self._raise_for_status(
                f"Failed to get file {filename} from {self._url}.", response, (200,)
            )

            response_data = response.json()
            file_url = response_data.get("file_url")
            if not file_url:
                raise ValueError(
                    f"Failed to get file {filename} from {self._url}. "
                    f"Response: {response_data}"
                )

            parsed_url = urllib.parse.urlparse(file_url)
            if parsed_url.scheme == "file":
                p = Path(_uris.to_fs_path(file_url))
                return p.read_bytes()
            else:
                response = sema4ai_http.get(file_url)
                self._raise_for_status(
                    f"Failed to get file {filename} from {file_url}. ",
                    response,
                    (200,),
                )

                return response.data

    def _raise_for_status(
        self, message: str, response, valid_statuses: tuple[int, ...]
    ):
        if response.status not in valid_statuses:
            raise ValueError(
                f"{message}\nStatus: {response.status}\nBody: {response.data!r}"
            )

    def set_bytes(
        self,
        filename: str,
        content: bytes,
        thread_id: str,
        content_type: str = "application/octet-stream",
    ) -> FileId:
        """
        Returns the file id (which uniquely identifies the file in the file management
        service -- usually it's the same as the filename, but it's possible that it gets
        changed by the file management service to avoid conflicts).
        """
        from pathlib import Path

        from sema4ai.actions import _uris

        if self.is_local_mode():
            # Join the filename to the uri
            assert (
                self._local_path is not None
            ), "Expected local_path to be set when in local mode."
            path = Path(self._local_path) / filename
            if path.exists():
                raise IOError(f"File {filename} already exists.")

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            file_id = filename
        else:
            # In this case we have the following protocol to follow: a POST request
            # is done to the server (to <_url>/threads/:threadId/files/request-upload) sending the `x-action-context`
            # header with a body with a json with {"file_name": <filename>}. The server
            # will then respond with a body with:
            # response.body {
            #   url: string // presigned-POST URL (could be the path to a local file such as file://c/temp/save-to-file.pdf or an S3 URL)
            #   form_data: {} // form data to be used in the PUT request to the url
            #   file_id: string // used for the upload complete notification
            #   file_ref: string // possibly different than the request, to handle duplicate names
            # }
            # The client will then do a POST request to the url with the content of the file and
            # should later send the upload complete notification.
            import json
            import urllib

            import sema4ai_http

            url = f"{self._url}/threads/{thread_id}/files/request-upload"
            headers = {
                "Content-Type": "application/json",
                "x-action-context": self.get_x_action_context(),
            }
            data = json.dumps(
                {"file_name": filename, "file_size": len(content)}
            ).encode("utf-8")

            # Send the initial request
            response = sema4ai_http.post(url, body=data, headers=headers)
            self._raise_for_status(
                f"Failed when requesting upload for file {filename} to {self._url}.",
                response,
                (200,),
            )

            response_data = response.json()
            file_url = response_data["url"]
            file_id = response_data["file_id"]
            file_ref = response_data["file_ref"]

            parsed_url = urllib.parse.urlparse(file_url)
            if parsed_url.scheme == "file":
                # We need to add the file to the local file system
                p = Path(_uris.to_fs_path(file_url))
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
            else:
                # We have a presigned-post URL, upload to it!
                response = sema4ai_http.post(
                    file_url,
                    fields={**response_data["form_data"], "file": (file_ref, content)},
                    headers={"Content-Type": content_type},
                )
                self._raise_for_status(
                    f"Failed when uploading file {filename} to {file_url}.",
                    response,
                    (200, 204),
                )

            # Send the upload complete notification
            url = f"{self._url}/threads/{thread_id}/files/confirm-upload"
            headers = {
                "Content-Type": "application/json",
                "x-action-context": self.get_x_action_context(),
            }
            data = json.dumps({"file_ref": file_ref, "file_id": file_id}).encode(
                "utf-8"
            )
            response = sema4ai_http.post(url, body=data, headers=headers)
            self._raise_for_status(
                f"Failed when completing upload for file {filename} to {self._url}.",
                response,
                (303, 200),
            )

        return file_id
