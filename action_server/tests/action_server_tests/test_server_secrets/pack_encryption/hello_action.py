from sema4ai.actions import Secret, action


@action
def get_private(private_info: Secret) -> str:
    """
    Returns the value passed to the private key.

    Args:
        private_info: Some private info.

    Returns:
        The value of the private key.
    """
    return private_info.value
