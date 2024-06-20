import json
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from sema4ai.action_server._rcc import ActionResult


@patch("sema4ai.action_server._session.session")
def test_session_empty_settings(session_mock: MagicMock):
    from sema4ai.action_server._session import initialize_session

    type(session_mock).proxies = PropertyMock(return_value={})

    rcc = Mock()
    rcc.get_network_settings.return_value = ActionResult(True, None, json.dumps({}))

    initialize_session(rcc)

    assert session_mock.verify is True
    assert hasattr(session_mock.proxies, "http") is False
    assert hasattr(session_mock.proxies, "https") is False


@patch("sema4ai.action_server._session.session")
def test_session_set_proxies(session_mock: MagicMock):
    from sema4ai.action_server._session import initialize_session

    type(session_mock).proxies = PropertyMock(return_value={})

    settings = {
        "network": {"http-proxy": "http://testing", "https-proxy": "https://testing"}
    }

    rcc = Mock()
    rcc.get_network_settings.return_value = ActionResult(
        True, None, json.dumps(settings)
    )

    initialize_session(rcc)

    assert session_mock.verify is True
    assert session_mock.proxies["http"] == "http://testing"
    assert session_mock.proxies["https"] == "https://testing"


@patch("sema4ai.action_server._session.session")
def test_session_disable_ssl_verify(session_mock: MagicMock):
    from sema4ai.action_server._session import initialize_session

    type(session_mock).proxies = PropertyMock(return_value={})

    settings = {"certificates": {"verify-ssl": False}}

    rcc = Mock()
    rcc.get_network_settings.return_value = ActionResult(
        True, None, json.dumps(settings)
    )

    initialize_session(rcc)

    assert session_mock.verify is False
    assert hasattr(session_mock.proxies, "http") is False
    assert hasattr(session_mock.proxies, "https") is False


@patch("sema4ai.action_server._session.session")
def test_session_fail_to_read_settings(session_mock: MagicMock):
    from sema4ai.action_server._session import initialize_session

    type(session_mock).proxies = PropertyMock(return_value={})

    rcc = Mock()
    rcc.get_network_settings.return_value = ActionResult(False, None, json.dumps({}))

    initialize_session(rcc)

    assert hasattr(session_mock.proxies, "http") is False
    assert hasattr(session_mock.proxies, "https") is False
