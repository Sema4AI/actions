from sema4ai.actions import action


@action
def doit(validate: bool = False) -> str:
    """
    This is an action.

    Args:
        validate: If True, will check that the environment is as expected.

    Returns:
        'Ok' string or 'Ok validated' if validate is True.
    """
    if validate:
        # Just import to check that it works
        import mylib  # type: ignore

        print(mylib.__file__)

        return "Ok validated"
    return "Ok"
