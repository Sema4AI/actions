from typing import List, Literal, TypedDict

from typing_extensions import NotRequired

ProxyAuthenticationType = TypedDict(
    "ProxyAuthenticationType",
    {
        "auth-type": Literal["os-certificate", "none", "oauth"],
        "oauth-token-url": str,
        "oauth-client-id": str,
        "oauth-client-secret": str,
        "other-oauth-params": str,
    },
    total=False,
)


ProxySettingsType = TypedDict(
    "ProxySettingsType",
    {
        "authentication": ProxyAuthenticationType,
        "no-proxy": str,
        "https-proxy": str,
        "http-proxy": str,
    },
)


ProfileType = TypedDict(
    "ProfileType",
    {
        "name": str,
        "description": str,
        "disable-ssl": bool,
        "proxy-settings": NotRequired[ProxySettingsType],
    },
)


NetworkConfigType = TypedDict(
    "NetworkConfigType",
    {
        "spec-version": str,
        "current-profile": str,
        "profiles": List[ProfileType],
    },
)

class EmptyDictType(TypedDict):
    pass