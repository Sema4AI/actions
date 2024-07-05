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
from pathlib import Path
from typing import Any, Optional

import requests
from fastapi.routing import APIRouter
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

oauth2_api_router = APIRouter(prefix="/oauth2")

log = logging.getLogger(__name__)


class OAuth2ProviderSettings(BaseModel):
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None
    server: Optional[str] = None
    tokenEndpoint: Optional[str] = None
    authorizationEndpoint: Optional[str] = None
    authParams: Optional[dict[str, str]] = None
    additionalHeaders: Optional[dict[str, str]] = None


_DEFAULT_OAUTH2_SETTINGS: dict[str, OAuth2ProviderSettings] = {
    "hubspot": OAuth2ProviderSettings(
        server="https://app-eu1.hubspot.com",
        tokenEndpoint="https://api.hubapi.com/oauth/v1/token",
        authorizationEndpoint="https://app-eu1.hubspot.com/oauth/authorize",
    ),
    "google": OAuth2ProviderSettings(
        server="https://accounts.google.com",
        tokenEndpoint="https://oauth2.googleapis.com/token",
        authorizationEndpoint="https://accounts.google.com/o/oauth2/v2/auth",
        authParams={
            "access_type": "offline",  # Force Google OAuth API to return an refresh token https://developers.google.com/identity/protocols/oauth2/web-server#request-parameter-access_type
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
        tokenEndpoint="https://slack.com/api/oauth.v2.access",
        authorizationEndpoint="https://slack.com/oauth/v2/authorize",
    ),
    "zendesk": OAuth2ProviderSettings(
        tokenEndpoint="/oauth/tokens",
        authorizationEndpoint="/oauth/authorizations/new",
        # server: settings.server,
    ),
}

_in_flight_state: dict = {}


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
        scopes: A comma-separated list of scopes requested.
        reference_id: If given the authentication info will later on be accessible through
            the given `reference_id`
    """
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
        settings = _get_oauthlib_settings(provider)
        app_settings = get_settings()
        base_url = app_settings.base_url
        assert base_url, "Internal error: `base_url` not available from app settings."

        client_id = settings.clientId
        redirect_uri = f"{base_url}/oauth2/redirect/"
        auth_url = settings.authorizationEndpoint

        oauth2_session = OAuth2Session(
            client_id=client_id, redirect_uri=redirect_uri, scope=scopes
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
    scopes: list[str]
    expires_at: str  # iso-formatted datetime


class OAuth2StatusResponseModel(BaseModel):
    provider_to_status: dict[str, OAuth2StatusResponseForProvider]


@oauth2_api_router.get("/status")
async def oauth2_status(
    request: Request, response: "Response", reference_id: str = ""
) -> OAuth2StatusResponseModel:
    """
    Collects the current status for the OAuth2 (either for the
    current session or the passed `reference_id`).
    """
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
        use_session_scope = session_scope(request)

    provider_to_status: dict[str, OAuth2StatusResponseForProvider] = {}
    db = get_db()

    with use_session_scope as session, db.connect():
        session.response = response
        where, values = db.where_from_dict(dict(user_session_id=session.session_id))

        for oauth_user_data in db.all(OAuth2UserData, where=where, values=values):
            provider_to_status[
                oauth_user_data.provider
            ] = OAuth2StatusResponseForProvider(
                expires_at=oauth_user_data.expires_at,
                scopes=json.loads(oauth_user_data.scopes),
            )

    status = OAuth2StatusResponseModel(provider_to_status=provider_to_status)
    return status


class CreatedReferenceId(BaseModel):
    reference_id: str


@oauth2_api_router.get("/create-reference-id")
async def create_reference_id() -> CreatedReferenceId:
    from sema4ai.action_server._user_session import create_user_session

    response = CreatedReferenceId(reference_id=create_user_session(external=True).id)
    return response


@oauth2_api_router.get("/redirect")
async def oauth2_redirect(request: Request, state: str = "") -> HTMLResponse:
    from requests_oauthlib import OAuth2Session  # type: ignore

    from sema4ai.action_server._database import Database
    from sema4ai.action_server._models import OAuth2UserData, get_db
    from sema4ai.action_server._settings import get_settings
    from sema4ai.action_server._user_session import datetime_to_iso, session_scope

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

        settings = _get_oauthlib_settings(provider)

        client_id = settings.clientId
        client_secret = settings.clientSecret

        token_url = settings.tokenEndpoint

        headers = settings.additionalHeaders or {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        app_settings = get_settings()
        base_url = app_settings.base_url
        assert base_url, "Internal error: `base_url` not available from app settings."
        redirect_uri = f"{base_url}/oauth2/redirect/"

        oauth2_session = OAuth2Session(
            client_id=client_id, state=state, redirect_uri=redirect_uri
        )
        token = oauth2_session.fetch_token(
            token_url,
            client_secret=client_secret,
            authorization_response=str(request.url),
            headers=headers,
            include_client_id=True,
        )

        access_token = token.get("access_token", "")
        scopes = token.scopes
        refresh_token = token.get("refresh_token", "")
        expires_at = token.get("expires_at", "")
        if expires_at:
            expires_at = datetime_to_iso(expires_at)

        token_type = token.get("token_type")

        use_id = reference_id
        if not use_id:
            use_id = session.session_id
        data = OAuth2UserData(
            user_session_id=use_id,
            provider=provider,
            refresh_token=refresh_token,
            access_token=access_token,
            expires_at=expires_at,
            token_type=token_type,
            scopes=json.dumps(scopes),
        )

        db: Database = get_db()
        with db.connect(), db.transaction():
            db.insert_or_update(data, ["user_session_id", "provider"])

        if callback_url:
            result = requests.post(
                callback_url,
                headers=headers,
                json={
                    "provider": provider,
                    "access_token": access_token,
                    "expires_at": expires_at,
                    "token_type": token_type,
                    "scopes": scopes,
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


def _get_oauthlib_settings(
    provider: str, oauth2_settings_file: Optional[str] = None
) -> OAuth2ProviderSettings:
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

    return OAuth2ProviderSettings.model_validate(as_dict)


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
