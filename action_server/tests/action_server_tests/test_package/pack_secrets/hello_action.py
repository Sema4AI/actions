from typing import Annotated

from sema4ai.actions import Secret, SecretSpec, action

AnnotatedSecret = Annotated[Secret, SecretSpec(tag="special-secret")]


@action(display_name="Display hello greeting")
def hello_greeting(
    name: str, private_info: Secret, annotated_secret: AnnotatedSecret
) -> str:
    """
    Provides a greeting for a person.

    Args:
        name: The name of the person to greet.

    Returns:
        The greeting for the person.
    """
    return f"Hello {name}. Private info: {private_info.value}. Annotated secret: {annotated_secret.value}"
