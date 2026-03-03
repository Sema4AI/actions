from logging import getLogger
from urllib.parse import urlparse

from sema4ai.actions._action import get_current_requests_contexts

logger = getLogger(__name__)


def get_request_header(header_name: str) -> str | None:
    # MCP hosts are expected to bind RequestContexts for each tool request.
    # Callback headers are always read from that bound request context.
    request_contexts = get_current_requests_contexts()
    if request_contexts is None or request_contexts.request is None:
        return None
    value = request_contexts.request.headers.get(header_name)
    if value:
        return str(value).strip() or None
    return None


def normalize_callback_base_url(
    callback_base_url: str, required_suffix: str | None = None
) -> str:
    # Callback base URLs may arrive with/without trailing slash and suffix.
    # Normalize once so callers can safely append endpoint paths.
    normalized = callback_base_url.rstrip("/")
    if not required_suffix:
        return normalized

    required_suffix = required_suffix.rstrip("/")
    if normalized.endswith(required_suffix):
        return f"{normalized}/"
    return f"{normalized}{required_suffix}/"


def should_propagate_auth_header(target_url: str, base_url: str) -> bool:
    # Forward callback auth only to same-host Agent Server/Workroom endpoints.
    # Example: don't forward callback auth to external presigned storage URLs.
    parsed_target = urlparse(target_url)
    parsed_base = urlparse(base_url)

    if (
        parsed_target.scheme in {"http", "https"}
        and parsed_base.netloc
        and parsed_target.netloc
        and parsed_target.netloc != parsed_base.netloc
    ):
        return False
    return True


class OnExitContextManager:
    def __init__(self, on_exit):
        self.on_exit = on_exit

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.on_exit()


class Callback:
    """
    Note that it's thread safe to register/unregister callbacks while callbacks
    are being notified, but it's not thread-safe to register/unregister at the
    same time in multiple threads.
    """

    def __init__(self, reversed=False, raise_exceptions=False):
        self.raise_exceptions = raise_exceptions
        self._reversed = reversed
        self._callbacks = ()

    def register(self, callback):
        self._callbacks = self._callbacks + (callback,)

        # Enable using as a context manager to automatically call the unregister.
        return OnExitContextManager(lambda: self.unregister(callback))

    def unregister(self, callback):
        self._callbacks = tuple(x for x in self._callbacks if x != callback)

    def __len__(self):
        return len(self._callbacks)

    def __call__(self, *args, **kwargs):
        if self._reversed:
            iter_in = reversed(self._callbacks)
        else:
            iter_in = self._callbacks
        for c in iter_in:
            try:
                c(*args, **kwargs)
            except Exception as e:
                from sema4ai.actions._exceptions import ActionsCollectError

                if not isinstance(e, ActionsCollectError) or not self.raise_exceptions:
                    logger.exception(f"Error calling: {c}.")

                if self.raise_exceptions:
                    raise
