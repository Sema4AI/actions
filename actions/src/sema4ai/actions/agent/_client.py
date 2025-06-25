import json
import logging
import os
import platform
from copy import copy
from urllib.parse import urljoin, urlparse

import sema4ai_http

log = logging.getLogger(__name__)


class _AgentAPIClient:
    API_ENDPOINT_VERSIONS = ["v1", "v2"]
    API_PATH_PREFIX = "api/public"
    ENV_VAR_NAME = "SEMA4AI_AGENTS_SERVICE_URL"
    PID_FILE_NAME = "agent-server.pid"
    CONNECTION_TIMEOUT = 1

    def __init__(self, api_key: str | None = None):
        """Initialize the AgentServerClient."""
        self.api_url = self._get_api_url()
        self.api_key = api_key
        log.info(f"API URL: {self.api_url}")

        # Determine if we're running in cloud environment
        self.is_cloud = self._is_cloud_environment()

        if self.is_cloud:
            log.info("Running in cloud environment - will use Bearer authentication")
        else:
            log.info("Running in local environment - no authentication required")

        self._check_health()

    def _get_api_url(self) -> str:
        """Determine the correct API URL by checking environment variable or agent-server.pid file
        and testing API availability.

        Returns:
            str: The working API URL

        Raises:
            ValueError: If no API server is responding
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
        raise ValueError("Could not connect to agent server")

    def _try_get_url_from_environment(self) -> str | None:
        env_url = os.getenv(self.ENV_VAR_NAME)
        if not env_url:
            return None

        return self._test_api_endpoints(env_url)

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
                    return self._test_api_endpoints(base_url)
                else:
                    return None
        except Exception as e:
            log.debug(f"Failed to read PID file: {e}")
            return None

    def _test_api_endpoints(self, base_url: str) -> str | None:
        """Test different API endpoint versions to find a working one.

        Args:
            base_url: Base URL to test

        Returns:
            str | None: Working API URL if found, None otherwise
        """
        for version in self.API_ENDPOINT_VERSIONS:
            endpoint_url = f"{base_url}/{self.API_PATH_PREFIX}/{version}"
            if self._is_url_accessible(endpoint_url):
                return endpoint_url
        return None

    def _is_url_accessible(self, url: str) -> bool:
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme not in ("http", "https"):
                return False

            sema4ai_http.get(url, timeout=self.CONNECTION_TIMEOUT)
            return True
        except Exception:
            return False

    def _get_pid_file_path(self) -> str:
        """Get the path to the agent-server.pid file based on the operating system.

        Returns:
            str: Path to the PID file
        """
        home_dir = os.path.expanduser("~")

        # Determine OS-specific path
        if platform.system() == "Windows":
            # Windows path: C:\Users\<username>\AppData\Local\sema4ai\sema4ai-studio\agent-server.pid
            return os.path.join(
                home_dir,
                "AppData",
                "Local",
                "sema4ai",
                "sema4ai-studio",
                self.PID_FILE_NAME,
            )
        else:
            # macOS/Linux path: ~/.sema4ai/sema4ai-studio/agent-server.pid
            return os.path.join(
                home_dir, ".sema4ai", "sema4ai-studio", self.PID_FILE_NAME
            )

    def _check_health(self) -> None:
        response = self.request(path="ok", method="GET")
        if response.status_code != 200:
            raise ValueError(
                f"Failed to connect to the Sema4 Agent API: {response.status_code} {response.text}"
            )

    def request(
        self,
        path: str,
        method="GET",
        json_data: dict | None = None,
        headers: dict | None = None,
    ) -> sema4ai_http.ResponseWrapper:
        """Make an API request with common error handling.

        Args:
            path: API endpoint path
            method: HTTP method (GET, POST, or DELETE)
            json_data: Optional JSON payload for POST requests
            headers: Optional additional headers

        Returns:
            sema4ai_http.ResponseWrapper object

        Raises:
           urllib3.exceptions.ConnectionError: If the request fails or returns an error status
        """
        url = urljoin(self.api_url + "/", path)

        # Initialize headers
        request_headers = copy(headers) if headers else {}

        # Add Bearer token for cloud environments if API key is provided
        if self.is_cloud and self.api_key:
            request_headers["Authorization"] = f"Bearer {self.api_key}"

        if method == "GET":
            response = sema4ai_http.get(url, json=json_data, headers=request_headers)
        elif method == "POST":
            response = sema4ai_http.post(url, json=json_data, headers=request_headers)
        elif method == "DELETE":
            response = sema4ai_http.delete(url, headers=request_headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        return response

    def _is_cloud_environment(self) -> bool:
        """Determine if we're running in a cloud environment based on URL patterns.

        Returns:
            bool: True if running in cloud, False otherwise
        """
        if not self.api_url:
            raise ValueError("No API URL detected - cannot determine environment")

        parsed_url = urlparse(self.api_url)
        return parsed_url.scheme == "https" or "router.ten" in parsed_url.netloc
