"""
We need to cover 2 use-cases here:

1. The Action Server UI.
    - In this case a cookie with a session id is created (both in the 
      oauth urls as well as in the index)
    - A pop-up browser window is opened at `/oauth2/login`
    - The user provides his information
    - A `/oauth2/redirect` request is received as a callback, at which
      point the session id will be connected to the token and a
      call to the action server should automatically add the required
      tokens when the action is called (and refresh them as needed). 
      
2. VSCode
    - In this case the VSCode would start the action server 
      and open `/oauth2/login` in a browser. 
      -- When doing the login a `client_callback` must be passed so that the token
      can be retrieved later.
      -- The `reference_id` must also be passed so that the login state can be checked
      later on.
    - After the `/oauth2/redirect` is triggered by the browser the `callback_url`
      will be triggered in succession.
"""
import datetime
import json
import logging
import os
import typing
from functools import lru_cache, partial
from pathlib import Path
from typing import Any, Iterable, Optional

import requests
from fastapi.routing import APIRouter
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

if typing.TYPE_CHECKING:
    from requests_oauthlib import OAuth2Session  # type: ignore

    from sema4ai.action_server._models import OAuth2UserData

oauth2_api_router = APIRouter(prefix="/oauth2")

log = logging.getLogger(__name__)


class OAuth2ProviderSettings(BaseModel):
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None
    server: Optional[str] = None
    tokenEndpoint: Optional[str] = None
    revocationEndpoint: Optional[str] = None
    authorizationEndpoint: Optional[str] = None
    authParams: Optional[dict[str, str]] = None
    additionalHeaders: Optional[dict[str, str]] = None


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
}

_in_flight_state: dict = {}


class StatusResponseModel(BaseModel):
    success: bool
    error_message: Optional[str] = ""


@oauth2_api_router.get("/logout")
async def oauth2_logout(
    provider: str,
    request: Request,
    response: Response,
    reference_id: str = "",
) -> StatusResponseModel:
    from sema4ai.action_server._encryption import decrypt_simple
    from sema4ai.action_server._models import OAuth2UserData, get_db
    from sema4ai.action_server._user_session import (
        referenced_session_scope,
        session_scope,
    )

    use_session_scope: Any
    if reference_id:
        # Note: will only be able to access a user session created with:
        # create_user_session(external=True).
        use_session_scope = referenced_session_scope(reference_id)
    else:
        # The "provide_access_token" is only respected if reference_id
        # was given (in which case it was an external request and not an
        # automatically created session).
        use_session_scope = session_scope(request)

    db = get_db()

    with use_session_scope as session, db.connect():
        session.response = response
        where, values = db.where_from_dict(
            dict(user_session_id=session.session_id, provider=provider)
        )

        current_oauth2_user_data: list[OAuth2UserData] = db.all(
            OAuth2UserData, where=where, values=values
        )

        with db.transaction():
            db.delete_where(OAuth2UserData, where=where, values=values)

        if current_oauth2_user_data:
            settings = _get_oauthlib2_provider_settings(provider)
            revoke_url = settings.revocationEndpoint
            if revoke_url:
                for user_data in current_oauth2_user_data:
                    for token_attr in ["access_token", "refresh_token"]:
                        token = getattr(user_data, token_attr)
                        if not token:
                            continue
                        try:
                            token = typing.cast(str, decrypt_simple(token))
                        except Exception:
                            log.critical(
                                f"It was not possible to decrypt the {token_attr}, secrets won't be revoked in server."
                            )
                            continue
                        if not token:
                            continue

                        payload = {"token": token}
                        headers = {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Authorization": f"Bearer {token}",
                        }

                        p = requests.post(revoke_url, data=payload, headers=headers)

                        if p.status_code != 200:
                            log.critical(
                                f"Failed to revoke token. Status code: {p.status_code}, Response: {p.text}"
                            )

        response_model = StatusResponseModel(success=True)

    return response_model


@oauth2_api_router.get("/login")
async def oauth2_login(
    provider: str,
    scopes: str,
    request: Request,
    reference_id: str = "",
    callback_url: str = "",
) -> RedirectResponse:
    """
    Args:
        provider: The provider (google, github, etc)
        scopes: A space-separated list of scopes requested.
        reference_id: If given the authentication info will later on be accessible through
            the given `reference_id`
    """
    log.info("/oauth2/login. Provider: %s, Scopes: %s", provider, scopes)
    if "," in scopes:
        log.info(
            "comma (,) found in scopes. Note that it's expected that a space separator is used."
        )
    from requests_oauthlib import OAuth2Session  # type: ignore

    from sema4ai.action_server._database import Database
    from sema4ai.action_server._models import get_db
    from sema4ai.action_server._settings import get_settings
    from sema4ai.action_server._user_session import session_scope

    if callback_url:

        def is_localhost(url):
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            return (
                parsed_url.scheme and parsed_url.scheme.lower() in ("http", "https")
            ) and (
                parsed_url.netloc == "localhost"
                or parsed_url.netloc.startswith("127.")
                or parsed_url.netloc == "::1"
            )

        if not is_localhost(callback_url):
            message = (
                f"Can only accept callbacks in the localhost. Found: {callback_url}"
            )
            log.critical(message)
            raise AssertionError(message)

    db: Database = get_db()

    with db.connect(), db.transaction(), session_scope(request) as session:
        settings = _get_oauthlib2_provider_settings(provider)
        app_settings = get_settings()
        base_url = app_settings.base_url
        assert base_url, "Internal error: `base_url` not available from app settings."

        client_id = settings.clientId
        redirect_uri = f"{base_url}/oauth2/redirect/"
        auth_url = settings.authorizationEndpoint

        oauth2_session = OAuth2Session(
            client_id=client_id, redirect_uri=redirect_uri, scope=scopes.split(" ")
        )

        params = settings.authParams or {}

        authorization_url, state = oauth2_session.authorization_url(auth_url, **params)
        session.set_session_data(
            f"oauth_state-${state}",
            {
                "provider": provider,
                "reference_id": reference_id,
                "callback_url": callback_url,
            },
            expires_at=datetime.datetime.now() + datetime.timedelta(minutes=15),
        )

        response = RedirectResponse(url=authorization_url)
        session.response = response
        return response


class OAuth2StatusResponseForProvider(BaseModel):
    scopes: Optional[list[str]]
    expires_at: str  # iso-formatted datetime or empty string
    access_token: Optional[str]  # Only available if not an automatic id
    metadata: Optional[dict]  # Metadata which may be available


@oauth2_api_router.get("/status")
async def oauth2_status(
    request: Request,
    response: "Response",
    reference_id: str = "",
    refresh_tokens: bool = False,
    force_refresh: bool = False,
    provide_access_token: bool = False,
) -> dict[str, OAuth2StatusResponseForProvider]:
    """
    Collects the current status for the OAuth2 (either for the
    current session or the passed `reference_id`).
    """
    import asyncio.futures

    from sema4ai.action_server._encryption import decrypt_simple
    from sema4ai.action_server._models import OAuth2UserData, get_db
    from sema4ai.action_server._robo_utils.run_in_thread import run_in_thread_asyncio
    from sema4ai.action_server._user_session import (
        referenced_session_scope,
        session_scope,
    )

    use_session_scope: Any
    if reference_id:
        # Note: will only be able to access a user session created with:
        # create_user_session(external=True).
        use_session_scope = referenced_session_scope(reference_id)
    else:
        # The "provide_access_token" is only respected if reference_id
        # was given (in which case it was an external request and not an
        # automatically created session).
        use_session_scope = session_scope(request)
        provide_access_token = False

    provider_to_status: dict[str, OAuth2StatusResponseForProvider] = {}
    db = get_db()

    with use_session_scope as session, db.connect():
        session.response = response
        where, values = db.where_from_dict(dict(user_session_id=session.session_id))

        current_oauth2_user_data = db.all(OAuth2UserData, where=where, values=values)
        must_renew: list[OAuth2UserData] = []
        if refresh_tokens:
            if force_refresh:
                must_renew = current_oauth2_user_data
            else:
                must_renew = [x for x in current_oauth2_user_data if _should_renew(x)]

        if must_renew:
            use_id = session.session_id
            # Renew in a thread.
            futures: list[asyncio.futures.Future[OAuth2UserData]] = [
                run_in_thread_asyncio(partial(_refresh_token, use_id, x))
                for x in must_renew
            ]

            for f in futures:
                _new_oauth2_data = await f

            # Get the new results after it was renewed.
            current_oauth2_user_data = db.all(
                OAuth2UserData, where=where, values=values
            )

        for oauth2_user_data in current_oauth2_user_data:
            settings = _get_oauthlib2_provider_settings(oauth2_user_data.provider)
            access_token = None
            if provide_access_token:
                try:
                    access_token = typing.cast(
                        str, decrypt_simple(oauth2_user_data.access_token)
                    )
                except Exception:
                    log.critical(
                        "It was not possible to decrypt the access token, secrets won't be sent"
                        "(the storage key has probably changed, so, a new login will be needed)."
                    )
            metadata: dict = {}
            if settings.server:
                # Always pass the server if it's available.
                metadata["server"] = settings.server

            provider_to_status[
                oauth2_user_data.provider
            ] = OAuth2StatusResponseForProvider(
                expires_at=oauth2_user_data.expires_at,  # may be empty
                scopes=json.loads(oauth2_user_data.scopes)
                if oauth2_user_data.scopes
                else None,
                access_token=access_token,
                metadata=metadata,
            )

    return provider_to_status


def refresh_tokens(
    use_id: str, oauth2_user_data_lst: Iterable["OAuth2UserData"]
) -> list["OAuth2UserData"]:
    """
    Args:
        use_id: The id of the session to which the tokens are related to.
        oauth2_user_data_lst: The OAuth2 information that should have the
            access_token refreshed.
    """
    new_lst: list["OAuth2UserData"] = []

    for oauth2_user_data in oauth2_user_data_lst:
        assert oauth2_user_data.user_session_id == use_id

        if _should_renew(oauth2_user_data):
            new_lst.append(_refresh_token(use_id, oauth2_user_data))
        else:
            new_lst.append(oauth2_user_data)

    return new_lst


def _refresh_token(use_id: str, oauth2_user_data: "OAuth2UserData") -> "OAuth2UserData":
    """
    Refreshes the tokens from the input user data (in the given session).

    Updates the information in the database and returns a new OAuth2UserData
    instance with the updated values (the input instance will be unchanged).
    """
    from sema4ai.action_server._encryption import decrypt_simple

    settings = _get_oauthlib2_provider_settings(oauth2_user_data.provider)
    oauth2_session = _create_oauth2_session(oauth2_user_data.provider)
    client_secret = settings.clientSecret
    client_id = settings.clientId
    token_url = settings.tokenEndpoint

    if not oauth2_user_data.refresh_token:
        raise RuntimeError(
            f"Unable to refresh token because a 'refresh_token' was not available. Provider: {oauth2_user_data.provider}."
        )

    try:
        refresh_token = decrypt_simple(oauth2_user_data.refresh_token)
    except Exception:
        raise RuntimeError(
            "It was not possible to decrypt the refresh_token "
            "(the storage key has probably changed, so, a new login will be needed)."
        )

    token = oauth2_session.refresh_token(
        token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )

    return _update_db_with_token(use_id, oauth2_user_data.provider, token)


def _should_renew(oauth2_user_data: "OAuth2UserData") -> bool:
    """
    Args:
        oauth2_user_data: The data to be checked

    Returns:
        True if the oauth2 access_token should be renewed and False otherwise.
    """
    from sema4ai.action_server._user_session import iso_to_datetime

    if not oauth2_user_data.refresh_token:
        # Unable to renew in this case as there's no refresh_token to renew.
        return False

    if not oauth2_user_data.expires_at:
        return False

    d = iso_to_datetime(oauth2_user_data.expires_at)
    now = datetime.datetime.now()
    refresh_newer_than = now - datetime.timedelta(minutes=10)
    return d > refresh_newer_than


class CreatedReferenceId(BaseModel):
    reference_id: str


@oauth2_api_router.get("/create-reference-id")
async def create_reference_id() -> CreatedReferenceId:
    """
    Creates a new reference ID (using this reference it's later possible
    to obtain the access_token and query the state of the OAuth2 authentication).
    """
    from sema4ai.action_server._user_session import create_user_session

    response = CreatedReferenceId(reference_id=create_user_session(external=True).id)
    return response


def _create_oauth2_session(
    provider: str, state: Optional[str] = None
) -> "OAuth2Session":
    from requests_oauthlib import OAuth2Session  # type: ignore

    from sema4ai.action_server._settings import get_settings

    settings = _get_oauthlib2_provider_settings(provider)

    client_id = settings.clientId
    app_settings = get_settings()
    base_url = app_settings.base_url
    assert base_url, "Internal error: `base_url` not available from app settings."
    redirect_uri = f"{base_url}/oauth2/redirect/"

    oauth2_session = OAuth2Session(
        client_id=client_id, state=state, redirect_uri=redirect_uri
    )
    return oauth2_session


def _update_db_with_token(use_id: str, provider: str, token) -> "OAuth2UserData":
    from sema4ai.action_server._database import Database
    from sema4ai.action_server._encryption import encrypt_simple
    from sema4ai.action_server._models import OAuth2UserData, get_db
    from sema4ai.action_server._user_session import datetime_to_iso

    access_token = token.get("access_token", "")

    if not token.scope:  # It may not be available (Hubspot)
        scopes = ""
    else:
        if " " in token.scope:
            # This seems to be the correct in the RFC.
            scopes_lst = token.scope.split(" ")
        elif "," in token.scope:
            # Slack gives this.
            scopes_lst = token.scope.split(",")
        else:
            scopes_lst = [token.scope]
        scopes = json.dumps(scopes_lst)

    refresh_token = token.get("refresh_token", "")
    if not refresh_token:
        log.info(
            f"No `refresh_token` provided when authenticating with provider: {provider} (a refresh will not be possible)."
        )
    expires_at = token.get("expires_at", "")
    if expires_at:
        expires_at = datetime_to_iso(expires_at)
    else:
        log.info(
            f"No `expires_at` provided when authenticating with provider: {provider} (a refresh will not be possible)."
        )

        # TODO: Allow users to configure in config file if not available?
        # https://www.rfc-editor.org/rfc/rfc6749.html says:
        # expires_in: RECOMMENDED.
        # If omitted, the authorization server SHOULD provide the
        # expiration time via other means or document the default value

    token_type = token.get("token_type")

    data = OAuth2UserData(
        user_session_id=use_id,
        provider=provider,
        refresh_token=encrypt_simple(refresh_token) if refresh_token else refresh_token,
        access_token=encrypt_simple(access_token) if access_token else access_token,
        expires_at=expires_at,
        token_type=token_type,
        scopes=scopes,
    )

    db: Database = get_db()
    with db.connect(), db.transaction():
        db.insert_or_update(data, ["user_session_id", "provider"])

    return data


@oauth2_api_router.get("/redirect")
async def oauth2_redirect(request: Request, state: str = "") -> HTMLResponse:
    """
    Callback that should've been registered in the OAuth2 callback to
    complete the authentication flow.
    """

    from sema4ai.action_server._user_session import session_scope

    with session_scope(request) as session:
        oauth_state = session.get_session_data(f"oauth_state-${state}")
        if not oauth_state:
            raise RuntimeError(
                "Internal error: session data invalid to make OAuth2 authentication."
            )

        if not isinstance(oauth_state, dict):
            raise RuntimeError(
                "Internal error: saved session data is invalid to make OAuth2 authentication."
            )

        provider = typing.cast(str, oauth_state["provider"])
        reference_id = typing.cast(str, oauth_state["reference_id"])
        callback_url = typing.cast(str, oauth_state["callback_url"])

        assert isinstance(provider, str)
        assert isinstance(callback_url, str)

        settings = _get_oauthlib2_provider_settings(provider)
        client_secret = settings.clientSecret
        token_url = settings.tokenEndpoint

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        if settings.additionalHeaders:
            headers.update(settings.additionalHeaders)

        oauth2_session = _create_oauth2_session(provider, state)
        token = oauth2_session.fetch_token(
            token_url,
            client_secret=client_secret,
            authorization_response=str(request.url),
            headers=headers,
            include_client_id=True,
        )

        use_id = reference_id
        if not use_id:
            use_id = session.session_id

        data = _update_db_with_token(use_id, provider, token)

        if reference_id and callback_url:
            result = requests.post(
                callback_url,
                headers=headers,
                json={
                    "provider": provider,
                    "reference_id": reference_id,
                    "access_token": token.get("access_token", ""),
                    "expires_at": data.expires_at,
                    "token_type": data.token_type,
                    "scopes": data.scopes,
                },
            )
            result.raise_for_status()

        response = HTMLResponse(
            """
<html>
<body>

    <h3>OAuth2 authentication flow completed!</h3><br/><br/>
    <div id="message">
        Please wait, this window should be closed shortly...<br/>
        <br/>
        If it's not closed automatically, something unexpected happened.<br/>
        In this case, please close this window and restart the login.<br/>
        <br/>
        <br/>
    </div>

    <script>
        if(window.opener){
            // When used as a pop-up in a browser (Action Server UI), we can
            // ask the parent to finish the process.
            window.opener.finishOAuth2();
        }else {
            // Note: this doesn't really work if a browser was opened to do it in
            // python with `webbrowser.open`.
            // window.close() in -- firefox says: 
            //     Scripts may only close windows that were opened by a script.
            const messageDiv = document.getElementById("message");
            messageDiv.innerHTML = `
                <b>This window may now be closed.</b>
                <br/><br/>
                `;
        }
    </script>
    
</body>
</html>
"""
        )
        session.response = response

    return response


@lru_cache
def _get_oauthlib2_global_settings(
    oauth2_settings_file: Optional[str] = None,
) -> dict[str, Any]:
    """
    Provides the global settings for doing an OAuth2 authentication
    (should be a mapping of provider->provider info).

    Note that it's cached and its result should not be mutated.
    """
    import yaml

    from sema4ai.action_server._settings import get_settings

    if not oauth2_settings_file:
        app_settings = get_settings()
        if not app_settings.use_https:
            os.environ[
                "OAUTHLIB_INSECURE_TRANSPORT"
            ] = "1"  # allow localhost `http` redirects

        oauth2_settings_file = app_settings.oauth2_settings

    if not oauth2_settings_file:
        raise RuntimeError(
            "Unable to make OAuth2 login because the oauth2 settings file is not set."
        )

    p = Path(oauth2_settings_file)
    if not p.exists():
        raise RuntimeError(
            f"Unable to make OAuth2 login because the oauth2 settings file: {oauth2_settings_file} does not exist."
        )

    with p.open("rb") as stream:
        contents = yaml.safe_load(stream)

    if not isinstance(contents, dict):
        raise RuntimeError(
            f"Expected {oauth2_settings_file} to be a yaml with a mapping of provider name->provider info."
        )
    return contents


def _get_oauthlib2_provider_settings(
    provider: str, oauth2_settings_file: Optional[str] = None
) -> OAuth2ProviderSettingsResolved:
    """
    Gets the OAuth2 settings to be used for a given provider.
    """
    contents = _get_oauthlib2_global_settings(oauth2_settings_file)

    settings = contents.get(provider)

    if not settings:
        raise RuntimeError(
            f"Found no OAuth2 info for provider {provider} in {oauth2_settings_file}."
        )

    if not isinstance(settings, dict):
        raise RuntimeError(
            f"Expected OAuth2 info for provider {provider} in {oauth2_settings_file} to be a mapping with the provider info."
        )

    if "clientId" not in settings:
        raise RuntimeError(
            f"Expected 'clientId' to be in OAuth2 settings for {provider}."
        )
    if "clientSecret" not in settings:
        raise RuntimeError(
            f"Expected 'clientSecret' to be in OAuth2 settings for {provider}."
        )
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
                f"Expected '{attr}' to be in OAuth2 settings for {provider}."
            )

        if value.startswith("/"):
            if not ret.server:
                raise RuntimeError(
                    f"As the '{attr}' is relative, the 'server' setting must be provided in the OAuth2 settings for {provider}"
                )

            use_server = ret.server
            if use_server.endswith("/"):
                use_server = use_server[:-1]

            value = f"{use_server}{value}"
            setattr(ret, attr, value)

    return ret


def _deep_update(dict1, dict2):
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
