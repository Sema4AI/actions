import json
import logging
import os
import platform
from copy import copy
from urllib.parse import urlencode, urljoin, urlparse

import sema4ai_http
from sema4ai.actions._action import get_x_action_invocation_context

log = logging.getLogger(__name__)


class AgentApiClientException(Exception):
    """Exception raised when the Agent API client encounters an error."""


class _AgentAPIClient:
    PID_FILE_NAME = "agent-server.pid"

    def __init__(self):
        """Initialize the AgentServerClient."""
        self.api_url = self._get_api_url()

        log.info(f"API URL: {self.api_url}")

    def _get_api_url(self) -> str:
        """Determine the correct API URL by checking environment variable or agent-server.pid file
        and testing API availability.

        Returns:
            str: The working API URL

        Raises:
            AgentApiClientException: If no API server is responding
        """
        # Try to get URL from environment variable first
        api_url = self._try_get_url_from_environment()
        if api_url:
            return api_url

        # Try to get URL from PID file as fallback
        api_url = self._try_get_url_from_pid_file()
        if api_url:
            return api_url

        # No working API server found
        raise AgentApiClientException("Could not connect to agent server")

    def _try_get_url_from_environment(self) -> str | None:
        env_url = os.getenv("SEMA4AI_AGENTS_SERVICE_URL")
        if not env_url:
            return None

        if self._is_url_accessible(f"{env_url}/api/v2/ok"):
            return env_url
        return None

    def _try_get_url_from_pid_file(self) -> str | None:
        pid_file_path = self._get_pid_file_path()
        log.debug(f"Looking for agent server in PID file: {pid_file_path}")

        try:
            if not os.path.exists(pid_file_path):
                return None

            with open(pid_file_path, "r") as f:
                server_info = json.loads(f.read())
                base_url = server_info.get("base_url")
                if base_url:
                    endpoint_url = f"{base_url}/api/v2"
                    if self._is_url_accessible(f"{endpoint_url}/ok"):
                        return endpoint_url
                else:
                    return None
        except Exception as e:
            log.debug(f"Failed to read PID file: {e}")
            return None
        return None

    def _is_url_accessible(self, url: str) -> bool:
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme not in ("http", "https"):
                return False

            sema4ai_http.get(url, timeout=1).raise_for_status()
            return True
        except Exception:
            return False

    def _get_pid_file_path(self) -> str:
        """Get the path to the agent-server.pid file based on the operating system.

        Returns:
            str: Path to the PID file
        """
        # Determine OS-specific path
        if platform.system() == "Windows":
            # Windows path: C:\Users\<username>\AppData\Local\sema4ai\sema4ai-studio\agent-server.pid
            local_app_data = os.environ.get("LOCALAPPDATA")
            if not local_app_data:
                # Fallback to default Windows AppData path
                local_app_data = os.path.join(
                    os.path.expanduser("~"), "AppData", "Local"
                )

            return os.path.join(
                local_app_data,
                "sema4ai",
                "sema4ai-studio",
                self.PID_FILE_NAME,
            )
        else:
            # macOS/Linux path: ~/.sema4ai/sema4ai-studio/agent-server.pid
            return os.path.join(
                os.path.expanduser("~"),
                ".sema4ai",
                "sema4ai-studio",
                self.PID_FILE_NAME,
            )

    def request(
        self,
        path: str,
        method="GET",
        json_data: dict | None = None,
        headers: dict | None = None,
        query_params: dict | None = None,
    ) -> sema4ai_http.ResponseWrapper:
        """Make an API request with common error handling.

        Args:
            path: API endpoint path
            method: HTTP method (GET, POST, or DELETE)
            json_data: Optional JSON payload for POST requests
            headers: Optional additional headers
            query_params: Optional query parameters

        Returns:
            sema4ai_http.ResponseWrapper object

        Raises:
           ValueError: for unsupported HTTP methods
           AgentApiClientException: for HTTP errors
           ConnectionError: If the request fails
        """
        url = self.api_url
        if not url.endswith("/"):
            url += "/"
        url = urljoin(url, path)

        request_headers = copy(headers) if headers else {}

        request_headers[
            "x-action-invocation-context"
        ] = get_x_action_invocation_context()

        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        log.debug(
            f"Request URL: {url}",
            extra={"json_data": json_data, "request_headers": request_headers},
        )
        if method == "GET":
            response = sema4ai_http.get(url, json=json_data, headers=request_headers)
        elif method == "POST":
            response = sema4ai_http.post(url, json=json_data, headers=request_headers)
        elif method == "DELETE":
            response = sema4ai_http.delete(url, headers=request_headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if response.status_code not in (200, 201):
            error_msg = f"HTTP {response.status_code}"
            if response.text:
                error_msg += f": {response.text}"
            else:
                error_msg += f": {response.reason or 'Unknown error'}"

            raise AgentApiClientException(error_msg)

        return response
