import json
import os
from pathlib import Path
from unittest import mock

import pytest
from action_server_tests.fixtures import get_in_resources

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


def _verify_oauth2_settings() -> Path:
    import yaml

    from sema4ai.action_server._settings import get_user_sema4_path

    user = get_user_sema4_path()
    yaml_location = user / "oauth2_config.yaml"
    assert (
        yaml_location.exists()
    ), f"Expected {yaml_location} to exist with the OAuth2 settings."

    txt = yaml_location.read_text()
    contents = yaml.safe_load(txt)
    assert (
        "oauth2Config" in contents
    ), f"Expected 'oauth2Config' to be defined in {yaml_location}"
    oauth2_config = contents.get("oauth2Config")

    assert (
        "providers" in oauth2_config
    ), f"Expected 'providers' to be defined in {yaml_location}"
    providers = oauth2_config.get("providers")

    assert (
        "google" in providers
    ), f"Expected 'providers/google' to be defined in {yaml_location}"
    google = providers["google"]
    for key in ["clientId", "clientSecret"]:
        assert (
            key in google
        ), f"Expected 'google/{key}' to be defined in {yaml_location}"
    return yaml_location


def manual_test_oauth2_vscode(
    action_server_process: ActionServerProcess, client: ActionServerClient, tmpdir
):
    """
    Note: this is a manual test that should open a browser to see if everything
    is correct.
    """
    import webbrowser

    from sema4ai.action_server._encryption import make_unencrypted_data_envelope
    from sema4ai.action_server._user_session import COOKIE_SESSION_ID, iso_to_datetime
    from sema4ai.action_server.vendored_deps.url_callback_server import (
        start_server_in_thread,
    )

    _verify_oauth2_settings()
    pack = get_in_resources("no_conda", "oauth2")

    action_server_process.start(
        actions_sync=True,
        cwd=pack,
        db_file="server.db",
        additional_args=[
            "--full-openapi-spec",
        ],
        port=8080,  # Needs to match redirect url
    )

    # For VSCode we create a reference so that we can refer to the OAuth2 status
    # later on (otherwise it'd be only accessible from the cookie stored in the
    # browser session which was used for the '/login' url access).
    result = client.get_json("/oauth2/create-reference-id")

    reference_id = result["reference_id"]

    fut_uri, fut_address = start_server_in_thread(port=0)

    callback_url = fut_address.result(10)
    assert callback_url

    # Needs to open the /oauth2/login in the browser as the cookie
    # related to the session id will be set at this point.
    webbrowser.open(
        client.build_full_url(
            "/oauth2/login?"
            "provider=google&"
            "scopes=openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile&"
            f"reference_id={reference_id}"
            f"&callback_url={callback_url}"
        ),
        new=1,
    )

    # At this point we have to manually make the login (5 minutes to do it).
    request_info = fut_uri.result(60 * 5)
    assert request_info["body"]
    loaded = json.loads(request_info["body"])
    assert loaded["provider"] == "google"
    assert "access_token" in loaded
    assert "expires_at" in loaded
    assert "scopes" in loaded

    provider_to_status = client.get_json(
        "/oauth2/status",
        params={
            "reference_id": reference_id,
            "provide_access_token": True,
            "refresh_tokens": True,
            "force_refresh": True,
        },
    )
    assert provider_to_status

    assert set(provider_to_status.keys()) == {"google"}
    info = provider_to_status["google"]

    assert set(info.keys()) == {"scopes", "access_token", "expires_at", "metadata"}
    assert iso_to_datetime(info["expires_at"])
    assert info["access_token"] != loaded["access_token"]

    # Ok, we're logged in. Call an action that requires it.
    found1 = client.post_get_str(
        "api/actions/oauth2/greet-user-oauth2/run",
        {},
        cookies={COOKIE_SESSION_ID: reference_id},
        headers={
            "x-action-context": make_unencrypted_data_envelope(
                {"secrets": {"regular_secret": "some-secret"}}
            )
        },
    )
    assert found1.startswith('"Hello: ')

    # Now, logout
    client.get_json(
        "/oauth2/logout",
        params={
            "provider": "google",
            "reference_id": reference_id,
        },
    )

    provider_to_status = client.get_json(
        "/oauth2/status",
        params={
            "reference_id": reference_id,
            "provide_access_token": True,
            "refresh_tokens": True,
            "force_refresh": True,
        },
    )
    assert not provider_to_status, "It should be empty as we've logged out already!"


def manual_test_oauth2_action_server_ui(
    action_server_process: ActionServerProcess, client: ActionServerClient
):
    """
    Note: this is a manual test that should open a browser to see if everything
    is correct.
    """
    import webbrowser

    from sema4ai.action_server.vendored_deps.url_callback_server import (
        start_server_in_thread,
    )

    settings_file = _verify_oauth2_settings()

    pack = get_in_resources("no_conda", "greeter")

    action_server_process.start(
        actions_sync=True,
        cwd=pack,
        db_file="server.db",
        additional_args=[
            f"--oauth2-settings={str(settings_file)}",
            "--full-openapi-spec",
        ],
        port=61080,  # Needs to match redirect url
    )

    fut_uri, fut_address = start_server_in_thread(port=0)

    callback_url = fut_address.result(10)
    assert callback_url

    result = client.get_json("/oauth2/create-reference-id")

    reference_id = result["reference_id"]

    # webbrowser.open(
    #     client.build_full_url(
    #         "/oauth2/login?provider=google&"
    #         "scopes=openid&"
    #         f"callback_url={callback_url}&"
    #         f"reference_id={reference_id}&"
    #     ),
    #     new=1,
    # )

    webbrowser.open(
        client.build_full_url(
            "/oauth2/login?provider=microsoft&"
            "scopes=Calendars.Read&"
            f"callback_url={callback_url}&"
            f"reference_id={reference_id}&"
        ),
        new=1,
    )

    request_info = fut_uri.result(60 * 5)
    assert request_info["body"]
    loaded = json.loads(request_info["body"])
    assert loaded


def test_settings(tmpdir):
    import yaml

    from sema4ai.action_server.vendored_deps.oauth2_settings import (
        get_oauthlib2_provider_settings,
    )

    oauth2_settings_file = Path(tmpdir) / "oauth2_settings.yaml"

    with pytest.raises(RuntimeError):  # File does not exist
        get_oauthlib2_provider_settings("google", str(oauth2_settings_file))

    oauth2_settings_file.write_text(
        yaml.safe_dump(
            dict(
                oauth2Config=dict(
                    providers=dict(
                        google={
                            "mode": "custom",
                            "clientId": "foo",
                            "clientSecret": "bar",
                            "tokenEndpoint": "<end>",
                        },
                        custom={
                            "mode": "custom",
                            "clientId": "f",
                            "clientSecret": "b",
                            "tokenEndpoint": "/end",
                            "authorizationEndpoint": "/auth",
                            "server": "http://server/",
                        },
                    )
                )
            )
        )
    )
    google_settings = get_oauthlib2_provider_settings(
        "google", str(oauth2_settings_file)
    )
    assert google_settings.clientId == "foo"
    assert google_settings.clientSecret == "bar"

    # i.e.: there's a default but it should be overridden.
    assert google_settings.tokenEndpoint == "<end>"

    # i.e.: the default ones should be loaded too.
    assert google_settings.server == "https://oauth2.googleapis.com"

    custom_settings = get_oauthlib2_provider_settings(
        "custom", str(oauth2_settings_file)
    )
    assert custom_settings.clientId == "f"
    assert custom_settings.clientSecret == "b"

    assert custom_settings.tokenEndpoint == "http://server/end"


def test_oauth2_provider_settings():
    from sema4ai.action_server.vendored_deps.oauth2_settings import (
        OAuth2ProviderSettings,
    )

    settings = OAuth2ProviderSettings(clientId="foo")
    dumped = settings.model_dump()
    new_settings = OAuth2ProviderSettings.model_validate(dumped)
    assert new_settings.clientId == "foo"


@mock.patch("builtins.print")
def test_print_user_oauth2_config_path(print_mock: mock.MagicMock, tmpdir) -> None:
    from sema4ai.action_server._oauth2 import (
        USER_CONFIG_FILE_NAME,
        print_user_oauth2_config_path,
    )

    mock_settings_dir: Path = tmpdir / "action-server"
    mock_config_path: Path = mock_settings_dir / USER_CONFIG_FILE_NAME

    # Make sure all the directories in the mocked config path exist.
    os.makedirs(mock_settings_dir)

    with mock.patch(
        "sema4ai.action_server._settings.get_default_settings_dir"
    ) as mock_get_default_settings_dir:
        mock_get_default_settings_dir.return_value = mock_settings_dir

        assert mock_config_path.exists() is False

        retcode = print_user_oauth2_config_path(output_json=False)

        assert retcode == 0
        assert mock_config_path.exists() is True

        # Get latest print args
        print_args = print_mock.mock_calls[-1].args

        assert print_args[0] == mock_config_path

        retcode = print_user_oauth2_config_path(output_json=True)

        assert retcode == 0
        assert mock_config_path.exists() is True

        print_args = print_mock.mock_calls[-1].args

        json_data = json.loads(print_args[0])

        assert json_data["path"] == mock_config_path
