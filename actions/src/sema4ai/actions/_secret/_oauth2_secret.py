from typing import Generic, TypeVar

# Definition (internal to sema4ai-actions)
ProviderT = TypeVar("ProviderT", bound=str)  # Restrict Provider to string
ScopesT = TypeVar("ScopesT", bound=list)

JSONValue = dict[str, "JSONValue"] | list["JSONValue"] | str | int | float | bool | None


class OAuth2Secret(Generic[ProviderT, ScopesT]):
    def __init__(
        self,
        provider: ProviderT,
        scopes: ScopesT,
        token: str,
        metadata: JSONValue = None,
    ):
        self._provider = provider
        self._scopes = scopes
        self._token = token
        self._metadata = metadata

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def scopes(self) -> ScopesT:
        return self._scopes

    @property
    def token(self) -> str:
        return self._token

    @property
    def metadata(self) -> JSONValue:
        return self._metadata
