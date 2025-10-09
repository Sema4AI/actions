from pathlib import Path
from typing import Annotated

from sema4ai.actions import Request, Secret, SecretSpec, action

# Type alias for a Secret with a custom tag
DocumentIntelligenceSecret = Annotated[Secret, SecretSpec(tag="document-intelligence")]


@action
def action_with_secret(my_password: Secret) -> str:
    """
    This is an action that requires a secret.
    """
    Path("json.output").write_text(my_password.value)
    return my_password.value


@action
def action_with_secret_annotated(
    config_secret: Annotated[Secret, SecretSpec(tag="special-secret")],
) -> str:
    """
    This is an action that requires a secret with a special tag.
    """
    Path("json.output").write_text(config_secret.value)
    return config_secret.value


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
def action_with_secret_type_alias(
    docint_secret: DocumentIntelligenceSecret,
) -> str:
    """
    This is an action that uses a Secret type alias.
    """
    Path("json.output").write_text(docint_secret.value)
    return docint_secret.value
