import json
import os
import typing

import requests

if typing.TYPE_CHECKING:
    from sema4ai.action_server._rcc import Rcc

session = requests.Session()


def initialize_session(rcc: "Rcc"):
    """
    Initialize the requests session with RCC profile settings.

    Args:
        rcc: Rcc instance to load the profiles from.
    """
    global session

    result = rcc.get_network_settings()
    if result.success and result.result:
        network_settings = json.loads(result.result)
    else:
        raise Exception("Failed to load RCC profile settings")

    network = network_settings["network"] if "network" in network_settings else None
    http_proxy = network["http-proxy"] if network and "http-proxy" in network else None
    https_proxy = (
        network["https-proxy"] if network and "https-proxy" in network else None
    )

    certificates = (
        network_settings["certificates"] if "certificates" in network_settings else None
    )
    verify_ssl = (
        certificates["verify-ssl"]
        if certificates and "verify-ssl" in certificates
        else True
    )

    if http_proxy:
        os.environ["http_proxy"] = http_proxy
        os.environ["HTTP_PROXY"] = http_proxy
        session.proxies["http"] = http_proxy

    if https_proxy:
        os.environ["https_proxy"] = https_proxy
        os.environ["HTTPS_PROXY"] = https_proxy
        session.proxies["https"] = https_proxy

    if not verify_ssl:
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        os.environ["CURL_CA_BUNDLE"] = ""

    session.verify = verify_ssl
