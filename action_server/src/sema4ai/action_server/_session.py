import logging
import os
import ssl
from typing import TYPE_CHECKING, Optional

import requests
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter

if TYPE_CHECKING:
    from sema4ai.action_server._rcc import Rcc


log = logging.getLogger(__name__)


class RccCertificateSettings(BaseModel):
    verify_ssl: Optional[bool] = Field(default=None, alias="verify-ssl")
    legacy_renegotiation_allowed: Optional[bool] = Field(
        default=None, alias="legacy-renegotiation-allowed"
    )


class RccNetworkSettings(BaseModel):
    http_proxy: Optional[str] = Field(default=None, alias="http-proxy")
    https_proxy: Optional[str] = Field(default=None, alias="https-proxy")
    no_proxy: Optional[str] = Field(default=None, alias="no-proxy")


class RccSettings(BaseModel):
    certificates: Optional[RccCertificateSettings] = None
    network: Optional[RccNetworkSettings] = None


class _SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)


session = requests.Session()


def _create_ssl_adapter(legacy_renegotiation_allowed: bool) -> _SSLAdapter:
    custom_ssl_context = ssl.create_default_context()

    if legacy_renegotiation_allowed:
        if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
            custom_ssl_context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        else:
            log.error(
                "Legacy renegotiation not enabled, the SSL module does not support the option"
            )
    else:
        if hasattr(ssl, "OP_NO_RENEGOTIATION"):
            custom_ssl_context.options |= ssl.OP_NO_RENEGOTIATION
        else:
            log.debug(
                "legacy renegotiation not disabled, the ssl module does not support the option"
            )

    return _SSLAdapter(ssl_context=custom_ssl_context)


def initialize_session(rcc: "Rcc"):
    """
    Initialize the requests session with RCC profile settings.

    Args:
        rcc: Rcc instance to load the profiles from.
    """
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    global session

    result = rcc.get_network_settings()
    if result.success and result.result:
        try:
            settings = RccSettings.model_validate_json(result.result, strict=False)
        except ValueError:
            log.critical(
                bold_red(f"Failed to read RCC profile settings: {result.result}")
            )
            return
    else:
        log.critical(bold_red("Failed to load RCC profile settings"))
        return

    http_proxy = settings.network.http_proxy if settings.network else None
    https_proxy = settings.network.https_proxy if settings.network else None
    no_proxy = settings.network.no_proxy if settings.network else None
    verify_ssl = (
        settings.certificates.verify_ssl
        if settings.certificates is not None
        and settings.certificates.verify_ssl is not None
        else True
    )
    legacy_renegotiation_allowed = (
        settings.certificates.legacy_renegotiation_allowed
        if settings.certificates
        and settings.certificates.legacy_renegotiation_allowed is not None
        else False
    )

    if http_proxy:
        os.environ["http_proxy"] = http_proxy
        os.environ["HTTP_PROXY"] = http_proxy
        session.proxies["http"] = http_proxy

    if https_proxy:
        os.environ["https_proxy"] = https_proxy
        os.environ["HTTPS_PROXY"] = https_proxy
        session.proxies["https"] = https_proxy

    if no_proxy:
        os.environ["NO_PROXY"] = no_proxy

    if not verify_ssl:
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        os.environ["CURL_CA_BUNDLE"] = ""

    session.verify = verify_ssl

    ssl_adapter = _create_ssl_adapter(legacy_renegotiation_allowed)
    session.mount("https://", ssl_adapter)
