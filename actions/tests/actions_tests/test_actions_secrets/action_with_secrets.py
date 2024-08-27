from pathlib import Path

from sema4ai.actions import Request, Secret, action


@action
def action_with_secret(my_password: Secret) -> str:
    """
    This is an action that requires a secret.
    """
    Path("json.output").write_text(my_password.value)
    return my_password.value


@action
def action_with_secret_and_request(
    my_password: Secret,
    request: Request,
    value: int = 0,
) -> str:
    """
    This is an action that requires a secret.

    Args:
        value: Some value.
    """
    Path("json.output").write_text(my_password.value)
    return my_password.value


@action
def action_with_default_secret(
    my_password: Secret = Secret.model_validate("my-default-secret"),
) -> str:
    """
    This is an action that requires a secret but has a default value for it.
    """
    Path("json.output").write_text(my_password.value)
    return my_password.value
