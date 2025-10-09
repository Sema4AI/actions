from typing import Annotated

from sema4ai.actions import Secret, SecretSpec, action

AnnotatedSecret = Annotated[Secret, SecretSpec(tag="special-secret")]
DocumentIntelligenceSecret = Annotated[Secret, SecretSpec(tag="document-intelligence")]


@action(display_name="Display hello greeting")
def hello_greeting(
    name: str,
    private_info: Secret,
    annotated_secret: AnnotatedSecret,
    doc_int_know_secret: DocumentIntelligenceSecret,
) -> str:
    """
    Provides a greeting for a person.

    Args:
        name: The name of the person to greet.
        private_info: Some private information gotten from somewhere.
        annotated_secret: Some private information gotten from somewhere with a special tag.

    Note:
        DocumentIntelligenceSecret type alias doesn't require docstrings as it is a know secret.

    Returns:
        The greeting for the person.
    """
    return f"Hello {name}. Private info: {private_info.value}. Annotated secret: {annotated_secret.value}"
