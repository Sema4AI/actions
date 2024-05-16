from typing import Literal

from sema4ai.actions import OAuth2Secret, action


@action(display_name="Display hello greeting")
def hello_greeting(
    name: str,
    oauth2_secret: OAuth2Secret[
        Literal["google"], list[Literal["https://scope:read", "https://scope:write"]]
    ],
) -> str:
    """
    Provides a greeting for a person.

    Args:
        name: The name of the person to greet.
        oauth2_secret: Oauth2 information

    Returns:
        The greeting for the person.
    """
    return f"Hello {name}. Access token: {oauth2_secret.access_token}"
