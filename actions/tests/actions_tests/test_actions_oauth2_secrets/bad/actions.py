from sema4ai.actions import OAuth2Secret, action


@action
def action_check_oauth2(
    message: str,
    google_secret: OAuth2Secret,  # Bad: cannot be unparameterized
) -> str:
    import json
    from pathlib import Path

    assert message == "some-message"
    ret = json.dumps(
        {
            "access_token": google_secret.access_token,
            "scopes": google_secret.scopes,
            "provider": google_secret.provider,
            "metadata": google_secret.metadata,
        }
    )

    Path("json.output").write_text(ret)

    return ret
