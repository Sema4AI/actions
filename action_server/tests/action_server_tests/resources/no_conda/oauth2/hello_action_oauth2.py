from typing import Literal

from sema4ai.actions import OAuth2Secret, Secret, action


@action()
def greet_user_oauth2(
    oauth2_secret: OAuth2Secret[
        Literal["google"],
        list[
            Literal[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ]
        ],
    ],
    regular_secret: Secret,
) -> str:
    """
    Provides a greeting for a person.

    Args:
        oauth2_secret: Oauth2 information
        regular_secret: Some secret

    Returns:
        The greeting for the person.
    """
    assert regular_secret.value
    import requests

    def get_user_info(access_token):
        url = "https://people.googleapis.com/v1/people/me?personFields=names"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            user_info = response.json()
            names = user_info.get("names", [])
            if names:
                return names[0].get("displayName")
            else:
                return None
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    access_token = oauth2_secret.access_token
    user_name = get_user_info(access_token)
    msg = f"Hello: {user_name}"
    print(msg)
    return msg
