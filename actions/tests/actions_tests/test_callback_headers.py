from __future__ import annotations

from dataclasses import dataclass

import pytest

from sema4ai.actions._action import set_current_requests_contexts
from sema4ai.actions._action_context import RequestContexts
from sema4ai.actions._callback import (
    get_request_header,
    normalize_callback_base_url,
    should_propagate_auth_header,
)
from sema4ai.actions._request import Request


def _bind_request_context(headers: dict[str, str]) -> None:
    request = Request.model_validate({"headers": headers})
    set_current_requests_contexts(RequestContexts(request))


@pytest.fixture(autouse=True)
def _clear_request_context():
    set_current_requests_contexts(None)
    yield
    set_current_requests_contexts(None)


def test_get_request_header_from_bound_context() -> None:
    _bind_request_context({"x-ags-base-url": "http://localhost:8001/api/v2"})
    assert get_request_header("x-ags-base-url") == "http://localhost:8001/api/v2"
    assert get_request_header("x-missing") is None


def test_normalize_callback_base_url() -> None:
    assert normalize_callback_base_url("http://localhost:8001/api/v2/") == "http://localhost:8001/api/v2"
    assert (
        normalize_callback_base_url("http://localhost:8001/tenants/spar/agents", "/api/v2")
        == "http://localhost:8001/tenants/spar/agents/api/v2/"
    )
    assert (
        normalize_callback_base_url("http://localhost:8001/api/v2", "/api/v2")
        == "http://localhost:8001/api/v2/"
    )


def test_should_propagate_auth_header() -> None:
    assert (
        should_propagate_auth_header(
            "http://localhost:8001/tenants/spar/agents/api/v2/threads/t/files",
            "http://localhost:8001/tenants/spar/agents/api/v2",
        )
        is True
    )
    assert (
        should_propagate_auth_header(
            "https://storage.googleapis.com/presigned-url",
            "http://localhost:8001/tenants/spar/agents/api/v2",
        )
        is False
    )


@dataclass
class _ChatResponse:
    status: int
    data: bytes
    _json_data: dict

    def json(self):
        return self._json_data


@pytest.mark.parametrize(
    ("download_url", "expects_auth_on_download"),
    [
        ("http://localhost:8001/tenants/spar/agents/api/v2/download", True),
        ("https://storage.example.com/presigned-get", False),
    ],
)
def test_chat_client_callback_auth_propagation(
    monkeypatch, download_url: str, expects_auth_on_download: bool
) -> None:
    from sema4ai.actions.chat import _client
    import sema4ai_http

    _bind_request_context(
        {
            "x-ags-base-url": "http://localhost:8001/tenants/spar/agents/api/v2",
            "x-ags-callback": "Bearer callback-token",
            "x-action-invocation-context": "e30=",
        }
    )

    calls: list[tuple[str, dict[str, str] | None]] = []

    def fake_get(url, *args, **kwargs):
        headers = kwargs.get("headers")
        calls.append((url, headers))
        if url.endswith("/file-by-ref"):
            return _ChatResponse(
                status=200,
                data=b"",
                _json_data={"file_url": download_url},
            )
        return _ChatResponse(status=200, data=b"downloaded", _json_data={})

    monkeypatch.setattr(sema4ai_http, "get", fake_get)

    client = _client._Client()
    assert client.get_bytes("file-ref", "thread-1") == b"downloaded"

    # Initial callback call (to Agent Server/Workroom) always gets callback auth.
    assert calls[0][1] is not None
    assert calls[0][1].get("Authorization") == "Bearer callback-token"
    if expects_auth_on_download:
        assert calls[1][1] is not None
        assert calls[1][1].get("Authorization") == "Bearer callback-token"
    else:
        assert calls[1][1] in (None, {})


@dataclass
class _AgentResponse:
    status_code: int
    text: str = ""
    reason: str = ""


def _patch_agent_get_capture(monkeypatch) -> dict[str, str]:
    import sema4ai_http

    captured: dict[str, str] = {}

    def fake_get(url, *args, **kwargs):
        headers = kwargs.get("headers", {})
        captured.update(headers)
        return _AgentResponse(status_code=200)

    monkeypatch.setattr(sema4ai_http, "get", fake_get)
    return captured


@pytest.mark.parametrize(
    ("request_path", "expects_auth"),
    [
        ("ok", True),
        ("https://example.com/path", False),
    ],
)
def test_agent_client_callback_auth_propagation(
    monkeypatch, request_path: str, expects_auth: bool
) -> None:
    from sema4ai.actions.agent._client import _AgentAPIClient

    _bind_request_context(
        {
            "x-ags-base-url": "http://localhost:8001/tenants/spar/agents",
            "x-ags-callback": "Bearer callback-token",
            "x-action-invocation-context": "e30=",
        }
    )

    captured = _patch_agent_get_capture(monkeypatch)

    client = _AgentAPIClient()
    assert client.api_url == "http://localhost:8001/tenants/spar/agents/api/v2/"
    client.request(request_path, method="GET")
    if expects_auth:
        assert captured.get("Authorization") == "Bearer callback-token"
    else:
        assert "Authorization" not in captured
