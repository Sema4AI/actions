from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass
class OAuth2ProviderSettings:
    mode: str | None = None  # custom/sema4ai
    name: str | None = None
    clientId: str | None = None
    clientSecret: str | None = None
    server: str | None = None
    tokenEndpoint: str | None = None
    revocationEndpoint: str | None = None
    authorizationEndpoint: str | None = None
    authParams: dict[str, str] | None = None
    additionalHeaders: dict[str, str] | None = None
    requiresHttps: bool | None = False

    # Some replacement functions to keep pydantic API without actually
    # relying on it.
    def model_dump(self) -> dict:
        import copy

        ret = {}
        for field_name, field_info in self.__class__.__dataclass_fields__.items():
            value = getattr(self, field_name)

            field_type = field_info.type
            if field_type == str:
                ret[field_name] = value
            else:
                ret[field_name] = copy.copy(value)

        return ret

    @classmethod
    def model_validate(cls, dct):
        try:
            settings = cls(**dct)
        except Exception as e:
            raise RuntimeError(f"Invalid OAuth2 settings. Original error: {str(e)}")

        for field_name, field_info in cls.__dataclass_fields__.items():
            field_type = field_info.type
            value = getattr(settings, field_name)

            if field_name in ("authParams", "additionalHeaders"):
                # Optional[dict[str, str] is NOT ok for isinstance: do it manually
                if value is not None:
                    if not isinstance(value, dict):
                        raise TypeError(
                            f"Field '{field_name}' expects type {field_type}, got {type(value)} instead"
                        )

                    for k, v in value.items():
                        if not isinstance(k, str):
                            raise TypeError(
                                f"Found bad key type in dict[str, str]: {k}"
                            )
                        if not isinstance(v, str):
                            raise TypeError(
                                f"Found bad value type in dict[str, str]: {v}"
                            )

            elif not isinstance(
                value, field_type
            ):  # Optional[str] is ok for isinstance
                raise TypeError(
                    f"Field '{field_name}' expects type {field_type}, got {type(value)} instead"
                )
        return settings


class OAuth2ProviderSettingsResolved(OAuth2ProviderSettings):
    # Same as OAuth2ProviderSettings, but signals that the
    # settings are resolved at this point (i.e.: relative urls
    # are absolute and validations were done).
    pass


_DEFAULT_OAUTH2_SETTINGS: dict[str, OAuth2ProviderSettings] = {
    "hubspot": OAuth2ProviderSettings(
        server="https://api.hubapi.com/oauth/v1",
        tokenEndpoint="/token",
        authorizationEndpoint="https://app-eu1.hubspot.com/oauth/authorize",
    ),
    "google": OAuth2ProviderSettings(
        server="https://oauth2.googleapis.com",
        tokenEndpoint="/token",
        revocationEndpoint="/revoke",
        authorizationEndpoint="https://accounts.google.com/o/oauth2/v2/auth",
        authParams={
            "access_type": "offline",  # Force Google OAuth API to return a refresh token https://developers.google.com/identity/protocols/oauth2/web-server#request-parameter-access_type
            "prompt": "select_account",  # Force Google OAuth UI to display account choice https://developers.google.com/identity/protocols/oauth2/web-server#request-parameter-prompt
        },
    ),
    "github": OAuth2ProviderSettings(
        server="https://github.com",
        authorizationEndpoint="/login/oauth/authorize",
        tokenEndpoint="/login/oauth/access_token",
    ),
    "slack": OAuth2ProviderSettings(
        server="https://slack.com",
        tokenEndpoint="/api/oauth.v2.access",
        authorizationEndpoint="/oauth/v2/authorize",
    ),
    "zendesk": OAuth2ProviderSettings(
        tokenEndpoint="/oauth/tokens",
        authorizationEndpoint="/oauth/authorizations/new",
        # server=settings.server,
    ),
    "microsoft": OAuth2ProviderSettings(
        authorizationEndpoint="/oauth2/v2.0/authorize",
        tokenEndpoint="/oauth2/v2.0/token",
        # server=settings.server,
    ),
    "salesforce": OAuth2ProviderSettings(
        server="https://login.salesforce.com",
        tokenEndpoint="/services/oauth2/token",
        revocationEndpoint="/services/oauth2/revoke",
        authorizationEndpoint="/services/oauth2/authorize",
    ),
}


def get_oauthlib2_user_settings(
    oauth2_settings_file: str,
) -> dict[str, Any]:
    """
    Provides the global settings for doing an OAuth2 authentication
    (should be a mapping of provider->provider info).
    """
    import yaml

    p = Path(oauth2_settings_file)
    if not p.exists():
        raise RuntimeError(
            f"Unable to make OAuth2 login because the oauth2 settings file: {oauth2_settings_file} does not exist."
        )

    try:
        with p.open("rb") as stream:
            contents = yaml.safe_load(stream)
    except Exception as e:
        raise RuntimeError(
            f"Unable to load file: {oauth2_settings_file} as YAML.\nDetails: {e}"
        )

    if not isinstance(contents, dict):
        raise RuntimeError(
            f"Expected {oauth2_settings_file} to be a yaml with a mapping of oauth2Config->providers->provider name->provider info."
        )

    return contents


_SEMA4AI_PROVIDED_OAUTH2_CONFIG_GETTER = None


def set_sema4ai_provided_oauth2_config_getter(getter: Callable[[], str]) -> None:
    """
    Sets a function that will be called to get the Sema4.ai provided oauth2
    config.

    Usually something running: `action-server oauth2 sema4ai-config`.
    """
    global _SEMA4AI_PROVIDED_OAUTH2_CONFIG_GETTER
    _SEMA4AI_PROVIDED_OAUTH2_CONFIG_GETTER = getter


def get_sema4ai_provided_oauth2_config() -> str:
    if _SEMA4AI_PROVIDED_OAUTH2_CONFIG_GETTER is None:
        raise RuntimeError(
            "Sema4.ai provided oauth2 config getter not set -- note: `action-server oauth2 sema4ai-config` can be used to get it."
        )
    return _SEMA4AI_PROVIDED_OAUTH2_CONFIG_GETTER()


def _get_oauthlib2_sema4ai_settings(provider: str) -> dict:
    import yaml

    contents = get_sema4ai_provided_oauth2_config()
    dct = yaml.safe_load(contents)
    if not isinstance(dct, dict):
        raise RuntimeError("Expected the Sema4.ai oauth2 config to be a yaml.")

    oauth2_config = _require("oauth2Config", dct)
    providers = _require("providers", oauth2_config)

    settings = providers.get(provider)

    if not settings:
        raise RuntimeError(
            f"Found no OAuth2 info for provider {provider} in sema4ai settings (either the provider name is mistyped or it's an unsupported provider and thus must be 'custom')."
        )

    if not isinstance(settings, dict):
        raise RuntimeError(f"Expected {provider} info to be a dict.")
    return settings


def _require(key: str, dct: dict) -> Any:
    found = dct.get(key, None)
    if found is None:
        raise RuntimeError(f"Expected '{key}' to be in Oauth2 settings.")
    return found


def get_oauthlib2_provider_settings(
    provider: str, oauth2_settings_file: str
) -> OAuth2ProviderSettingsResolved:
    """
    Gets the OAuth2 settings to be used for a given provider.
    """
    contents = get_oauthlib2_user_settings(oauth2_settings_file)
    oauth2_config = _require("oauth2Config", contents)
    providers = _require("providers", oauth2_config)

    settings = providers.get(provider)

    if not settings:
        raise RuntimeError(
            f"Found no OAuth2 info for provider {provider} in {oauth2_settings_file}."
        )

    if not isinstance(settings, dict):
        raise RuntimeError(
            f"Expected OAuth2 info for provider {provider} in {oauth2_settings_file} to be a mapping with the provider info."
        )

    mode = settings.get("mode")
    if not mode:
        raise RuntimeError(
            f"'mode' not specified for provider: {provider} (expected either 'sema4ai' or 'custom' to be set as the mode)."
        )

    if mode not in ("custom", "sema4ai"):
        raise RuntimeError(
            f"Invalid 'mode': {mode!r} specified for provider: {provider} (expected either 'sema4ai' or 'custom' to be set as the mode)."
        )

    if mode == "sema4ai":
        settings = _get_oauthlib2_sema4ai_settings(provider)

    if "clientId" not in settings:
        raise RuntimeError(
            f"Expected 'clientId' to be in OAuth2 settings for {provider} (mode: {mode})."
        )

    # clientSecret is optional (if not given uses pkce to make the authentication)
    # if "clientSecret" not in settings:
    #     raise RuntimeError(
    #         f"Expected 'clientSecret' to be in OAuth2 settings for {provider} (mode: {mode})."
    #     )

    default_settings = _DEFAULT_OAUTH2_SETTINGS.get(provider)
    if not default_settings:
        default_settings = OAuth2ProviderSettings()

    as_dict = _deep_update(default_settings.model_dump(), settings)

    ret = OAuth2ProviderSettingsResolved.model_validate(as_dict)

    for attr in ("authorizationEndpoint", "tokenEndpoint", "revocationEndpoint"):
        value = getattr(ret, attr)
        if not value:
            if attr == "revocationEndpoint":
                # This one is optional
                continue

            raise RuntimeError(
                f"Expected '{attr}' to be in OAuth2 settings for {provider} (mode: {mode})."
            )

        if value.startswith("/"):
            if not ret.server:
                raise RuntimeError(
                    f"As the '{attr}' is relative, the 'server' setting must be provided in the OAuth2 settings for {provider} (mode: {mode})"
                )

            use_server = ret.server
            if use_server.endswith("/"):
                use_server = use_server[:-1]

            value = f"{use_server}{value}"
            setattr(ret, attr, value)

    return ret


def _deep_update(dict1: dict, dict2: dict) -> dict:
    """
    Merges two dictionaries recursively.

    Returns:
        A new dictionary with the merged content.
    """
    merged = dict1.copy()
    for key, value in dict2.items():
        if key in dict1:
            if isinstance(value, dict) and isinstance(dict1[key], dict):
                merged[key] = _deep_update(dict1[key], value)
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged
