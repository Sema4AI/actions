import logging
import os
from typing import TYPE_CHECKING, Optional

import requests
from pydantic import BaseModel, Field

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


session = requests.Session()


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

    if legacy_renegotiation_allowed:
        # The robocorp-truststore package uses this environment variable to
        # check if the legacy renegotiation is allowed and will enable it for
        # all requests
        os.environ["RC_TLS_LEGACY_RENEGOTIATION_ALLOWED"] = "True"
